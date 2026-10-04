"""Unissued local linearization diagnostic; ablations are not admissible commands.
Capture the unchanged candidate's exact constraint closures before optimization.
Local LP infeasibility does not prove nonlinear/global infeasibility.
"""
from pathlib import Path
import datetime, hashlib, json, sys, time
import numpy as np
from scipy.optimize import minimize
W=Path(__file__).resolve().parent; ROOT=W.parents[1]; S=W/'staged_front_effective_height_v1'
D=W/'front_normal_nondegradation_probe_r1'; D.mkdir(exist_ok=False)
sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
import front_xy_nonreversal_solver_candidate_v1 as candidate
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin'
cs={c['step']:c for c in read(ep/'coordination.json')}
g=ClearanceGuard(ROOT,S)
class Captured(BaseException): pass
capture={}
def intercept(fun,x0,**kwargs):
 capture.update(fun=fun,x0=x0,**kwargs)
 raise Captured()
candidate.minimize=intercept


from loaded_z_priority_checks import support_point
from scipy.spatial.transform import Rotation
rows=[]
steps=[r['step'] for r in read(W/'front_cross_track_full_stream_probe_r1/RESULT.json')['rows']]
assert len(steps)==34
for t in steps:
 c=cs[t];old=c['joint_transport_clearance'];tc=old['collector_context'];z=tc['scene']
 scene=RecontactScene(g,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size'])
 try:
  candidate.propose(step=t,side=z['side'],scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=old['parent_command'],decay=tc['decay'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True,cross_track_nonreversal=True,route_stage='lateral_y')
 except Captured:pass
 q=np.array(tc['current']);prev=np.array(tc['previous_command']);qp=np.array(tc['previous_q']);a=np.array(tc['decay']);parent=np.array(old['parent_command']);J=np.array(c['task_inputs']['jacobian']);parent_z=float(J[5]@(parent-q))
 original=capture['constraints'][0]['fun'];center=np.array(c['active_support_reference']['center_local']);normal=Rotation.from_quat(z['target_quat']).as_matrix()[:,2];reference=support_point(g.model,q,'right',normal,center);signs=np.sign(np.array(c['task_inputs']['error'])[3:5]);assert np.all(signs!=0)
 def pred(u):return (1-a)*u+a*q+q-prev-a*(qp-prev)
 def delta(u):return support_point(g.model,u,'right',normal,center)-reference
 parent_normal=float(normal@delta(parent));observed_load=float(c['front_loaded_z_priority']['context']['observed_vertical_load_n'])
 if parent_normal>=0 or observed_load<.3:
  row=dict(step=t,selection_rejected=True,reason='requires loaded original inward parent',parent_normal_delta_mm=parent_normal*1000,observed_vertical_load_n=observed_load,preliminary_passed=False,command=None,issued=False)
  rows.append(row)
  with (D/f'CONTEXT_{t}.json').open('x') as f:json.dump(row,f,indent=2,allow_nan=False)
  print(json.dumps(row),flush=True)
  continue
 original_predicted_normal=float(normal@delta(pred(np.array(old['output_command']))))
 def bounded_constraints(u):
  nom=delta(u);forecast=delta(pred(u));dn=float(normal@nom);dp=float(normal@forecast)
  return np.r_[original(u),signs*forecast[:2]*1000,(dn-parent_normal)*1000,-dn*1000,(original_predicted_normal-dp)*1000]
 start=time.monotonic();fit=minimize(capture['fun'],np.clip(parent,capture['bounds'].lb,capture['bounds'].ub),jac=True,bounds=capture['bounds'],constraints=[dict(type='ineq',fun=bounded_constraints)],method='SLSQP',options=dict(maxiter=240,ftol=1e-10))
 u=fit.x.astype(np.float32).astype(float);v=pred(u);vals=bounded_constraints(u);guard=g.command(u,q,prev);pathrows=[]
 for label,end in [('nominal',u),('predicted',v)]:
  for alpha in np.linspace(0,1,17):
   state=q+alpha*(end-q);d=scene.details(state);margins=np.r_[d['inactive_z']-.84,d['gaps']['inactive_target']-.01,d['gaps']['inactive_other']-.01,d['gaps']['active_other']-.01,g.geometry.constraints(state)-.005]
   pathrows.append(dict(path=label,alpha=float(alpha),minimum_margin_m=float(margins.min()),passed=bool(margins.min()>=-2e-7)))
 passed=bool(fit.success and vals.min()>=-.0002 and guard['accepted'] and all(r['passed'] for r in pathrows))
 row=dict(original_predicted_normal_delta_mm=original_predicted_normal*1000,parent_normal_delta_mm=parent_normal*1000,nominal_normal_delta_mm=float(normal@delta(u))*1000,predicted_normal_delta_mm=float(normal@delta(v))*1000,observed_vertical_load_n=observed_load,step=t,solver_success=bool(fit.success),status=int(fit.status),iterations=int(fit.nit),message=fit.message,command=u.tolist(),predicted_q=v.tolist(),minimum_scaled_margin=float(vals.min()),nominal_delta_mm=(delta(u)*1000).tolist(),predicted_delta_mm=(delta(v)*1000).tolist(),signed_nominal_xy_mm=(signs*delta(u)[:2]*1000).tolist(),signed_predicted_xy_mm=(signs*delta(v)[:2]*1000).tolist(),parent_linear_z_mm=parent_z*1000,proposal_linear_z_mm=float(J[5]@(u-q))*1000,height_change_mm=float(J[5]@(u-parent))*1000,original_final_guard=guard,sampled_paths=pathrows,preliminary_passed=passed,elapsed_s=time.monotonic()-start,independent_certificate=False,issued=False)
 rows.append(row)
 with (D/f'CONTEXT_{t}.json').open('x') as f:json.dump(row,f,indent=2,allow_nan=False)
 print(json.dumps({k:row[k] for k in ['step','status','preliminary_passed','minimum_scaled_margin','height_change_mm','signed_nominal_xy_mm','signed_predicted_xy_mm','predicted_delta_mm','nominal_normal_delta_mm','predicted_normal_delta_mm','original_predicted_normal_delta_mm','elapsed_s']}),flush=True)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Unissued exact object-normal support-height interval [parent inward displacement,0], predicted normal displacement no more outward than original final-command prediction; original full9 objective, all original geometry/normal inequalities, nominal and predicted XY nonreversal. Requires observed load>=0.3N and inward parent.',rows=rows,contexts=len(rows),preliminary_passed=sum(r['preliminary_passed'] for r in rows),source_sha256={str(p):sha(p) for p in [Path(__file__),Path(candidate.__file__),W/'probe_front_exact_normal_band_v1.py',ep/'coordination.json']},installed=False,physics_started=False,training_ready=False,limitations=['New planning policy not original exact Z equality.','Static current object normal/pose and old causal histories; not actual force or contact retention.','No independent KKT/continuous path/source/native certification.','Explicitly rejected unloaded/outward parents still need a complete recovery strategy.','No physical commands or training admissions.','Prediction is a relative nondegradation comparison, not proof of no outward actual movement or contact retention; absolute zero constraint was separately diagnosed.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
print(json.dumps(dict(contexts=report['contexts'],preliminary_passed=report['preliminary_passed'])),flush=True)
