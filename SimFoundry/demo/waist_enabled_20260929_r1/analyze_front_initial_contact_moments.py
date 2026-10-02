"""Read-only observed COP and instantaneous yaw moments for front-route pushes.
Uses the last solved tick of each previous control step, not all24 substeps.
These samples are neither integrated impulses nor proof of causal yaw dynamics.
No controller, threshold, or dataset admission is changed.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
EP=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
fr=json.loads((EP/'frontal_bypass.json').read_text());plan=fr['plan'];assert plan['front_route_selected'];key='box' if plan['direction']==-1 else 'mailer';actor='parcel_box' if key=='box' else 'mailer';side='right' if key=='box' else 'left'
packets=json.loads((EP/'solved_contact_forces.json').read_text());assert 'last physics tick' in packets['sampling'];pk={r['after_action_step']:r for r in packets['rows']};assert len(pk)==len(packets['rows'])
with np.load(EP/'trace.npz') as z:xyz=z[key].copy()
with np.load(EP/'parcel_orientation.npz') as z:quat=z[key].copy()
rot=Rotation.from_quat(quat).as_matrix();yaw=np.rad2deg(np.unwrap(Rotation.from_quat(quat).as_euler('xyz')[:,2]));core=np.asarray(plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']);rows=[]
for row in fr['rows']:
 if row['mode']!='top_push':continue
 t=row['step'];packet=pk[t-1];np.testing.assert_allclose(packet['post_action_pose'][key],xyz[t],rtol=0,atol=1e-8)
 groups={};points=[];weights=[]
 for contact in packet['parcel_contacts']:
  slots=[i for i,label in enumerate(contact['shapes']) if '/'+actor+'/' in label]
  if not slots:continue
  assert len(slots)==1;slot=slots[0];sgn=1 if slot==1 else -1;other=contact['shapes'][1-slot]
  group='active_hand' if side+'_wrist' in other else ('table' if '/table/' in other else 'other')
  force=sgn*np.asarray(contact['force_world_N'],float);matrix=np.asarray(contact['contact_frame'],float);wrench=sgn*np.asarray(contact['force_torque_contact'],float);np.testing.assert_allclose(wrench[:3]@matrix,force,rtol=1e-6,atol=1e-5)
  offset=np.asarray(contact['position_world'])-xyz[t];moment=np.cross(offset,force)+(wrench[3:]@matrix);assert np.isfinite(moment).all()
  g=groups.setdefault(group,dict(contacts=0,force_world_N=np.zeros(3),moment_world_Nm=np.zeros(3)));g['contacts']+=1;g['force_world_N']+=force;g['moment_world_Nm']+=moment
  normal=-float(force@rot[t,:,2])
  if group=='active_hand' and normal>.05:points.append(contact['position_world']);weights.append(normal)
 cop=None;logged=row.get('cop_slip_following',{});checked=False
 if sum(weights)>=.3:
  world=np.average(points,axis=0,weights=weights);local=rot[t].T@(world-xyz[t]);cop=dict(local_m=local.tolist(),normal_load_N=float(sum(weights)),xy_radius_mm=float(np.linalg.norm(local[:2])*1000),xy_fraction_of_half_core=(abs(local[:2])/(core[:2]/2)).tolist())
  if logged.get('override'):
   np.testing.assert_allclose(logged['measured_cop_local'],local,rtol=0,atol=2e-6);checked=True
 elif logged.get('override'):raise AssertionError('Logged COP override without independently reconstructed load')
 rows.append(dict(step=t,target_yaw_deg=float(yaw[t]),yaw_change_from_initial_deg=float(yaw[t]-yaw[0]),next_observation_yaw_change_deg=float(yaw[t+1]-yaw[t]) if t+1<len(yaw) else None,cop=cop,cop_log_verified=checked,moments={k:dict(contacts=v['contacts'],force_world_N=v['force_world_N'].tolist(),moment_world_Nm=v['moment_world_Nm'].tolist()) for k,v in groups.items()}))
loaded=[r for r in rows if r['cop'] is not None];assert loaded
summary=dict(push_rows=len(rows),loaded_cop_rows=len(loaded),cop_logs_verified=sum(r['cop_log_verified'] for r in rows),median_cop_radius_mm=float(np.median([r['cop']['xy_radius_mm'] for r in loaded])),max_cop_radius_mm=max(r['cop']['xy_radius_mm'] for r in loaded),max_abs_active_hand_yaw_moment_Nm=max(abs(r['moments'].get('active_hand',{}).get('moment_world_Nm',[0,0,0])[2]) for r in rows),first_loaded=loaded[0],last_loaded=loaded[-1])
source={str(EP/name):sha(EP/name) for name in ['trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']};source[str(Path(__file__))]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=EP.name,core_size_xyz=core.tolist(),sampling=packets['sampling'],summary=summary,rows=rows,source_sha256=source,training_ready=False)
dest=EP/'FRONT_INITIAL_CONTACT_MOMENT_DIAGNOSTIC.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['first_loaded','last_loaded']},indent=2))
