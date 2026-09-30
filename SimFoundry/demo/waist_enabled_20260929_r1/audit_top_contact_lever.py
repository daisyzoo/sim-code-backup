"""Measured contact lever and motion by contiguous top-push segment, read only."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.spatial.transform import Rotation
run=Path(sys.argv[1]);status=json.loads((run/'STATUS.json').read_text())
assert status['stage']=='numeric_complete_actual_visual_review_pending'
rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1
 tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');yaw=np.unwrap(Rotation.from_quat(ori[key]).as_euler('xyz')[:,2]);cmd=json.loads((ep/'frontal_bypass.json').read_text())['rows'];forces={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 segments=[]
 for c in cmd:
  if c['mode']!='top_push':continue
  if not segments or c['step']!=segments[-1][-1]['step']+1:segments.append([])
  segments[-1].append(c)
 summaries=[]
 for segment in segments:
  samples=[]
  for row in segment:
   t=row['step'];poseframe=min(t+1,len(tr[key])-1);center=tr[key][poseframe];contacts=[]
   for c in forces.get(t,{}).get('parcel_contacts',[]):
    if not any(side+'_wrist' in s for s in c['shapes']) or not any('/'+actor+'/' in s for s in c['shapes']):continue
    force=np.array(c['force_world_N']);magnitude=np.linalg.norm(force)
    if magnitude<.5:continue
    lever=np.array(c['position_world'])-center
    contacts.append(dict(force_norm_N=float(magnitude),lever_x_m=float(lever[0]),lever_y_m=float(lever[1]),abs_yaw_moment_Nm=float(abs(np.cross(lever,force)[2])),abs_xyz_force_N=np.abs(force).tolist()))
   samples.append(dict(step=t,contacts=contacts))
  first,last=segment[0]['step'],segment[-1]['step'];cs=[c for sample in samples for c in sample['contacts']];weights=np.array([c['force_norm_N'] for c in cs]);weight_sum=weights.sum()
  summaries.append(dict(first_step=first,last_step=last,frames=len(segment),target_progress_m=float(direction*(tr[key][last,1]-tr[key][first,1])),yaw_change_deg=float(np.rad2deg(yaw[last]-yaw[first])),peak_abs_yaw_moment_Nm=max((sum(c['abs_yaw_moment_Nm'] for c in sample['contacts']) for sample in samples),default=0.),force_weighted_abs_x_lever_m=None if weight_sum==0 else float(sum(abs(c['lever_x_m'])*w for c,w in zip(cs,weights))/weight_sum),samples=samples))
 result=dict(episode=ep.name,segments=summaries);rows.append(result);print(ep.name,[{k:v for k,v in s.items() if k!='samples'} for s in summaries])
(run/'TOP_CONTACT_LEVER_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Contiguous top_push segments only; contact>0.5N, world lever from contact position to next pre-action object center as approximate post-action pose. Absolute per-contact yaw moment, not signed net torque or impulse. Frame-sampled forces, not every physics substep. Kinematic motion is recorded pre-action. No training admission.',training_ready=False),indent=2))
