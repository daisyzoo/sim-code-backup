"""Whole closed5N eight-push adapter replay; every original row stays in scope.
Default-off output/trace must exactly reproduce recorded actions. Enabled mode
may change only the26 original failures; recovered candidates independently obey
original FK direction, bounds, slew,1e-6KKT and5mm self-clearance. Not a rollout.
"""
from pathlib import Path
import sys,json,ast,hashlib,datetime,collections
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_interior';probe=w/'staged_rear_edge_parent_seed_probe';sys.path[:0]=[str(probe),str(stage),str(repo),str(w)]
from joint_edge_adapter import refine_record
from audit_parent_seed_retry_metadata import verify_parent_seed_retry_metadata
from audit_joint_edge_retry_execution_live import verify_retry_metadata
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.data.top_contact_bypass import rotation_xyzw
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from audit_joint_edge_execution_live import verify_refinement
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class RemoveOptional(ast.NodeTransformer):
 def visit_FunctionDef(self,node):
  if node.name=='refine_record':
   ix=next(i for i,x in enumerate(node.args.kwonlyargs) if x.arg=='parent_seed_retry');node.args.kwonlyargs.pop(ix);node.args.kw_defaults.pop(ix)
  return self.generic_visit(node)
 def visit_If(self,node):
  if any(isinstance(x,ast.Name) and x.id=='parent_seed_retry' for x in ast.walk(node.test)):return None
  return self.generic_visit(node)
assert ast.dump(ast.parse((stage/'joint_edge_adapter.py').read_text()),include_attributes=False)==ast.dump(RemoveOptional().visit(ast.parse((probe/'joint_edge_adapter.py').read_text())),include_attributes=False)
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';model=ArticulatedHandGeometry(urdf,vertices);hand=HandModel(urdf,vertices);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);run=w/'recontact_interior_groups_r1';records=[];sources={};total=changed=0
protocol=json.loads((run/'PROTOCOL.json').read_text())
for entry in protocol['commands']:
 if entry['wait']:continue
 for task in entry['tasks']:
  ep=run/f"case_{entry['layout_id']}"/f"layout_{entry['layout_id']}_{task}";print('start',ep.name,flush=True)
  prov=json.loads((ep.parent/'provenance.json').read_text())
  for name in ['joint_edge_command.py','joint_edge_adapter.py','articulated_hand_geometry.py']:
   rel=next(x for x in prov['source_sha256'] if x.endswith('/'+name));assert sha(stage/name)==prov['source_sha256'][rel]==sha(ep.parent/'source_snapshot'/rel)
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
  key='box' if 'push_box' in task else 'mailer';side='right' if key=='box' else 'left'
  with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
  with np.load(ep/'parcel_orientation.npz') as z:quats=z[key].copy()
  fr=json.loads((ep/'frontal_bypass.json').read_text());cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};selected=bool(fr['plan'].get('rear_joint_edge_command',{}).get('enabled'));core=np.array(fr['plan'].get('region_causal_response',{}).get('actual_core',{}).get('collision_core_size_xyz',[.1,.1,.1]));counts=collections.Counter();details=[]
  assert np.max(abs(q[0]))==np.max(abs(u[0]))==0 and len(fr['rows'])==1199
  for f in fr['rows']:
   t=f['step'];c=cs[t];old=c.get('joint_edge_refinement');parent=np.array(old['parent_final_upper_command'],dtype=np.float32) if selected else u[t].copy();R=np.array(rotation_xyzw(quats[t].tolist()));kwargs=dict(enabled=selected,row=f,coordinate=c,current=q[t],previous=u[t-1],parent_command=parent,object_xyz=xyz[t],object_rotation=R,core_size=core,model=model,side=side,analytic_retry=True)
   off,ot=refine_record(**kwargs);assert np.array_equal(off,u[t]),(ep.name,t,'default action mismatch')
   if selected:assert ot==old,(ep.name,t,'default trace mismatch')
   else:assert ot is None
   on,tr=refine_record(**kwargs,parent_seed_retry=True);total+=1;counts['frames']+=1
   eligible=bool(old.get('input_selected',False)) if old else False
   verify_parent_seed_retry_metadata(ot,enabled=False,analytic_enabled=True,eligible=eligible,mode=f['mode'],original_verifier=verify_retry_metadata)
   verify_parent_seed_retry_metadata(tr,enabled=True,analytic_enabled=True,eligible=eligible,mode=f['mode'],original_verifier=verify_retry_metadata)
   if not selected or old['reason']!='nonlinear_solver_failed':
    assert np.array_equal(on,off) and tr==ot,(ep.name,t,'original outcome changed');counts['unchanged']+=1;continue
   assert tr['override'] and 'parent_seed_retry' in tr and tr['analytic_retry']==old['analytic_retry'];assert not np.array_equal(on,off)
   J=np.vstack([np.array(c['control_jacobian_world'],dtype=np.float32),np.array(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]).astype(float);errors=[]
   for name in ['left','right']:
    target=f['target_xyz'] if name==side else c['inactive_anchor'];errors.extend(np.clip(np.float32(.72)*(np.array(target,dtype=np.float32)-np.array(c['control_point_positions'][name],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
   error=np.r_[np.array(errors,dtype=np.float32),np.array(c['contact_normal_tracking']['error'],dtype=np.float32)].astype(float);lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;damp=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10));local=R.T@(np.array(f['rear_cop_centering']['cop_world'])-xyz[t]);offset=np.array(f['control_offset_local'])
   def point(x):M=hand.fk(x,side);return M[:3,3]+M[:3,:3]@offset
   def point_jac(x):
    x=np.array(x,float);eps=1e-6;G=np.column_stack([(point(x+np.eye(11)[i]*eps)-point(x-np.eye(11)[i]*eps))/(2*eps) for i in range(11)]);return point(x),G
   check=verify_refinement(tr,parent,on,u[t-1],q[t].astype(float),J,error,damp,lo,hi,limits,point_jac,R,local,core,-1 if side=='right' else 1,[3,4,5] if side=='right' else [0,1,2]);gap=elbows.gap(on);assert min(gap)>=.005-2e-7
   changed+=1;counts['recovered_failure']+=1;details.append(dict(step=t,independent=check,retry=tr['parent_seed_retry'],self_clearance_gap_m=list(map(float,gap))))
  records.append(dict(episode=ep.name,selected=selected,counts=dict(counts),changed_rows=details))
  for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json']:sources[str(ep/name)]=sha(ep/name)
  print('done',ep.name,dict(counts),flush=True)
assert total==8*1199 and changed==26 and len(records)==8
for p in [Path(__file__),w/'audit_parent_seed_retry_metadata.py',w/'audit_joint_edge_retry_execution_live.py',probe/'joint_edge_command.py',probe/'joint_edge_adapter.py',stage/'joint_edge_command.py',stage/'joint_edge_adapter.py',stage/'articulated_hand_geometry.py',stage/'elbow_torso_hulls.json',w/'audit_joint_edge_execution_live.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',urdf,vertices,run/'RESULT.json',run/'PROTOCOL.json']:sources[str(p)]=sha(p)
out=dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),adapter_default_off_ast_exact=True,episodes=records,frames=total,changed_only_original_failures=changed,unchanged_frames=total-changed,source_sha256=sources,collector_connected=False,physical_validation=False,training_ready=False);(probe/'METADATA_HISTORY_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',total,changed,flush=True)
