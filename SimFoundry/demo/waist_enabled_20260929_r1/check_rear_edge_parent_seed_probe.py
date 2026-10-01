"""Actual parent-seed helper verification on ALL closed5N rear solver failures.
Original primary+analytic retry are reproduced first. Three alternative starting
points use the same objective, original limits, .055 slew, nonlinear FK direction,
float32 and independent1e-6 KKT checks. No collector connection or new physics.
"""
from pathlib import Path
import json,sys,hashlib,datetime,ast,importlib.util
import numpy as np
from scipy.optimize import minimize,Bounds
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_interior';sys.path[:0]=[str(stage),str(repo),str(w)]
import joint_edge_adapter as adapter
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.data.top_contact_bypass import rotation_xyzw
from audit_joint_edge_execution_live import verify_refinement
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';model=ArticulatedHandGeometry(urdf,vertices);independent=HandModel(urdf,vertices);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);original_refine=adapter.refine_rear_command;reports=[];sources={};expected=0

probe=w/'staged_rear_edge_parent_seed_probe';spec=importlib.util.spec_from_file_location('parent_seed_candidate',probe/'joint_edge_command.py');candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
class RemoveOptional(ast.NodeTransformer):
 def visit_FunctionDef(self,node):
  if node.name=='refine_rear_command':
   index=next(i for i,x in enumerate(node.args.kwonlyargs) if x.arg=='parent_seed_retry');node.args.kwonlyargs.pop(index);node.args.kw_defaults.pop(index)
  return self.generic_visit(node)
 def visit_If(self,node):
  if any(isinstance(x,ast.Name) and x.id=='parent_seed_retry' for x in ast.walk(node.test)):return None
  return self.generic_visit(node)
assert ast.dump(ast.parse((stage/'joint_edge_command.py').read_text()),include_attributes=False)==ast.dump(RemoveOptional().visit(ast.parse((probe/'joint_edge_command.py').read_text())),include_attributes=False)

for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 ep=w/'recontact_interior_groups_r1'/f'case_{cid}/layout_{cid}_{task}';side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer'
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].copy();us=z['action'][:,12:23].copy()
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
 with np.load(ep/'parcel_orientation.npz') as z:rotation=np.array([rotation_xyzw(x.tolist()) for x in z[key]])
 fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
 for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json']:sources[str(ep/n)]=sha(ep/n)
 failed=[(t,c) for t,c in cs.items() if c.get('joint_edge_refinement',{}).get('reason')=='nonlinear_solver_failed'];expected+=len(failed)
 for t,c in failed:
  f=fs[t];old=c['joint_edge_refinement'];parent=np.array(old['parent_final_upper_command'],dtype=np.float32);captured={}
  def capture(**kw):captured.update(kw);return {'override':False,'reason':'offline_input_capture'}
  adapter.refine_rear_command=capture
  try:adapter.refine_record(enabled=True,row=f,coordinate=c,current=qs[t],previous=us[t-1],parent_command=parent,object_xyz=xyz[t],object_rotation=rotation[t],core_size=core,model=model,side=side,analytic_retry=True)
  finally:adapter.refine_rear_command=original_refine
  base=original_refine(**captured);assert not base['override'] and base['reason']==old['reason'],(ep.name,t,base)
  q=np.array(captured['current'],float);prev=np.array(captured['previous'],float);J=np.array(captured['jacobian'],float);e=np.array(captured['error'],float);damp=np.array(captured['damping'],float);lo=np.array(captured['lower']);hi=np.array(captured['upper']);limits=np.array(captured['step_limits']);R=rotation[t];cop=np.array(captured['cop_local']);direction=captured['direction'];axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.01];normals=np.array([-np.sign(cop[k])*R[:,k] for k in axes]);point=captured['point_fn'];pj=captured['point_jacobian_fn'];origin=point(q);offset=np.array(f['control_offset_local'])
  low=np.maximum.reduce([lo-q,-limits,prev-.055-q]);high=np.minimum.reduce([hi-q,limits,prev+.055-q]);assert (low<high).all()
  design=np.vstack([J,np.diag(damp)]);rhs=np.r_[e,np.zeros(11)];H=design.T@design;g=design.T@rhs
  fun=lambda x:5000*float(x@H@x-2*g@x)
  grad=lambda x:10000*(H@x-g)
  def constraints(x):
   v=point(q+x)-origin;return np.r_[normals@v,direction*v[1]]
  def jac(x):
   jp=pj(q+x);return np.vstack([normals@jp,direction*jp[1]])
  def ipoint(x):
   M=independent.fk(x,side);return M[:3,3]+M[:3,:3]@offset
  def independent_point_jac(x):
   x=np.array(x,float);step=1e-6;j=np.column_stack([(ipoint(x+np.eye(11)[k]*step)-ipoint(x-np.eye(11)[k]*step))/(2*step) for k in range(11)]);return ipoint(x),j
  assert np.max(abs(ipoint(q)-origin))<1e-10
  off=candidate.refine_rear_command(**captured);assert off==base,(ep.name,t,'disabled differs')
  on=candidate.refine_rear_command(**captured,parent_seed_retry=True);assert on['override'],(ep.name,t,on)
  assert on['analytic_retry']==base['analytic_retry'] and on['analytic_retry']['retry_solver_status']==8
  retry=on['parent_seed_retry'];assert retry['maximum_extra_retries']==1 and retry['initializer']=='bounded_parent_delta' and retry['prior_solver_status']==8 and retry['retry_solver_status']==0
  cmd=np.array(on['command'],dtype=np.float32);full=dict(on,parent_final_upper_command=parent.tolist(),final_upper_command=cmd.tolist(),previous_upper_command=prev.tolist())
  check=verify_refinement(full,parent,cmd,prev,q,J,e,damp,lo,hi,limits,independent_point_jac,R,cop,core,direction,captured['active_rows']);gap=elbows.gap(cmd);assert min(gap)>=.005-2e-7
  reports.append(dict(episode=ep.name,step=t,default_off_exact=True,original_failure_reproduced=True,counterfactual_recovered=True,original_analytic_failure_preserved=True,retry=retry,independent=check,self_clearance_gap_m=list(map(float,gap))))
  print(ep.name,t,'PASS',check['stationarity_residual'],flush=True)
