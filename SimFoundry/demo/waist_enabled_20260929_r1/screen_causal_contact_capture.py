"""Causal measured-vertex capture in bounded offline IK; no physical execution."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
s=(w/'screen_rear_top_contact_reach.py').read_text();exec(compile(s.split("run=root/'current_lateral_profile_r1'")[0],'<checked FK and Jacobians>','exec'))
from simfoundry.data.top_contact_bypass import top_surface_point
cases=[w/'contact_bout_yaw_groups_r1/case_898001/layout_898001_push_box_to_bin',w/'fresh_diagonal_02_trial_v2_r1/case_840004/layout_840004_nudge_mailer_to_bin'];results=[]
for ep in cases:
 side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);other_size=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'raw.npz') as z:q0=z['q'][-1,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:tr={k:z[k][-1] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k][-1] for k in z.files}
 coord=json.loads((ep/'coordination.json').read_text())[-1];assert coord['contact_normal_tracking'] is None;anchor=np.array(coord['inactive_anchor']);verts=np.array(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);target_rotation=Rotation.from_quat(ori[key]).as_matrix();normal=target_rotation[:,2];m,_,_=fk(side,q0);ref0=projected_support_reference(verts,m[:3,:3],normal);physical0=m[:3,3]+m[:3,:3]@ref0['lowest_vertex_local'];half=size[:2]/2-.01;local0=target_rotation.T@(physical0-tr[key]);goal_local=np.r_[np.clip(local0[:2],-half,half),size[2]/2]
 fk_error=float(np.linalg.norm(m[:3,3]+m[:3,:3]@np.array([.20,0,.007])-tr['palm_'+side]));assert fk_error<.0001
 for capture in [False,True]:
  q=q0.copy();center=ref0['lowest_vertex_local'] if capture else None;goal=tr[key]+target_rotation@goal_local if capture else np.array(top_surface_point(tr[key],ori[key],size));m,_,_=fk(side,q);ref=projected_support_reference(verts,m[:3,:3],normal,center_local=center);point=m[:3,3]+m[:3,:3]@ref['reference_local'];descent_z=point[2];history=[]
  for k in range(400):
   m,jl,jw=fk(side,q);r=m[:3,:3];ref=projected_support_reference(verts,r,normal,center_local=center);point=m[:3,3]+r@ref['reference_local'];physical=m[:3,3]+r@ref['lowest_vertex_local'];local=target_rotation.T@(physical-tr[key]);xy=float(max(abs(point[:2]-goal[:2])));inside=bool(np.all(abs(local[:2])<=half+1e-8));gap=float(hand_face_separation(side).gap(m[:3,3],Rotation.from_matrix(r).as_quat(),tr[other],ori[other],other_size));height=float(local[2]-size[2]/2)
   if xy<.010:descent_z=max(goal[2]+.004,descent_z-.0015)
   desired=np.r_[goal[:2],descent_z];mi,jli,jwi=fk(inactive,q);po=np.array([.20,0,.007]);pi=mi[:3,3]+mi[:3,:3]@po;ji=jli-skew(mi[:3,:3]@po)@jwi;ja=projected_support_jacobian(jl,jw,r,ref)
   record=dict(step=k,virtual_xy_error_m=xy,physical_lowest_inside_10mm_inset=inside,physical_top_gap_m=height,hand_other_gap_m=gap,waist_rad=float(q[0]),inactive_error_m=float(np.linalg.norm(pi-anchor)),support_index=int(ref['support_index']));history.append(record)
   if capture and (not inside or gap<.005):break
   if inside and xy<.010 and .003<=height<=.005 and np.linalg.norm(pi-anchor)<.002:break
   dq=bounded_damped_step(np.vstack([ja,ji]),np.r_[np.clip(.72*(desired-point),-.035,.035),np.clip(.72*(anchor-pi),-.035,.035)],q,lo,hi,limits,damping);assert max(abs(dq))<=.04000001 and abs(dq[0])<=.01500001;q+=dq
  success=bool(history[-1]['physical_lowest_inside_10mm_inset'] and history[-1]['virtual_xy_error_m']<.01 and .003<=history[-1]['physical_top_gap_m']<=.005 and history[-1]['inactive_error_m']<.002 and min(x['hand_other_gap_m'] for x in history)>=.005)
  row=dict(episode=ep.name,capture_current_physical_vertex=capture,contact_goal_local=goal_local.tolist() if capture else None,steps=len(history),geometric_approach_reached=success,min_hand_other_gap_m=min(x['hand_other_gap_m'] for x in history),support_switches=sum(a['support_index']!=b['support_index'] for a,b in zip(history,history[1:])),final=history[-1],actual_fk_error_m=fk_error,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),history=history);results.append(row);print(json.dumps({k:v for k,v in row.items() if k!='history'}),flush=True)
report=dict(rows=results,scope='Each candidate selects its hand-local tangential center from actual q0 lowest vertex and projects current physical support onto legal10mm-inset top region; does NOT consume optimized/hindsight q. Fixed recorded objects, analytic FK/Jacobians, original bounded step solver/inactive anchor and descent rate. No normal anchor before first contact. Guards reject sampled hand-other interference or support leaving inset. Approaching within3..5mm of top is NOT actual loaded contact, continuous dynamics, full-arm collision, camera improvement or sorting proof. No production change or joint command execution.',training_ready=False)
(w/'CAUSAL_CONTACT_CAPTURE_SCREEN.json').write_text(json.dumps(report,indent=2))
