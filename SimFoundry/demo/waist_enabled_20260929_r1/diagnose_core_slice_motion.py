"""Measured motion of feasible world-X slice as COP Y/Z and object pose change."""
from pathlib import Path
import json,hashlib,numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['rear_cop_measured_bounds_groups_r1','rear_core_slice_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());key='box' if cid==840001 else 'mailer';h=np.array(fr['plan']['rear_cop_centering']['actual_core_size_xyz'])[:2]/2-.01
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
  rows=[];prior=None
  for r in fr['rows']:
   t=r['step'];c=r.get('rear_cop_centering',{})
   if not c.get('override'):prior=None;continue
   cop=np.array(c['cop_world']);local=R[t].T@(cop-xyz[t]);low,high=-float('inf'),float('inf')
   for j in range(2):
    a=R[t][0,j]
    if abs(a)<1e-10:
     if abs(local[j])>h[j]:low,high=1,0
    else:
     v=sorted([(-h[j]-local[j])/a,(h[j]-local[j])/a]);low=max(low,v[0]);high=min(high,v[1])
   if low>high or not np.isfinite([low,high]).all():prior=None;continue
   absolute=np.array([low,high])+cop[0];chosen=float(np.clip(c['anchor_world'][0],*absolute));fixed=np.array([chosen,cop[1],cop[2]]);assert np.all(abs((R[t].T@(fixed-xyz[t]))[:2])<=h+1e-9)
   if prior is not None:
    assert prior['step']==t-1
    feed=chosen-prior['chosen'];rows.append(dict(step=t,inset_world_x_interval_m=absolute.tolist(),chosen_slice_world_x_m=chosen,recorded_anchor_feed_mm=c['feed_x_m']*1000,measured_slice_feed_mm=feed*1000,omitted_slice_motion_mm=(feed-c['feed_x_m'])*1000,recorded_feedback_mm=c['feedback_x_m']*1000,recorded_command_delta_x_mm=c['command_delta_x_m']*1000,recorded_cop_delta_x_mm=(cop[0]-prior['cop_x'])*1000))
   prior=dict(step=t,chosen=chosen,cop_x=float(cop[0]))
  keys=['recorded_anchor_feed_mm','measured_slice_feed_mm','omitted_slice_motion_mm','recorded_feedback_mm','recorded_command_delta_x_mm','recorded_cop_delta_x_mm'];summary={k:dict(median=float(np.median([r[k] for r in rows])),p95_abs=float(np.percentile(abs(np.array([r[k] for r in rows])),95))) for k in keys};report=dict(run=run,episode=ep.name,continuous_valid_samples=len(rows),summary=summary,rows=rows,source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json']});reports.append(report);print(run,task,len(rows),json.dumps(summary),flush=True)
p=w/'CORE_SLICE_MOTION_DIAGNOSIS.json';assert not p.exists();p.write_text(json.dumps(dict(episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Same-current-COP Y/Z slice, preferred original object anchor X clamped to actual inset interval. Its measured interframe change differs from fixed object-anchor feedforward. Previous/current samples only; no forecast that command produces matching COP motion. Gaps and no-slice frames reset descriptive differencing; not a controller or success proof.'),indent=2))
