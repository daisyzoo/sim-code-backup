"""Seven original contact-entry snapshots, full9D IK->quarterZ->transport->guard.
First reproduce original final commands, then change only explicit XY waypoint.
Independent old9D feasibility/KKT retained. Fixed original observations/history:
not a recursive rollout, realized hold/force, whole-body or data-admission proof.
"""
from pathlib import Path
from copy import deepcopy
import datetime,hashlib,json,sys,traceback
import numpy as np
from scipy.optimize import nnls
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_bag_preload_command_chain_r2';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from task_ik_precision import solve
from front_loaded_z_fraction import FrontLoadedZFraction
from joint_transport_effective_height_runtime_v1 import JointTransportRuntime
from recontact_scene import RecontactScene
from loaded_z_priority_checks import support_point
from audit_self_clearance_task_optimality import IndependentElbows
from simfoundry.data.bounded_ik import bounded_damped_step
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
def main():
 ep=W/'front_effective_height_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};coords={r['step']:r for r in read(ep/'coordination.json')};trs=read(ep/'joint_transport_clearance.json')['rows'];proposal=read(W/'front_bag_preload_waypoint_r1/RESULT.json');assert proposal['passed']
 for p,h in proposal['source_sha256'].items():assert sha(p)==h,p
 with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
 guard=ClearanceGuard(ROOT,S);zref=FrontLoadedZFraction(guard,fraction=.25);transport=JointTransportRuntime(guard,ROOT,S,enabled=True,effective_quarter_height=True)
 prov=read(ep.parent/'provenance.json');snap=ep.parent/'source_snapshot'
 def archived(name):
  names=[n for n in prov['source_sha256'] if n.endswith('/'+name)];assert len(names)==1;p=snap/names[0];assert sha(p)==prov['source_sha256'][names[0]];return p
 geom=IndependentElbows(archived('elbow_torso_hulls.json'),archived('g1_23dof_rev_1_0_u1_black.urdf'))
 def certificate(a,x,tr):
  J,E,cur,prev,lo,hi,lim,damp,prior=[np.asarray(a[k],float) for k in ['jacobian','error','current','previous','lower','upper','step_limits','damping','preferred_step']];assert J.shape==(9,11)
  low=np.maximum.reduce([lo,cur-lim,prev-.055]);high=np.minimum.reduce([hi,cur+lim,prev+.055]);gap=geom.gap(x);assert min(gap)>=.005-2e-7 and np.all(x>=low-2e-7) and np.all(x<=high+2e-7)
  baseline=(cur+bounded_damped_step(J,E,cur,lo,hi,lim,damp,preferred_step=prior)).astype(np.float32);baseline_valid=bool(np.all(baseline>=low-2e-7) and np.all(baseline<=high+2e-7) and min(geom.gap(baseline))>=.005-2e-7)
  if not tr['override']:assert baseline_valid and np.array_equal(x,baseline);return dict(passed=True,override=False)
  assert not baseline_valid and tr['solver_success'] and tr['status']==0 and tr['iterations']<=150
  gradient=J.T@(J@(x-cur)-E)+damp*damp*(x-cur-prior);G=geom.gradient(x);constraints=[]
  for i in range(2):
   if gap[i]-.005<=1e-6:constraints.append(G[i])
  for i in range(11):
   if x[i]-low[i]<=2e-6:constraints.append(np.eye(11)[i])
   if high[i]-x[i]<=2e-6:constraints.append(-np.eye(11)[i])
  if constraints:
   A=np.array(constraints);norm=np.linalg.norm(A,axis=1);A=A[norm>1e-12]/norm[norm>1e-12,None];_,res=nnls(A.T,gradient,maxiter=1000)
  else:res=float(np.linalg.norm(gradient))
  assert res<=1e-6,res;return dict(passed=True,override=True,stationarity_residual=float(res))
 output=[]
 for item in proposal['isolated_original_entry_proposals']:
  t=item['step'];original=coords[t];tc=trs[t]['collector_context'];sc=tc['scene'];scene=RecontactScene(guard,sc['side'],sc['target_xyz'],sc['target_quat'],sc['core_size'],sc['other_xyz'],sc['other_quat'],sc['other_size']);zc=original['front_loaded_z_priority']['context'];a=original['task_inputs'];assert np.array_equal(a['current'],q[t]) and np.array_equal(a['previous'],u[t-1]);assert not original['terminal_joint_hold'];assert original['preferred_waist_step_rad']==0
  exact_old_error=np.clip(np.float32(.72)*(np.asarray(fr[t]['target_xyz'],np.float32)-np.asarray(original['control_point_positions']['left'],np.float32)),np.float32(-.035),np.float32(.035));np.testing.assert_array_equal(exact_old_error,a['error'][:3])
  branches={}
  for changed in [False,True]:
   c=deepcopy(original);row=deepcopy(fr[t]);a=deepcopy(a)
   for k in ['front_loaded_z_priority','joint_transport_clearance','joint_transport_unexecuted_parent_waist_target_rad','unexecuted_parent_waist_target_rad']:c.pop(k,None)
   if changed:
    row['target_xyz']=item['output_target_xyz'];new_error=np.clip(np.float32(.72)*(np.asarray(row['target_xyz'],np.float32)-np.asarray(c['control_point_positions']['left'],np.float32)),np.float32(-.035),np.float32(.035));a['error'][:3]=new_error.tolist();assert a['error'][2]==original['task_inputs']['error'][2] and a['error'][3:]==original['task_inputs']['error'][3:]
   base,tr=solve(enabled=True,geometry=guard.geometry,**a);assert base is not None and tr['accepted'];cert=certificate(a,base.astype(float),tr)
   c.update(task_inputs=a,self_clearance_task=tr,waist_target_rad=float(base[0]),front_loaded_z_priority_side='left')
   parent=np.clip(base.astype(np.float32),u[t-1]-.055,u[t-1]+.055).astype(np.float32);parent[0]=np.clip(parent[0],-1.,1.)
   if not changed:np.testing.assert_array_equal(parent,zc['parent_command'])
   zcmd,zrecord=zref.refine(step=t,selected=True,row=row,coordinate=c,current=q[t],previous=u[t-1],parent_command=parent,target_rotation=zc['target_rotation'],other_xyz=zc['other_xyz'],other_rotation=zc['other_rotation'],other_size=zc['other_size']);c['front_loaded_z_priority']=zrecord
   if zrecord['applied']:c['unexecuted_parent_waist_target_rad']=c['waist_target_rad'];c['waist_target_rad']=float(zcmd[0])
   cmd,trecord=transport.refine(step=t,selected=True,side='left',row=row,coordinate=c,scene=scene,current=q[t],previous_q=q[t-1],previous_command=u[t-1],parent_command=zcmd,decay=tc['decay']);final=guard.command(cmd,q[t],u[t-1]);assert final['accepted']
   if not changed:np.testing.assert_array_equal(cmd,u[t])
   normal=np.asarray(zc['target_rotation'])[:,2];center=np.asarray(zc['center_local']);p0=support_point(guard.model,q[t],'left',normal,center);p1=support_point(guard.model,cmd,'left',normal,center);decay=np.asarray(tc['decay']);prediction=(1-decay)*cmd+decay*q[t]+q[t]-u[t-1]-decay*(q[t-1]-u[t-1]);pp=support_point(guard.model,prediction,'left',normal,center)
   branches['candidate' if changed else 'original']=dict(command=np.asarray(cmd).tolist(),full9D_certificate=cert,z_applied=zrecord['applied'],transport_applied=trecord['applied'],transport_reason=trecord['reason'],final_guard_passed=True,nominal_support_delta_mm=(1000*(p1-p0)).tolist(),forecast_support_delta_mm=(1000*(pp-p0)).tolist(),final_joint_max_change_from_old_rad=float(np.max(abs(cmd-u[t]))),waypoint_xy_error_mm=(1000*(np.asarray(row['target_xyz'][:2])-p0[:2])).tolist(),z_record=zrecord,transport_record=trecord)
  output.append(dict(step=t,branches=branches));print(json.dumps(dict(step=t,original_reproduced=True,candidate_nominal_support_delta_mm=branches['candidate']['nominal_support_delta_mm'],candidate_forecast_support_delta_mm=branches['candidate']['forecast_support_delta_mm'])),flush=True)
 sources={str(p):sha(p) for p in [Path(__file__),W/'front_bag_preload_waypoint_r1/RESULT.json',W/'audit_self_clearance_task_optimality.py',*[ep/n for n in ['raw.npz','frontal_bypass.json','coordination.json','joint_transport_clearance.json']]]};sources.update({str(p):sha(p) for p in S.iterdir() if p.is_file()})
 return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,original_entry_contexts=7,rows=output,source_sha256=sources,recursive_history_verified=False,actual_force_or_hold_verified=False,whole_body_dynamics_verified=False,installed=False,training_ready=False)
try:
 out=main();(D/'RESULT.json').write_text(json.dumps(out,indent=2));print('PASSED seven entry command chains',flush=True)
except Exception:
 (D/'FAILURE.log').write_text(traceback.format_exc());(D/'RESULT.json').write_text(json.dumps(dict(passed=False,training_ready=False,scope=__doc__)));raise
