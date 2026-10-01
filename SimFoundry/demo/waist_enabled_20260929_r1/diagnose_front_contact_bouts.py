"""Actual force-weighted contact migration before each front-route recovery."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(sys.argv[1]).resolve();rows=json.loads((p/'frontal_bypass.json').read_text())['rows'];assert json.loads((p/'frontal_bypass.json').read_text())['plan']['front_route_selected'];assert 'nudge_mailer' in p.name
with np.load(p/'trace.npz') as z:target=z['mailer'].astype(float)
with np.load(p/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['mailer']).as_matrix()
packets={x['after_action_step']:x for x in json.loads((p/'solved_contact_forces.json').read_text())['rows']};series=[];bouts=[];current=[]
for r in rows:
 t=r['step']
 if r['mode']!='top_push':
  if current:bouts.append(current);current=[]
  continue
 packet=packets.get(t-1);points=[];weights=[]
 if packet:
  assert np.max(abs(np.asarray(packet['post_action_pose']['mailer'])-target[t]))<1e-6
  for c in packet['parcel_contacts']:
   slots=[i for i,x in enumerate(c['shapes']) if '/mailer/' in x]
   if len(slots)!=1 or not any('left_wrist' in x for x in c['shapes']):continue
   force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
   if load>.05:points.append(c['position_world']);weights.append(load)
 record=dict(step=t,route_stage=r['route_stage'],observed_load_n=r['contact_load']['observed_vertical_load_n'],tip_minus_target_world_m=(np.asarray(r['observed_support_xyz'])-target[t]).tolist(),command_minus_tip_world_m=(np.asarray(r['target_xyz'])-r['observed_support_xyz']).tolist(),target_xyz=target[t].tolist(),yaw_rad=float(Rotation.from_matrix(rot[t]).as_euler('xyz')[2]))
 if weights:
  centroid=np.average(points,axis=0,weights=weights);local=rot[t].T@(centroid-target[t]);record.update(normal_load_n=float(sum(weights)),cop_local_xyz_m=local.tolist(),cop_xy_edge_margin_m=float(np.min(np.array([.075,.0725])-abs(local[:2]))),cop_world_xyz_m=centroid.tolist())
 current.append(record);series.append(record)
if current:bouts.append(current)
summary=[]
for bout in bouts:
 loaded=[r for r in bout if 'cop_local_xyz_m' in r];first=bout[0]['step'];last=bout[-1]['step'];after=next((r for r in rows if r['step']==last+1),None)
 def stats(rs):
  if not rs:return None
  return dict(frames=[r['step'] for r in rs],median_local_cop_m=np.median([r['cop_local_xyz_m'] for r in rs],axis=0).tolist(),median_edge_margin_m=float(np.median([r['cop_xy_edge_margin_m'] for r in rs])),median_load_n=float(np.median([r['normal_load_n'] for r in rs])))
 summary.append(dict(start=first,end=last,frames=len(bout),route_stages=sorted({r['route_stage'] for r in bout}),loaded_samples=len(loaded),first_loaded=stats(loaded[:5]),last_loaded=stats(loaded[-5:]),delta_target_xy_m=(target[min(last+1,len(target)-1),:2]-target[first,:2]).tolist(),next_mode=after['mode'] if after else None,recontact_reason=after.get('last_recontact_reason') if after and after['recontacts']>next(r['recontacts'] for r in rows if r['step']==last) else None))
out=dict(episode=p.name,bouts=summary,series=series,source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']},scope='Pre-action mode and previous last-substep measured contact matched by exact post-action pose. Force-weighted COP local edge distances use nominal object dimensions; not full contact patch, causal proof or collision certificate. All bouts and failures preserved; no training admission.',training_ready=False)
(p/'FRONT_CONTACT_BOUT_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
