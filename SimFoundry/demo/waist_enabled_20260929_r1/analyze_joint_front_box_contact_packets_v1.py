"""Recompute actual front-box pressure-centroid motion from solved contact packets.
Descriptive association only: pressure centroid is not a tracked material point.
No modified actions, future rollout, force fitting, quality change or admission.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'joint_transport_physical_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
report=R/'FRONT_BOX_THREE_RUN_TRANSPORT_DIAGNOSIS.json';budget=json.loads(report.read_text())
for p,h in budget['source_sha256'].items():assert sha(p)==h,p
sources={str(report):sha(report),str(Path(__file__)):sha(__file__)};results=[]
for case in budget['runs']:
 ep=Path(case['episode']);fr=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in fr['rows']}
 packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];assert [p['after_action_step'] for p in packets]==list(range(1200))
 with np.load(ep/'trace.npz') as z:xyz=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:mat=Rotation.from_quat(z['box']).as_matrix()
 half=np.asarray(fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'])/2
 measured={};errors=[]
 for t,row in rows.items():
  if row['mode']!='top_push':continue
  packet=packets[t-1];np.testing.assert_allclose(packet['post_action_pose']['box'],xyz[t],atol=2e-6,rtol=0)
  points=[];weights=[]
  for c in packet['parcel_contacts']:
   slots=[i for i,v in enumerate(c['shapes']) if '/parcel_box/' in v]
   if len(slots)!=1 or not any('right_wrist' in v for v in c['shapes']):continue
   force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@mat[t,:,2])
   if normal>.05:points.append(c['position_world']);weights.append(normal)
  if not weights or sum(weights)<.3:continue
  cop=np.average(points,axis=0,weights=weights);local=mat[t].T@(cop-xyz[t]);saved=row['cop_slip_following'].get('measured_cop_local')
  if saved is not None:
   errors.append(float(np.max(np.abs(local-np.asarray(saved)))));np.testing.assert_allclose(local,saved,atol=2e-6,rtol=0)
  measured[t]=dict(step=t,cop_local_mm=(local*1000).tolist(),normal_n=sum(weights),nearest_xy_core_edge_mm=float(np.min(half[:2]-abs(local[:2]))*1000),target_y_mm=float(xyz[t,1]*1000),observed_tilt_rad=row['observed_parcel_tilt_rad'])
 bouts=[]
 for b in case['bouts']:
  cc=[measured[t] for t in range(b['start'],b['end']+1) if t in measured];assert cc
  a,z=cc[0],cc[-1];travel=-(xyz[z['step'],1]-xyz[a['step'],1])*1000;coptravel=-(z['cop_local_mm'][1]-a['cop_local_mm'][1])
  bouts.append(dict(start=b['start'],end=b['end'],exit_reason=b['exit_reason'],route_stage=b['route_stage'],valid_prior_packets=len(cc),first=a,last=z,within_observed_contact_target_progress_mm=float(travel),cop_local_y_migration_mm=float(coptravel),median_normal_n=float(np.median([c['normal_n'] for c in cc])),minimum_core_edge_mm=min(c['nearest_xy_core_edge_mm'] for c in cc),target_progress_full_bout_mm=b['target_progress_mm']))
 tilt=[b for b in bouts if b['exit_reason']=='incipient_tilt_independent']
 summary=dict(run=case['run'],bouts=len(bouts),tilt_bouts=len(tilt),independently_checked_contact_frames=len(errors),max_saved_cop_error_m=max(errors),median_tilt_bout_target_motion_mm=float(np.median([b['within_observed_contact_target_progress_mm'] for b in tilt])),median_tilt_bout_cop_migration_mm=float(np.median([b['cop_local_y_migration_mm'] for b in tilt])),median_tilt_bout_initial_local_y_mm=float(np.median([b['first']['cop_local_mm'][1] for b in tilt])),median_tilt_bout_last_local_y_mm=float(np.median([b['last']['cop_local_mm'][1] for b in tilt])),median_tilt_bout_normal_n=float(np.median([b['median_normal_n'] for b in tilt])))
 results.append(dict(summary=summary,bouts=bouts,contact_rows=list(measured.values())))
 for n in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']:sources[str(ep/n)]=sha(ep/n)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=results,source_sha256=sources,findings=['The pressure centroid migrating toward the forward edge is independently reproduced from actual prior-step forces and current box orientation.','Centroid migration and repeated tilt exits coexist; neither proves material-point sticking/sliding or a unique force mechanism.','Landing-offset and tangential-relative-speed ideas address different mechanisms; current reserve and rear-only trial must remain isolated.','No hypothetical landing offset is declared sufficient to reach the original target zone.'],training_ready=False)
with (R/'FRONT_BOX_ACTUAL_CONTACT_PACKETS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([r['summary'] for r in results],indent=2))
