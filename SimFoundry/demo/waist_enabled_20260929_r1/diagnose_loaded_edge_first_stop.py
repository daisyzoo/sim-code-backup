"""Read-only diagnosis and local retry screen at a stopped physical decision.
No candidate is executed or admitted. Current robot q is bound to the final pre
measurement and prior command to raw. Object xyz is bound to packet(t-1), but
orientation at the unexecuted stop exists only in the recorded decision context,
not a separately saved orientation frame. Feasibility is local to that context.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime
import numpy as np
from scipy.optimize import minimize,Bounds
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_loaded_edge_coverage';sys.path[:0]=[str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from audit_loaded_edge_coverage_record import verify,near
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
p=w/'loaded_edge_coverage_groups_r1/case_840001/layout_840001_push_box_to_bin';read=lambda n:json.loads((p/n).read_text());edge=read('loaded_edge_coverage.json');tr=edge['rows'][-1];t=tr['step'];assert edge['failure']==dict(step=t,reason='no_verified_nominal_edge_command') and tr['accepted'] is False
cs={r['step']:r for r in read('coordination.json')};fs={r['step']:r for r in read('frontal_bypass.json')['rows']};pack={r['after_action_step']:r for r in read('solved_contact_forces.json')['rows']};clear=read('self_clearance.json');pre=next(r for r in clear['rows'] if r['step']==t and r['phase']=='pre');q=np.asarray(pre['upper_q'],float);near(q,cs[t]['upper_q'],1e-7)
with np.load(p/'raw.npz') as z:assert len(z['q'])==t;previous=z['action'][-1,12:23].copy()
assert not any(r['step']==t and r['phase']=='final_command' for r in clear['rows'])
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);guard=ClearanceGuard(repo,stage);ctx=tr['context'];R=np.array(ctx['object_rotation']);quat=Rotation.from_matrix(R).as_quat();parent=np.array(tr['parent_upper_command']);offset=np.array(fs[t]['control_offset_local']);inp=cs[t]['task_inputs'];J=np.array(inp['jacobian']);E=np.array(inp['error']);damp=np.array(inp['damping']);low=np.array(tr['bound_low']);high=np.array(tr['bound_high']);cop=np.array(ctx['current_cop_local']);A=np.vstack([[-np.sign(cop[k])*R[:,k] for k in tr['threatened_axes']],[0,-1,0]])
def point(x):T,_,_=guard.model.fk('right',x);return T[:3,3]+T[:3,:3]@offset
def jac(x):
 T,jl,jw=guard.model.fk('right',x);a,b,c=T[:3,:3]@offset;skew=np.array([[0,-c,b],[c,0,-a],[-b,a,0]]);return jl-skew@jw
origin=point(q)
def constraints(x):return np.r_[A@(point(x)-origin),guard.geometry.constraints(x)-.005]
def cj(x):return np.vstack([A@jac(x),guard.geometry.jacobian(x)])
def check(x):
 z=copy.deepcopy(tr);z.update(accepted=True,override=True,reason='current_contact_nominal_edge_repair',command=np.asarray(x,dtype=np.float32).tolist(),final_upper_command=np.asarray(x,dtype=np.float32).tolist())
 try:
  out=verify(z,row=fs[t],previous_row=fs[t-1],coordinate=cs[t],current=q,previous_command=previous,parent_command=parent,final_command=z['command'],packet=pack[t-1],object_xyz=ctx['object_xyz'],object_quat=quat,core_size=ctx['core_size'],side='right',selected=True,hand=hand,elbows=elbows)
  return out
 except AssertionError as e:return dict(passed=False,error=str(e))
original=[];retries=[]
for a in tr['attempts']:
 x=np.asarray(a['final']['command']);original.append(dict(seed=a['seed'],solver_status=a['status'],original_accepted=a['accepted'],independent=check(x)))
 for scale in [1.,100.,5000.]:
  def cost(x):delta=x-q;res=J@delta-E;return scale*float(res@res+sum(damp*damp*delta*delta)),2*scale*(J.T@res+damp*damp*delta)
  fit=minimize(cost,np.clip(x,low,high),jac=True,bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=constraints,jac=cj)],method='SLSQP',options=dict(maxiter=300,ftol=1e-11))
  result=check(fit.x);retries.append(dict(seed=a['seed'],positive_objective_scale=scale,success=bool(fit.success),status=int(fit.status),iterations=int(fit.nit),independent=result,command=np.asarray(fit.x,dtype=np.float32).tolist()));print(retries[-1]['seed'],scale,fit.status,result.get('passed'),result.get('stationarity_residual'),flush=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();paths=[p/n for n in ['raw.npz','coordination.json','frontal_bypass.json','solved_contact_forces.json','self_clearance.json','loaded_edge_coverage.json']]+[Path(__file__),w/'audit_loaded_edge_coverage_record.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',stage/'articulated_hand_geometry.py',stage/'clearance_runtime.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json',urdf,vertices]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=p.name,stop_step=t,original_attempts=original,retries=retries,independently_feasible_stationary_original=sum(x['independent']['passed'] for x in original),verified_successful_local_retries=sum(x['success'] and x['independent']['passed'] for x in retries),source_sha256={str(p):sha(p) for p in paths},executed=False,training_ready=False)
(w/'LOADED_EDGE_FIRST_STOP_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print('SUMMARY',out['independently_feasible_stationary_original'],out['verified_successful_local_retries'])
