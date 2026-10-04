"""Observed bag yaw and unsigned contact-load history around first corridor stop.
One earliest completed-solve boundary per tick1..24; no signed impulse or
force/state synchronization is assumed. Full control audits remain separate.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'front_corridor_lateral_physical_r1';ep=R/'case_840023/layout_840023_nudge_mailer_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json');m=meta['metadata'];assert meta['recording_sha256']==sha(ep/'substep_contacts.npz');assert meta['action_intervals']==1200 and m['expected_substeps']==24 and meta['force_body_sign_not_yet_verified'] and meta['force_state_timing_not_assumed_synchronous'];labels=m['shape_labels'];first=read(R/'FRONT_BAG_FIRST_GUARD_DIAGNOSIS.json')['first_guard_step'];fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};assert first==649
with np.load(ep/'substep_contacts.npz') as z:a={k:z[k].copy() for k in z.files}
with np.load(ep/'trace.npz') as z:xyz=z['mailer'].copy()
with np.load(ep/'parcel_orientation.npz') as z:quat=z['mailer'].copy()
interval=24+m['expected_manager_steps'];assert len(a['action_step'])==1200*interval;off=a['contact_offsets'];rows=[]
for step in range(first-6,first+1):
 ids=np.flatnonzero(a['action_step']==step);assert len(ids)==interval;stamps=a['substep_tick'][ids];initial=ids[np.flatnonzero(stamps==0)[0]];chosen=[int(ids[np.flatnonzero(stamps==i)[0]]) for i in range(1,25)];final=int(ids[-1]);assert a['kind'][final]==1 and stamps[-1]==24
 np.testing.assert_allclose(a['body_q'][initial,1,:3],xyz[step],atol=2e-6,rtol=0);np.testing.assert_allclose(a['body_q'][final,1,:3],xyz[step+1],atol=2e-6,rtol=0);assert (Rotation.from_quat(a['body_q'][initial,1,3:])*Rotation.from_quat(quat[step]).inv()).magnitude()<2e-6;assert (Rotation.from_quat(a['body_q'][final,1,3:])*Rotation.from_quat(quat[step+1]).inv()).magnitude()<2e-6
 yaw=np.unwrap(Rotation.from_quat(a['body_q'][[int(initial),*chosen],1,3:]).as_euler('xyz')[:,2]);values=[]
 for tick,j in enumerate(chosen,1):
  loads=dict(left_hand_vertical_abs_n=0.,right_hand_vertical_abs_n=0.,table_vertical_abs_n=0.,other_robot_force_norm_sum_n=0.,box_contact_force_norm_sum_n=0.);contacts=range(int(off[j]),int(off[j+1]))
  for k in contacts:
   names=[labels[int(i)] for i in a['shape_ids'][k]]
   if not any('/mailer/' in n for n in names):continue
   force=a['force_torque_world'][k,:3].astype(float)
   if any('left_wrist_roll' in n for n in names):loads['left_hand_vertical_abs_n']+=abs(float(force[2]))
   elif any('right_wrist_roll' in n for n in names):loads['right_hand_vertical_abs_n']+=abs(float(force[2]))
   elif any('/Robot/' in n for n in names):loads['other_robot_force_norm_sum_n']+=float(np.linalg.norm(force))
   if any('/table/' in n for n in names):loads['table_vertical_abs_n']+=abs(float(force[2]))
   if any('/parcel_box/' in n for n in names):loads['box_contact_force_norm_sum_n']+=float(np.linalg.norm(force))
  values.append(dict(tick=tick,yaw_deg=float(np.degrees(yaw[tick])),yaw_change_deg=float(np.degrees(yaw[tick]-yaw[tick-1])),**loads))
 row=dict(action_step=step,controller_mode=fr[step]['mode'],first_guard_action=step==first,yaw_before_deg=float(np.degrees(yaw[0])),yaw_after_deg=float(np.degrees(Rotation.from_quat(a['body_q'][final,1,3:]).as_euler('xyz')[2])),within_action_yaw_change_deg=float(np.degrees(yaw[-1]-yaw[0])),maximum_single_tick_yaw_change_deg=max(abs(v['yaw_change_deg']) for v in values),peak_left_hand_vertical_abs_n=max(v['left_hand_vertical_abs_n'] for v in values),final_left_hand_vertical_abs_n=values[-1]['left_hand_vertical_abs_n'],peak_box_contact_force_norm_sum_n=max(v['box_contact_force_norm_sum_n'] for v in values),peak_other_robot_force_norm_sum_n=max(v['other_robot_force_norm_sum_n'] for v in values),peak_right_hand_vertical_abs_n=max(v['right_hand_vertical_abs_n'] for v in values),ticks=values);rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='ticks'}),flush=True)
source=[Path(__file__),ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'frontal_bypass.json',R/'FRONT_BAG_FIRST_GUARD_DIAGNOSIS.json'];out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,first_guard_step=first,solver_dt_s=m['solver_dt_s'],rows=rows,source_sha256={str(p):sha(p) for p in source},first_tick_excluded=True,boundary_duplicates_not_double_counted=True,force_sign_verified=False,force_state_synchronous=False,causal_mechanism_proven=False,training_ready=False)
with (R/'FRONT_BAG_FIRST_GUARD_SUBSTEP_HISTORY.json').open('x') as f:json.dump(out,f,indent=2)
