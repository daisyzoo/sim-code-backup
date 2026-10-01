"""Isolated bounded IK tracking recorded push bouts; no dynamics replay."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_contact_bout_yaw';sys.path[:0]=[str(stage),str(repo)]
s=(w/'screen_rear_top_contact_reach.py').read_text();exec(compile(s.split("run=root/'current_lateral_profile_r1'")[0],'<validated_fk_jac>','exec'))
from contact_bout_yaw import ContactBoutYaw,contact_bout_yaw_constraint
from simfoundry.data.contact_normal_constraint import contact_normal_constraint
run=w/'y_path_nearhalf_groups_r1';ep=run/'case_897003/layout_897003_nudge_mailer_to_bin'
with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};controls={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};bouts=json.loads((run/'LOADED_HAND_TWIST.json').read_text())['bouts'];mesh=np.asarray(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices']['left']);results=[]
for enabled in [False,True]:
 for bout in bouts:
  start=bout['first_push'];q=qs[start].copy();yaw_state=ContactBoutYaw();records=[];qsteps=[]
  for t in range(start,bout['last_push']+1):
   m,jl,jw=fk('left',q);r=m[:3,:3];normal=Rotation.from_quat(ori['mailer'][t]).as_matrix()[:,2];ref=projected_support_reference(mesh,r,normal);point=m[:3,3]+r@ref['reference_local'];ja=projected_support_jacobian(jl,jw,r,ref);mi,jli,jwi=fk('right',q);po=np.array([.20,0,.007]);pi=mi[:3,3]+mi[:3,:3]@po;ji=jli-skew(mi[:3,:3]@po)@jwi
   anchor=np.asarray(coords[t]['inactive_anchor']);nc=contact_normal_constraint(r,jw,coords[t]['contact_normal_tracking']['target_local_up']);a=yaw_state.update('top_push',r);yc=contact_bout_yaw_constraint(r,jw,a);goal=np.asarray(controls[t]['target_xyz']);jac=np.vstack([ja,ji,nc['jacobian']]+([yc['jacobian']] if enabled else []));error=np.r_[np.clip(.72*(goal-point),-.035,.035),np.clip(.72*(anchor-pi),-.035,.035),nc['error'],yc['error'] if enabled else []];dq=bounded_damped_step(jac,error,q,lo,hi,limits,damping);q+=dq
   assert np.max(abs(dq))<=.04000001 and abs(dq[0])<=.01500001
   gap=hand_face_separation('left').gap(m[:3,3],Rotation.from_matrix(r).as_quat(),tr['box'][t],ori['box'][t],(.14,.09,.045));low=m[:3,3]+r@ref['lowest_vertex_local'];local=Rotation.from_quat(ori['mailer'][t]).inv().apply(low-tr['mailer'][t]);records.append(dict(frame=t,pre_step_active_error_m=float(np.linalg.norm(point-goal)),pre_step_inactive_error_m=float(np.linalg.norm(pi-anchor)),heading_error_rad=yc['heading_error_rad'],hand_other_gap_m=float(gap),lowest_vertex_inside_xy=bool(abs(local[0])<=.075 and abs(local[1])<=.0725),q=q.tolist()));qsteps.append(dq.tolist())
  summary=dict(enabled=enabled,bout_start=start,steps=len(records),max_pre_step_active_error_m=max(r['pre_step_active_error_m'] for r in records),rms_pre_step_active_error_m=float(np.sqrt(np.mean([r['pre_step_active_error_m']**2 for r in records]))),max_abs_heading_error_rad=max(abs(r['heading_error_rad']) for r in records),min_hand_other_gap_m=min(r['hand_other_gap_m'] for r in records),lowest_vertex_outside_frames=sum(not r['lowest_vertex_inside_xy'] for r in records));results.append(dict(summary=summary,records=records));print(json.dumps(summary),flush=True)
report=dict(rows=results,candidate_sha256=hashlib.sha256((stage/'contact_bout_yaw.py').read_bytes()).hexdigest(),raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),scope='Actual bounded_damped_step with analytic independently checked URDF FK/Jacobian, projected support, original .15 normal term and bounds. One instantaneous command step per recorded push frame, each bout starts from measured q. Recorded goals/parcels held as exogenous observations, so this is NOT causal closed-loop replay, physical contact or task proof. No active production source changed. Whole-arm/swept collision/force not certified.',training_ready=False)
(stage/'BOUNDED_CONTROL_SCREEN.json').write_text(json.dumps(report,indent=2))
