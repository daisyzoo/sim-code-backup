"""Separate measured yaw/tilt contributions to front-bag corridor closure.
Rotation counterfactuals recompute geometry only; no object pose is changed in
simulation or data. Contact samples describe association, not integrated torque
or proof that a proposed correction can be executed.
"""
from pathlib import Path
import json,hashlib,datetime,sys
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import brentq
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};results=[]
for run in ['joint_transport_reserve_physical_r1','rear_trailing_physical_r1','front_corridor_lateral_physical_r1']:
 ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in fr['rows']};first=next(r for r in fr['rows'] if r.get('route_stop_reason'));t=first['step'];record=first['front_corridor_midpoint'];assert record['original_planning_margin_m']==.012 and record['original_table_margin_m']==.005
 with np.load(ep/'trace.npz') as z:xyz=z['mailer'].astype(float);other=z['box'].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:q=z['mailer'].astype(float);oq=z['box'].astype(float)
 rot=Rotation.from_quat(q).as_matrix();orot=Rotation.from_quat(oq).as_matrix();euler=Rotation.from_quat(q).as_euler('xyz');yaw=np.unwrap(euler[:,2]);size=np.array([.15,.145,.04]);osize=np.array([.14,.09,.045]);otherx=(np.abs(orot[t])@osize/2)[0];actual=euler[t];initial=euler[0]
 def width(R):rad=(np.abs(R)@size/2)[0];return float(other[t,0]-otherx-2*rad-.012-.285)
 actual_width=width(rot[t]);np.testing.assert_allclose(actual_width,record['safe_interval_x'][1]-record['safe_interval_x'][0],atol=1e-12,rtol=0)
 restored=Rotation.from_euler('xyz',[actual[0],actual[1],initial[2]]).as_matrix();untilted=Rotation.from_euler('xyz',[0.,0.,actual[2]]).as_matrix();initial_full=rot[0];delta=float(np.arctan2(np.sin(initial[2]-actual[2]),np.cos(initial[2]-actual[2])))
 def at(f):return width(Rotation.from_euler('xyz',[actual[0],actual[1],actual[2]+f*delta]).as_matrix())
 corrections={}
 for desired in [0.,.003]:
  if at(0)>=desired:f=0.
  elif at(1)>=desired:f=brentq(lambda v:at(v)-desired,0.,1.,xtol=1e-12)
  else:f=None
  corrections[str(desired)]=None if f is None else dict(correction_rad=float(f*delta),correction_deg=float(np.degrees(f*delta)),resulting_yaw_deg=float(np.degrees(actual[2]+f*delta)),width_m=at(f),geometry_only=True)
 packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];packet={r['after_action_step']:r for r in packets};measured=[];coperrors=[]
 for step,row in rows.items():
  if step>=t or row['mode']!='top_push':continue
  pkt=packet[step-1];np.testing.assert_allclose(pkt['post_action_pose']['mailer'],xyz[step],atol=2e-6,rtol=0);forces=[];points=[];loads=[]
  for c in pkt['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/mailer/' in s]
   if len(slots)!=1 or not any('left_wrist' in s for s in c['shapes']):continue
   force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[step,:,2])
   if load>.05:forces.append(force);points.append(c['position_world']);loads.append(load)
  if sum(loads)<.3:continue
  cop=rot[step].T@(np.average(points,axis=0,weights=loads)-xyz[step]);saved=row.get('cop_slip_following',{}).get('measured_cop_local')
  if saved is not None:np.testing.assert_allclose(cop,saved,atol=2e-6,rtol=0);coperrors.append(float(np.max(abs(cop-saved))))
  # The sign convention matches the archived observer's shape order and the
  # existing independently checked pressure-centroid analysis; table moments
  # and within-action force variation are not included in this last-tick sample.
  moment=sum(np.cross(np.asarray(p)-xyz[step],f)[2] for p,f in zip(points,forces));force=np.sum(forces,axis=0);measured.append(dict(step=step,yaw_deg=float(np.degrees(yaw[step])),previous_action_yaw_change_deg=float(np.degrees(yaw[step]-yaw[step-1])),cop_local_mm=(cop*1000).tolist(),last_tick_hand_force_on_bag_n=force.tolist(),last_tick_hand_moment_about_center_z_nm=float(moment),normal_load_n=sum(loads)))
 row=dict(run=run,first_guard_step=t,phase=first['route_stage'],actual_rpy_deg=np.degrees(actual).tolist(),initial_rpy_deg=np.degrees(initial).tolist(),width_actual_mm=1000*actual_width,width_restore_initial_yaw_only_mm=1000*width(restored),width_remove_tilt_only_mm=1000*width(untilted),width_restore_initial_full_rotation_mm=1000*width(initial_full),geometry_only_yaw_corrections=corrections,loaded_contact_rows=len(measured),cop_rows_verified=len(coperrors),maximum_cop_error_m=max(coperrors,default=0.),last_loaded_contact=None if not measured else measured[-1],contact_samples=measured)
 results.append(row)
 for n in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json','quality.json']:sources[str(ep/n)]=sha(ep/n)
 print(json.dumps({k:v for k,v in row.items() if k!='contact_samples'}),flush=True)
for p in [Path(__file__),W/'analyze_front_box_normal_and_cop_v1.py',ROOT/'simfoundry/data/solved_contact_trace.py']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=results,source_sha256=sources,limitations=['Counterfactual rotations are analytical only, not feasible actions or motion responses.','Last solver-tick hand force moments omit table moments, full substep integration and rolling/torsional contact components; no unique dynamical cause is claimed.','The3mm width is a descriptive planning-slack comparison, not a changed quality or admission gate.','One trial per version cannot attribute score differences causally to a flag.'],controller_changed=False,physical_started=False,training_ready=False)
with (W/'front_corridor_lateral_physical_r1/FRONT_BAG_CORRIDOR_YAW_ASSOCIATION.json').open('x') as f:json.dump(report,f,indent=2)
