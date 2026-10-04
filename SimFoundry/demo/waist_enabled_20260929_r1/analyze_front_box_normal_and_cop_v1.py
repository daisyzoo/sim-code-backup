"""Observed pre-exit normal-tracking error versus box tilt and pressure migration.
Read-only temporal association, not a hand-material slip or unique force-cause
claim. Independently recomputes normal residual angles and pressure centroids.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};results=[]
for run in ['front_box_recenter_physical_r2','joint_transport_physical_r1','joint_transport_reserve_physical_r1']:
 ep=W/run/'case_840020/layout_840020_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in fr['rows']};co={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];assert list(co)==list(range(1,1200)) and len(packets)==1200
 with np.load(ep/'trace.npz') as z:xyz=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box']).as_matrix()
 measured={};errors=[]
 for t,row in rows.items():
  if row['mode']!='top_push':continue
  normal=co[t]['contact_normal_tracking'];a=np.asarray(normal['current_local_up']);b=np.asarray(normal['target_local_up']);angle=float(np.arccos(np.clip(a@b/(np.linalg.norm(a)*np.linalg.norm(b)),-1,1)));assert abs(float(np.arccos(np.clip(a@b,-1,1)))-normal['angle_error_rad'])<2e-10;assert abs(np.linalg.norm(a)-1)<2e-6 and abs(np.linalg.norm(b)-1)<2e-6
  packet=packets[t-1];np.testing.assert_allclose(packet['post_action_pose']['box'],xyz[t],atol=2e-6,rtol=0);points=[];weights=[]
  for c in packet['parcel_contacts']:
   slots=[i for i,n in enumerate(c['shapes']) if '/parcel_box/' in n]
   if len(slots)!=1 or not any('right_wrist' in n for n in c['shapes']):continue
   force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
   if load>.05:points.append(c['position_world']);weights.append(load)
  cop=None
  if weights and sum(weights)>=.3:
   cop=rot[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]);saved=row['cop_slip_following'].get('measured_cop_local')
   if saved is not None:errors.append(float(np.max(abs(cop-np.asarray(saved)))));np.testing.assert_allclose(cop,saved,atol=2e-6,rtol=0)
  measured[t]=dict(step=t,normal_tracking_error_rad=angle,recorded_box_tilt_rad=row['observed_parcel_tilt_rad'],pressure_cop_local_mm=None if cop is None else (cop*1000).tolist(),load_n=sum(weights))
 bouts=[];start=None
 for t,row in rows.items():
  if row['mode']=='top_push':
   if start is None:start=t
  elif start is not None:
   rr=[measured[k] for k in range(start,t)];cc=[r for r in rr if r['pressure_cop_local_mm'] is not None];assert rr
   b=dict(start=start,last=t-1,exit_step=t,exit_reason=row.get('last_recontact_reason'),frames=len(rr),actual_target_progress_mm=float((xyz[start,1]-xyz[t,1])*1000),last_normal_error_rad=rr[-1]['normal_tracking_error_rad'],max_normal_error_rad=max(r['normal_tracking_error_rad'] for r in rr),last_box_tilt_rad=rr[-1]['recorded_box_tilt_rad'],exit_box_tilt_rad=row['observed_parcel_tilt_rad'],last_pressure_cop_local_y_mm=None if not cc else cc[-1]['pressure_cop_local_mm'][1],initial_pressure_cop_local_y_mm=None if not cc else cc[0]['pressure_cop_local_mm'][1],last_load_n=rr[-1]['load_n']);bouts.append(b);start=None
 tilt=[b for b in bouts if b['exit_reason']=='incipient_tilt_independent'];assert tilt
 summary=dict(run=run,tilt_exits=len(tilt),last_normal_error_median_rad=float(np.median([b['last_normal_error_rad'] for b in tilt])),last_normal_error_max_rad=max(b['last_normal_error_rad'] for b in tilt),tilt_exits_with_prior_normal_error_below_003=sum(b['last_normal_error_rad']<.03 for b in tilt),median_bout_progress_mm=float(np.median([b['actual_target_progress_mm'] for b in tilt])),median_last_cop_local_y_mm=float(np.median([b['last_pressure_cop_local_y_mm'] for b in tilt])),median_contact_frames=float(np.median([b['frames'] for b in tilt])),independent_cop_rows=len(errors),max_cop_reconstruction_error_m=max(errors))
 results.append(dict(summary=summary,bouts=bouts,rows=list(measured.values())))
 for n in ['raw.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz']:sources[str(ep/n)]=sha(ep/n)
 print(json.dumps(summary),flush=True)
sources[str(Path(__file__))]=sha(Path(__file__))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=results,source_sha256=sources,limitations=['Independent angle normalizes stored float vectors; recorded angle uses their unnormalized dot product and is checked separately.', 'Normal residual is parcel-normal expressed in hand coordinates versus the captured anchor, not independent world wrist orientation.','The .03rad comparison is descriptive and is not a new acceptance criterion.','Saved observation205 is a response to action204; pre-exit204 is a response to203. No action after tilt guard is treated as its cause.','Small residual cannot rule out contact geometry, pressure distribution, angular acceleration or tracking-force effects.'],next='Do not infer gross normal-tracking instability solely from tilt exits. Evaluate recovery landing preference separately from tangential relative-drive control, retaining original physical quality gates.',training_ready=False)
with (W/'joint_transport_reserve_physical_r1/FRONT_BOX_NORMAL_COP_ASSOCIATION.json').open('x') as f:json.dump(report,f,indent=2)