assert len(reports)==expected==26
# Original protected branches must never invoke any extra optimizer.
real_minimize=candidate.minimize
candidate.minimize=lambda *a,**k:(_ for _ in ()).throw(AssertionError('unexpected optimizer'))
protected=[]
try:
 for label,changes in [('disabled',{'enabled':False}),('not_selected',{'selected':False}),('non_push',{'mode':'top_lift'}),('parent_already_valid',{'parent_command':cmd})]:
  off=original_refine(**dict(captured,**changes));on=candidate.refine_rear_command(**dict(captured,**changes),parent_seed_retry=True);assert off==on and 'parent_seed_retry' not in on;protected.append(label)
finally:candidate.minimize=real_minimize
# Explicit bounded failure chains: unchanged fallback, no fourth optimization.
from types import SimpleNamespace
failure_checks=[]
for label,statuses,nonfinite in [('primary_status9',[9],False),('three_status8',[8,8,8],False),('retry_status9',[8,9],False),('extra_status9',[8,8,9],False),('extra_nonfinite',[8,8,0],True)]:
 calls=[]
 def fake(fun,initial,**kwargs):
  idx=len(calls);assert idx<len(statuses);calls.append(initial.copy());status=statuses[idx];x=np.full(11,np.nan) if nonfinite and idx==len(statuses)-1 else initial.copy();return SimpleNamespace(status=status,success=status==0,nit=1,x=x)
 candidate.minimize=fake
 try:out=candidate.refine_rear_command(**captured,parent_seed_retry=True)
 finally:candidate.minimize=real_minimize
 assert len(calls)==len(statuses) and not out['override'] and 'command' not in out
 failure_checks.append(dict(name=label,calls=len(calls),reason=out['reason']))
for changes in [{'parent_seed_retry':1},{'parent_seed_retry':True,'analytic_retry':False}]:
 try:candidate.refine_rear_command(**dict(captured,**changes))
 except ValueError:pass
 else:raise AssertionError('invalid flag accepted')
for p in [Path(__file__),probe/'joint_edge_command.py',stage/'joint_edge_adapter.py',stage/'joint_edge_command.py',stage/'articulated_hand_geometry.py',stage/'elbow_torso_hulls.json',w/'audit_joint_edge_execution_live.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',urdf,vertices]:sources[str(p)]=sha(p)
out=dict(passed=True,scope='Actual default-off helper test on all26 recorded5N failures; same objective/bounds/nonlinear FK/float32 and independent1e-6KKT plus5mm self-clearance. Not recursive physical behavior or whole episode eligibility.',created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),default_off_ast_exact=True,states=26,recovered=26,records=reports,protected_branches=protected,failure_checks=failure_checks,invalid_flags_rejected=2,source_sha256=sources,collector_connected=False,physical_validation=False,training_ready=False)
(probe/'PROBE_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS26 + protected/failure branches',flush=True)
