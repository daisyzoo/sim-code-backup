"""Measured loaded contact centroid versus virtual reference; read-only diagnosis."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from scipy.spatial.transform import Rotation

p=Path(sys.argv[1]);rows={r['step']:r for r in json.loads((p/'frontal_bypass.json').read_text())['rows']}
packets=json.loads((p/'solved_contact_forces.json').read_text())['rows'];ori=np.load(p/'parcel_orientation.npz')
key,actor,side=('box','parcel_box','right') if 'push_box' in p.name else ('mailer','mailer','left')
records=[]
for packet in packets:
    t=packet['after_action_step'];next_step=t+1
    if next_step not in rows or next_step>=len(ori[key]): continue
    row=rows[next_step]
    if row['mode']!='top_push':continue
    rotation=Rotation.from_quat(ori[key][next_step]).as_matrix();normal=rotation[:,2]
    position=np.array(packet['post_action_pose'][key]);points=[];weights=[];force=np.zeros(3)
    for c in packet['parcel_contacts']:
        slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
        if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']): continue
        f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);force+=f
        weight=-float(f@normal)
        if weight>.05:points.append(c['position_world']);weights.append(weight)
    if not weights:continue
    centroid=np.average(points,axis=0,weights=weights);tip=np.array(row['observed_support_xyz'])
    records.append(dict(after_action_step=t,controller_step=next_step,route_stage=row.get('route_stage'),normal_load_n=sum(weights),force_on_target_world_n=force.tolist(),contact_minus_target_xy_m=(centroid-position)[:2].tolist(),reference_minus_contact_xy_m=(tip-centroid)[:2].tolist(),pose_alignment_error_m=float(np.max(abs(position-np.array(row['observed_target']))))))
stats={}
for stage in sorted({r['route_stage'] or 'none' for r in records}):
    selected=[r for r in records if (r['route_stage'] or 'none')==stage]
    stats[stage]=dict(samples=len(selected))
    for field in ('normal_load_n','force_on_target_world_n','contact_minus_target_xy_m','reference_minus_contact_xy_m'):
        a=np.asarray([r[field] for r in selected]);stats[stage][field]={name:np.quantile(a,q,axis=0).tolist() for name,q in [('p10',.1),('median',.5),('p90',.9)]}
assert records,'No loaded top push samples'
out=dict(summary=stats,max_pose_alignment_error_m=max(r['pose_alignment_error_m'] for r in records),records=records,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),force_sha256=hashlib.sha256((p/'solved_contact_forces.json').read_bytes()).hexdigest(),scope='Last solved action contact packet matched to next pre-action controller pose and quaternion; final unmatched packet omitted. Downward normal-force-weighted centroid of recorded contacts, not all-substep contact patch or causal proof. Virtual reference explicitly distinguished.',training_ready=False)
(p/'LOADED_CONTACT_OFFSETS.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(summary=stats,max_pose_alignment_error_m=out['max_pose_alignment_error_m']),indent=2))
