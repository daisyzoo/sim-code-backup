"""Actual prior-solve COP and box orientation at each rear push bout.
Pressure centroid is not a material point; geometry correlation is not causality.
No alternate contact pose, force prediction or physics is executed here.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'joint_transport_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();budget=json.loads((R/'REAR_BOX_THREE_RUN_BUDGET_DIAGNOSTIC.json').read_text());results=[];sources={str(R/'REAR_BOX_THREE_RUN_BUDGET_DIAGNOSTIC.json'):sha(R/'REAR_BOX_THREE_RUN_BUDGET_DIAGNOSTIC.json')}
for case in budget['records']:
 ep=W/case['run']/'case_840023/layout_840023_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in fr['rows']};packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];assert len(packets)==1200 and [r['after_action_step'] for r in packets]==list(range(1200))
 half=np.asarray(fr['plan']['rear_cop_centering']['actual_core_size_xyz'])/2
 with np.load(ep/'trace.npz') as z:xyz=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:rotation=Rotation.from_quat(z['box']);mat=rotation.as_matrix();euler=rotation.as_euler('xyz',degrees=True)
 contacts={}
 for t,row in rows.items():
  if row['mode']!='top_push':continue
  packet=packets[t-1];np.testing.assert_allclose(packet['post_action_pose']['box'],xyz[t],atol=2e-6,rtol=0);points=[];weights=[]
  for c in packet['parcel_contacts']:
   slots=[i for i,label in enumerate(c['shapes']) if '/parcel_box/' in label]
   if len(slots)!=1 or not any('right_wrist' in label for label in c['shapes']):continue
   force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@mat[t,:,2])
   if normal>.05:points.append(c['position_world']);weights.append(normal)
  if not weights or sum(weights)<.3:continue
  cop=np.average(points,axis=0,weights=weights);local=mat[t].T@(cop-xyz[t]);f=row['rear_cop_centering']
  if f.get('override'):np.testing.assert_allclose(cop,f['cop_world'],rtol=0,atol=2e-6)
  contacts[t]=dict(step=t,local_cop_m=local.tolist(),euler_xyz_deg=euler[t].tolist(),normal_load_n=sum(weights),cop_xy_edge_margin_m=(half[:2]-abs(local[:2])).tolist(),physical_contact_points=len(points),reference_xy_lead_from_cop_m=(np.asarray(row['target_xyz'][:2])-cop[:2]).tolist(),rear_joint_xy_override=bool(row['rear_joint_xy_progress'].get('override')))
 bouts=[]
 for b in case['bouts']:
  ts=[t for t in range(b['start'],b['last']+1) if t in contacts];assert ts
  cc=[contacts[t] for t in ts];bouts.append(dict(start=b['start'],last=b['last'],frames=b['frames'],progress_mm=b['measured_progress_mm'],first_valid=cc[0],last_valid=cc[-1],mean_normal_n=float(np.mean([c['normal_load_n'] for c in cc])),min_xy_edge_margin_m=float(min(min(c['cop_xy_edge_margin_m']) for c in cc)),valid_prior_packet_frames=len(ts),joint_xy_override_frames=sum(c['rear_joint_xy_override'] for c in cc)))
 results.append(dict(run=case['run'],bouts=bouts))
 for name in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']:sources[str(ep/name)]=sha(ep/name)
sources[str(Path(__file__))]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=results,source_sha256=sources,training_ready=False)
with (R/'REAR_BOX_BOUT_CONTACT_GEOMETRY.json').open('x') as f:json.dump(out,f,indent=2)
for r in results:
 print(r['run'])
 for b in r['bouts']:
  print(b['start'],b['frames'],round(b['progress_mm'],2),'yaw',[round(b[k]['euler_xyz_deg'][2],2) for k in ['first_valid','last_valid']],'cop_y_mm',[round(1000*b[k]['local_cop_m'][1],2) for k in ['first_valid','last_valid']],'minmargin',round(b['min_xy_edge_margin_m']*1000,2),'joint_xy_frames',b['joint_xy_override_frames'])
