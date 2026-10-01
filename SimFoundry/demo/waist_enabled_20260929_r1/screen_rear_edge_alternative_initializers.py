"""Offline bounded-initializer screen on ALL closed5N rear solver failures.
Original primary+analytic retry are reproduced first. Three alternative starting
points use the same objective, original limits, .055 slew, nonlinear FK direction,
float32 and independent1e-6 KKT checks. No collector connection or new physics.
"""
from pathlib import Path
import json,sys,hashlib,datetime
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
  attempts=[];seen=[]
  for name,initial in [('clipped_parent',parent.astype(float)-q),('clipped_previous',prev-q),('clipped_current',np.zeros(11))]:
   initial=np.clip(initial,low,high)
   if any(np.array_equal(initial,x) for x in seen):continue
   seen.append(initial.copy());sol=minimize(fun,initial,jac=grad,bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=constraints,jac=jac)],method='SLSQP',options={'ftol':1e-11,'maxiter':300});a=dict(initializer=name,success=bool(sol.success),solver_status=int(sol.status),iterations=int(sol.nit),independent_passed=False)
   if sol.success and np.isfinite(sol.x).all():
    cmd=(q+sol.x).astype(np.float32);dq=cmd.astype(float)-q;v=constraints(dq);pv=constraints(parent.astype(float)-q)
    trace=dict(override=True,reason='nonlinear_joint_direction',command=cmd.tolist(),nominal_edge_inward_m=v[:-1].tolist(),nominal_forward_m=float(v[-1]),iterations=int(sol.nit),threatened_axes=axes,parent_nominal_edge_inward_m=pv[:-1].tolist(),parent_nominal_forward_m=float(pv[-1]),parent_final_upper_command=parent.tolist(),final_upper_command=cmd.tolist(),previous_upper_command=prev.tolist())
    try:
     check=verify_refinement(trace,parent,cmd,prev,q,J,e,damp,lo,hi,limits,independent_point_jac,R,cop,core,direction,captured['active_rows']);gap=elbows.gap(cmd);assert min(gap)>=.005-2e-7,('self_clearance',gap)
    except (AssertionError,ValueError) as exc:a['independent_rejection']=str(exc)
    else:a.update(independent_passed=True,check=check,self_clearance_gap_m=list(map(float,gap)),command=cmd.tolist(),objective=float(np.linalg.norm(J@dq-e)**2+np.linalg.norm(damp*dq)**2))
   attempts.append(a)
  good=[a for a in attempts if a['independent_passed']];best=min(good,key=lambda a:a['objective']) if good else None
  reports.append(dict(episode=ep.name,step=t,original_failure_reproduced=True,original_solver_status=base['solver_status'],attempts=attempts,counterfactual_recovered=best is not None,selected_initializer=best['initializer'] if best else None));print(ep.name,t,'recovered',best['initializer'] if best else None,[(a['initializer'],a['solver_status'],a['independent_passed']) for a in attempts],flush=True)
assert len(reports)==expected==26
for p in [Path(__file__),stage/'joint_edge_adapter.py',stage/'joint_edge_command.py',stage/'articulated_hand_geometry.py',stage/'elbow_torso_hulls.json',w/'audit_joint_edge_execution_live.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',urdf,vertices]:sources[str(p)]=sha(p)
out=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),failed_states=expected,counterfactual_recovered=sum(r['counterfactual_recovered'] for r in reports),records=reports,source_sha256=sources,collector_connected=False,physical_validation=False,training_ready=False);(w/'REAR_EDGE_ALTERNATIVE_INITIALIZERS_SCREEN.json').write_text(json.dumps(out,indent=2));print('RESULT',expected,out['counterfactual_recovered'],flush=True)
