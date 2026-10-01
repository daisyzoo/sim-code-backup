"""Read actual post-action contact wrenches; no controller or data mutation."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(sys.argv[1]).resolve();key,actor,side=('box','parcel_box','right') if 'push_box' in p.name else ('mailer','mailer','left')
rows={x['step']:x for x in json.loads((p/'frontal_bypass.json').read_text())['rows']};force_file=json.loads((p/'solved_contact_forces.json').read_text());trace=np.load(p/'trace.npz');ori=np.load(p/'parcel_orientation.npz');angles=np.unwrap(Rotation.from_quat(ori[key]).as_euler('xyz')[:,2]);records=[]
for packet in force_file['rows']:
 t=packet['after_action_step'];after=t+1;row=rows.get(t)
 if row is None or row['mode']!='top_push' or after>=len(angles):continue
 center=np.array(packet['post_action_pose'][key]);assert np.max(abs(center-trace[key][after]))<1e-5
 rot=Rotation.from_quat(ori[key][after]).as_matrix();groups={name:dict(force=np.zeros(3),moment=np.zeros(3),orbital=np.zeros(3),torsional=np.zeros(3),count=0) for name in ['active_hand','table','other']};points=[];weights=[]
 for c in packet['parcel_contacts']:
  slots=[i for i,x in enumerate(c['shapes']) if '/'+actor+'/' in x]
  if len(slots)!=1:continue
  slot=slots[0];sign=1 if slot==1 else -1;other=c['shapes'][1-slot];name='active_hand' if side+'_wrist' in other else 'table' if '/table/' in other else 'other'
  f=sign*np.array(c['force_world_N']);moment_arm=np.array(c['position_world'])-center;orbital=np.cross(moment_arm,f);torsional=sign*(np.array(c['force_torque_contact'])[3:]@np.array(c['contact_frame']));g=groups[name];g['force']+=f;g['orbital']+=orbital;g['torsional']+=torsional;g['moment']+=orbital+torsional;g['count']+=1
  weight=-float(f@rot[:,2])
  if name=='active_hand' and weight>.05:points.append(c['position_world']);weights.append(weight)
 if not weights:continue
 centroid=np.average(points,axis=0,weights=weights);data={name:{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in g.items()} for name,g in groups.items()};cop=rot.T@(centroid-center)
 records.append(dict(after_action_step=t,next_pre_action_frame=after,route_stage=row.get('route_stage'),yaw_rad=float(angles[after]),yaw_change_rad=float(angles[after]-angles[t]),normal_load_n=sum(weights),normal_weighted_contact_target_local_xyz_m=cop.tolist(),contact_minus_target_world_xyz_m=(centroid-center).tolist(),groups=data,net_contact_yaw_moment_Nm=float(sum(g['moment'][2] for g in groups.values())),pose_alignment_error_m=float(np.max(abs(center-trace[key][after])))))
assert records
stats={}
for stage in sorted({r['route_stage'] or 'none' for r in records}):
 rr=[r for r in records if (r['route_stage'] or 'none')==stage];stats[stage]=dict(samples=len(rr),first_action_step=rr[0]['after_action_step'],last_action_step=rr[-1]['after_action_step'],yaw_change_deg=float(np.degrees(angles[rr[-1]['next_pre_action_frame']]-angles[rr[0]['after_action_step']])),negative_hand_yaw_moment_samples=sum(r['groups']['active_hand']['moment'][2]<0 for r in rr),negative_yaw_change_samples=sum(r['yaw_change_rad']<0 for r in rr))
 for name,values in [('hand_yaw_moment_Nm',[r['groups']['active_hand']['moment'][2] for r in rr]),('table_yaw_moment_Nm',[r['groups']['table']['moment'][2] for r in rr]),('net_contact_yaw_moment_Nm',[r['net_contact_yaw_moment_Nm'] for r in rr]),('normal_weighted_contact_target_local_xyz_m',[r['normal_weighted_contact_target_local_xyz_m'] for r in rr]),('hand_force_world_N',[r['groups']['active_hand']['force'] for r in rr])]:stats[stage][name]={label:np.quantile(values,q,axis=0).tolist() for label,q in [('p10',.1),('median',.5),('p90',.9)]}
report=dict(summary=stats,records=records,source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']},auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Action t command mode matched to last solved physics contact packet after action t; exact recorded post-action target center matches next pre-action t+1. Signed force/torque on target uses body slot convention (force on second shape), includes lever cross force plus contact-frame rotational torque. Normal-force-weighted centroid of measured contacts, not hull-minimum surrogate. Frame-sampled last tick only, NOT integrated impulses/full-substep mechanics or causal intervention. Gravity has no yaw moment about center; omitted noncontact/body effects not reconstructed. No training admission.',training_ready=False)
(p/'SIGNED_CONTACT_MOMENTS.json').write_text(json.dumps(report,indent=2));print(json.dumps(stats,indent=2))
