"""Locate original left refinement failure with independent archived-URDF FK.
No threshold changes, no dynamics, no replacement for the failed whole audit.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import nnls
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'rear_early_bag_stationarity_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
from audit_box_inward_refinement import verify_refinement
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'rear_early_edge_physical_r1/case_840020/layout_840020_nudge_mailer_to_bin';prov=read(ep.parent/'provenance.json');sources={}
def archived(name):
 keys=[k for k in prov['source_sha256'] if Path(k).name==name];assert len(keys)==1
 p=ep.parent/'source_snapshot'/keys[0];assert sha(p)==prov['source_sha256'][keys[0]];sources[str(p)]=sha(p);return p
hand=HandModel(archived('g1_23dof_rev_1_0_u1_black.urdf'),archived('g1_hand_support_vertices.json'))
for name in ['joint_edge_command.py','joint_edge_adapter.py','collect_paired_sorting.py']:archived(name)
with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);us=z['action'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:xyz=z['mailer'].copy()
with np.load(ep/'parcel_orientation.npz') as z:quat=z['mailer'].copy()
coords=read(ep/'coordination.json');fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};results=[]
for c in coords:
 old=c.get('joint_edge_refinement')
 if not old or not old['override']:continue
 t=c['step'];row=fr[t];trace=c['joint_edge_clearance_intersection'];assert c['active_side']=='left';q=qs[t];prev=us[t-1];x=np.asarray(old['final_upper_command']);a=c['task_inputs'];J=np.asarray(a['jacobian']);e=np.asarray(a['error']);damp=np.asarray(a['damping']);lo=np.asarray(a['lower']);hi=np.asarray(a['upper']);lim=np.asarray(a['step_limits']);R=Rotation.from_quat(quat[t]).as_matrix();core=np.asarray(trace['core_size']);local=R.T@(np.asarray(row['rear_cop_centering']['cop_world'])-xyz[t]);offset=np.asarray(row['control_offset_local']);parent=np.asarray(old['parent_final_upper_command'])
 assert np.array_equal(a['current'],q) and np.array_equal(a['previous'],prev) and np.all(np.asarray(a['preferred_step'])==0)
 assert np.max(abs(R-np.asarray(trace['object_rotation'])))<1e-12 and np.array_equal(trace['object_xyz'],xyz[t])
 axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01];assert axes==old['threatened_axes'];normals=np.asarray([-np.sign(local[k])*R[:,k] for k in axes])
 def point(v):
  T=hand.fk(v,'left');return T[:3,3]+T[:3,:3]@offset
 def pj(v,h=2e-7):
  G=np.stack([(point(v+np.eye(11)[j]*h)-point(v-np.eye(11)[j]*h))/(2*h) for j in range(11)],axis=1);return point(v),G
 try:
  cert=verify_refinement(old,parent,x,prev,q,J,e,damp,lo,hi,lim,pj,R,local,core,1,[0,1,2],inward_enabled=False);error=None
 except AssertionError as exc:cert=None;error=str(exc)
 low=np.maximum.reduce([lo-q,-lim,prev-.055-q]);high=np.minimum.reduce([hi-q,lim,prev+.055-q]);dq=x-q;motion=point(x)-point(q);values=np.r_[normals@motion,motion[1]];grad=J.T@(J@dq-e)+damp*damp*dq
 def residual(h):
  _,G=pj(x,h);jac=np.vstack([normals@G,G[1]]);active=[jac[i] for i,v in enumerate(values) if v<=1e-6]
  for j in range(11):
   if dq[j]-low[j]<=2e-6:active.append(np.eye(11)[j])
   if high[j]-dq[j]<=2e-6:active.append(-np.eye(11)[j])
  if active:
   A=np.asarray(active);norm=np.linalg.norm(A,axis=1);A=A[norm>1e-12]/norm[norm>1e-12,None];_,res=nnls(A.T,grad,maxiter=1000)
  else:res=np.linalg.norm(grad)
  return float(res)
 rr=residual(2e-7)
 r=dict(step=t,passed=cert is not None,error=error,stationarity=rr,threshold=1e-6,primal_min_direction_m=float(min(values)),min_bound_margin_rad=float(min(np.min(dq-low),np.min(high-dq))),solver_iterations=old['iterations'],finite_difference_residuals={str(h):residual(h) for h in [1e-6,5e-7,1e-7,5e-8]} if error else {},intersection_changed=trace['changed'],final_transport_applied=c['joint_transport_clearance']['applied'])
 results.append(r)
 if error:
  (D/f'CONTEXT_{t}.json').write_text(json.dumps(dict(coordinate=c,frontal_row=row,current=q.tolist(),previous=prev.tolist(),object_xyz=xyz[t].tolist(),object_rotation=R.tolist(),core_size=core.tolist(),scope=__doc__,training_ready=False),indent=2));print(json.dumps(r),flush=True)
for p in [Path(__file__),W/'audit_joint_edge_clearance_record.py',W/'audit_box_inward_refinement.py',W/'audit_box_entry_pose_loaded_execution.py',W/'audit_unloaded_wrist_prior_live.py',ep/'raw.npz',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'coordination.json',ep/'frontal_bypass.json',ep/'audit_rear_early_edge_r1_v3_stage_self_clearance.py.log']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checked=len(results),failures=[r for r in results if not r['passed']],rows=results,source_sha256=sources,original_failure_preserved=True,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(checked=len(results),failed=len(out['failures']))),flush=True)
