"""Additional default-off retry test on rear-bag3executed+1stopped decisions.
Prior186-state report is a prerequisite; no repeated physical run.
Original successes must be bit-identical; only the otherwise rejected stop may
change. Stop orientation is recorded context, not an independently saved frame.
No command is executed, and failed/short episodes retain failed status.
"""
from pathlib import Path
import sys,ast,json,hashlib,datetime,copy
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_loaded_edge_coverage';probe=w/'staged_loaded_edge_scaled_retry_probe';sys.path[:0]=[str(probe),str(stage),str(w),str(repo)]
from loaded_edge_scaled_retry import propose
from clearance_runtime import ClearanceGuard
from audit_loaded_edge_coverage_record import verify
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();a=ast.parse((stage/'loaded_edge_coverage_current_contact.py').read_text());b=ast.parse((probe/'loaded_edge_scaled_retry.py').read_text())
class Disabled(ast.NodeTransformer):
 def visit_FunctionDef(self,node):
  if node.name=='propose':
   ix=next(i for i,x in enumerate(node.args.kwonlyargs) if x.arg=='scaled_retry');node.args.kwonlyargs.pop(ix);node.args.kw_defaults.pop(ix)
  return self.generic_visit(node)
 def visit_If(self,node):
  if any(isinstance(n,ast.Name) and n.id=='scaled_retry' for n in ast.walk(node.test)):return None
  return self.generic_visit(node)
assert ast.dump(a,include_attributes=False)==ast.dump(Disabled().visit(b),include_attributes=False)
guard=ClearanceGuard(repo,stage);urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);records=[];sources={};cached={};negative=[]
fixture=probe/'PROBE_CHECK.json';d=json.loads(fixture.read_text());assert d['passed'];sources[str(fixture)]=sha(fixture)
new_ep=w/'loaded_edge_coverage_groups_r1/case_840004/layout_840004_nudge_mailer_to_bin';traces=json.loads((new_ep/'loaded_edge_coverage.json').read_text())['rows'];states=[(new_ep,tr,'executed' if tr['accepted'] else 'unexecuted_stop') for tr in traces if tr['override'] or not tr['accepted']];assert len(states)==4
for ep,tr,origin in states:
 if ep not in cached:
  fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};pack={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
  key='box' if 'push_box' in ep.name else 'mailer'
  with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].copy()
  cached[ep]=(fr,fs,cs,pack,q,u,quat)
  for name in ['raw.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json','parcel_orientation.npz']:
   sources[str(ep/name)]=sha(ep/name)
 fr,fs,cs,pack,qs,us,quats=cached[ep];t=tr['step'];side='right' if 'push_box' in ep.name else 'left';inp=cs[t]['task_inputs'];q=np.array(inp['current'],dtype=np.float32);prev=us[t-1];parent=np.array(tr['parent_upper_command'],dtype=np.float32);ctx=tr['context'];R=np.array(ctx['object_rotation']);offset=np.array(fs[t]['control_offset_local'])
 def point(x):T,_,_=guard.model.fk(side,x);return T[:3,3]+T[:3,:3]@offset
 def jac(x):T,jl,jw=guard.model.fk(side,x);a,b,c=T[:3,:3]@offset;return jl-np.array([[0,-c,b],[c,0,-a],[-b,a,0]])@jw
 args={k:ctx[k] for k in ['enabled','selected','mode','previous_mode','recontacts','previous_recontacts','load_n','previous_load_n','parent_guard','terminal_hold','region_override','unloaded_override']}
 args.update(current=q,previous_command=prev,parent_command=parent,jacobian=inp['jacobian'],error=inp['error'],damping=inp['damping'],lower=inp['lower'],upper=inp['upper'],step_limits=inp['step_limits'],object_rotation=R,cop_local=ctx['current_cop_local'],core_size=ctx['core_size'],direction=-1 if side=='right' else 1,point_fn=point,point_jacobian_fn=jac,geometry=guard.geometry)
 off=propose(**args)
 for k,v in off.items():assert v==tr[k],(origin,ep.name,t,k,'disabled differs from actual original record')
 on=propose(**args,scaled_retry=True)
 if tr['accepted']:assert on==off,(origin,t,'original success changed')
 else:assert origin=='unexecuted_stop' and on['accepted'] and on['override']
 full=dict(tr,**on);full['final_upper_command']=on['command'];quat=quats[t].astype(float) if t<len(quats) else Rotation.from_matrix(R).as_quat()
 checked=verify(full,row=fs[t],previous_row=fs[t-1],coordinate=cs[t],current=q,previous_command=prev,parent_command=parent,final_command=on['command'],packet=pack[t-1],object_xyz=ctx['object_xyz'],object_quat=quat,core_size=ctx['core_size'],side=side,selected=True,hand=hand,elbows=elbows);assert checked['passed'],(origin,t,checked)
 retry=[x for x in on['attempts'] if 'retry' in x];assert len(retry)<=3
 for a in retry:assert a['retry']['primary_status']==8 and a['retry']['objective_scale_from']==5000 and a['retry']['objective_scale_to']==100 and a['retry']['maximum_retries_per_primary']==1
 records.append(dict(episode=ep.name,origin=origin,step=t,default_off_exact=True,original_success_preserved=tr['accepted'],retries=len(retry),selected_seed=on['selected_seed'],independent=checked))
 if origin=='unexecuted_stop':
  for label,change in [('disabled',{'enabled':False}),('guard',{'parent_guard':True}),('first_push',{'previous_mode':'top_press'}),('no_load',{'load_n':0.}),('terminal',{'terminal_hold':True})]:
   z=propose(**dict(args,**change),scaled_retry=True);assert not z['eligible'] and not z['override'] and 'attempts' not in z;negative.append(label)
  class Impossible:
   def constraints(self,x):return np.array([-1.,-1.])
   def jacobian(self,x):return np.zeros((2,11))
  z=propose(**dict(args,geometry=Impossible()),scaled_retry=True);assert z['accepted'] is False and z['command'] is None;negative.append('infeasible_remains_rejected')
 if len(records)%25==0:print('checked',len(records),flush=True)
assert len(negative)==6 and sum(r['original_success_preserved'] for r in records)==3
for p in [Path(__file__),fixture,new_ep/'loaded_edge_coverage.json',probe/'loaded_edge_scaled_retry.py',stage/'loaded_edge_coverage_current_contact.py',stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json',w/'audit_loaded_edge_coverage_record.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',urdf,vertices]:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,default_off_ast_exact=True,states=4,unchanged_successes=3,recovered_unexecuted_stops=1,negative_checks=negative,records=records,source_sha256=sources,collector_connected=False,physical_validation=False,training_ready=False)
(probe/'REAR_BAG_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',4,3,1,flush=True)
