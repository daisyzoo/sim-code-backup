"""Causal measured-wrench relanding screen for all original front-selected tasks.
Only prior completed action packets enter each ten-observation window. These
are last-physics-tick samples, NOT integrated impulses or causal intervention
outcomes. Algebraically moving unchanged force application points is a local
hypothesis; it is NOT a friction law or proof that a new hand landing sets COP.
No object pose/force writes, controller mutation, layout exclusion or admission.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;B=W/'fresh_closed_peak_trials_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
episodes=sorted(B.glob('case_*/layout_*'))+[W/'terminal_margin_physical_r1/case_840015/layout_840015_nudge_mailer_to_bin']
for ep in episodes:
 f=ep/'frontal_bypass.json'
 if not f.exists():continue
 log=json.loads(f.read_text());plan=log['plan']
 if not plan.get('front_route_selected'):continue
 key='box' if 'push_box_to_bin' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';direction=-1 if key=='box' else 1;sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};core=sizes[key]
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);obstacle=z[other].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix();orot=Rotation.from_quat(z[other]).as_matrix()
 packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};rows={r['step']:r for r in log['rows']};moments={};force_frames=0
 for t in range(1,len(xyz)):
  pk=packets[t-1];assert np.max(abs(np.array(pk['post_action_pose'][key])-xyz[t]))<1e-6
  F=np.zeros(3);M=np.zeros(3);points=[];weights=[];decomposed=[]
  for c in pk['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1 or not any(side+'_wrist_roll_rubber_hand' in s for s in c['shapes']):continue
   sign=1 if slots[0]==1 else -1;cf=np.array(c['force_torque_contact']);frame=np.array(c['contact_frame']);assert np.allclose(cf[:3]@frame,c['force_world_N'],rtol=2e-6,atol=2e-6)
   force=sign*np.array(c['force_world_N']);torque=sign*cf[3:]@frame;point=np.array(c['position_world']);F+=force;M+=np.cross(point-xyz[t],force)+torque;weight=max(0.,-float(force@rot[t,:,2]));points.append((point-xyz[t])@rot[t]);weights.append(weight);decomposed.append(dict(force=force.tolist(),torque=torque.tolist(),relative_point=(point-xyz[t]).tolist()))
  total=sum(weights);cop=np.average(points,axis=0,weights=weights) if total>0 else None;moments[t]=dict(observation_step=t,action_step=t-1,force=F,moment=M,normal=total,cop=cop,contacts=decomposed);force_frames+=int(total>.3)
 reasons=collections.Counter();chosen=None;first_narrow=None;eligible_windows=[]
 for t,row in rows.items():
  if row['mode']!='top_push' or row.get('route_stage')!='lateral_y':continue
  tr=abs(rot[t])@(core/2);orr=abs(orot[t])@(sizes[other]/2);width=float(obstacle[t,0]-orr[0]-2*tr[0]-.012-.285)
  if width>.020:reasons['corridor_not_narrow']+=1;continue
  if first_narrow is None:first_narrow=t
  if width<=0:reasons['no_original_geometric_corridor']+=1;continue
  times=list(range(t-9,t+1))
  if times[0]<2 or any(rows[k-1]['mode']!='top_push' or rows[k-1].get('route_stage')!='lateral_y' for k in times):reasons['ten_prior_actions_not_continuous_lateral']+=1;continue
  window=[moments[k] for k in times];loaded=sum(v['normal']>.3 for v in window);F=np.mean([v['force'] for v in window],axis=0);M=np.mean([v['moment'] for v in window],axis=0)
  if loaded<8 or direction*F[1]<.3:reasons['insufficient_stable_forward_contact']+=1;continue
  cop=np.average([v['cop'] for v in window if v['normal']>0],axis=0,weights=[v['normal'] for v in window if v['normal']>0]);dx=float(-M[2]/F[1]);offset=np.array([dx,0.,0.]);landing=cop+rot[t].T@offset;inset=float(np.min(core[:2]/2-abs(landing[:2])));residual=float(M[2]+dx*F[1]);assert abs(residual)<1e-10
  inside=inset>=.014 # original12mm planner inset plus2mm endpoint localization box
  proposal=dict(step=t,source_actions=[v['action_step'] for v in window],first_narrow_step=first_narrow,current_corridor_width_m=width,loaded_last_tick_samples=loaded,mean_last_tick_force_N=F.tolist(),mean_last_tick_moment_Nm=M.tolist(),normal_weighted_cop_local_m=cop.tolist(),hypothetical_world_x_shift_m=dx,proposed_contact_local_xy_m=landing[:2].tolist(),proposed_point_inset_m=inset,original12mm_inset_plus2mm_tolerance=inside,algebraic_frozen_force_moment_residual_Nm=residual,actual_COP_after_relanding_unproven=True)
  eligible_windows.append(proposal)
  if not inside:reasons['corrective_landing_outside_original_inset']+=1;continue
  if chosen is None:chosen=proposal
 record=dict(episode=str(ep.relative_to(W)),original_task_passed=json.loads((ep/'quality.json').read_text())['passed'],side=side,target_key=key,initial_xyz=xyz[0].tolist(),first_narrow_step=first_narrow,loaded_last_tick_samples=force_frames,rejections=dict(reasons),eligible_contact_windows=len(eligible_windows),first_contact_window=eligible_windows[0] if eligible_windows else None,chosen_first_causal_inside_landing=chosen,source_sha256={str(ep/n):sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','quality.json']})
 records.append(record);print(record['episode'],'task',record['original_task_passed'],'selected',None if chosen is None else (chosen['step'],chosen['hypothetical_world_x_shift_m'],chosen['proposed_contact_local_xy_m']),'rejects',record['rejections'],flush=True)
assert len(records)==9
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=records,candidate_rule=dict(window=10,minimum_loaded_samples=8,normal_sample_threshold_n=.3,minimum_mean_task_force_n=.3,maximum_corridor_width_m=.020,minimum_landing_inset_m=.014),source_sha256={str(Path(__file__)):sha(__file__),str(B/'RECORDED_CONTACT_FORCE_SIGN_CHECK.json'):sha(B/'RECORDED_CONTACT_FORCE_SIGN_CHECK.json')},simulation_started=False,collector_integrated=False,training_ready=False)
dest=W/'FRONT_CAUSAL_WRENCH_RELANDING_SCREEN.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2))
