"""Compare observed hand/object motion during every push bout and lost-load exit.
The data can establish sliding/separation, but cannot prove a force-controller
counterfactual. All thresholds, raw data and controller files stay unchanged.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();fr=json.loads((p/'frontal_bypass.json').read_text());key='box' if fr['plan']['direction']==-1 else 'mailer';direction=fr['plan']['direction'];rows=fr['rows'];by={r['step']:r for r in rows};core=np.asarray(fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']);mom=json.loads((p/'FRONT_INITIAL_CONTACT_MOMENT_DIAGNOSTIC.json').read_text());mr={r['step']:r for r in mom['rows']}
with np.load(p/'trace.npz') as z:xyz=z[key].copy()
with np.load(p/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
starts=[];current=[]
for r in rows:
 if r['mode']=='top_push':current.append(r)
 elif current:starts.append((current,r));current=[]
if current:starts.append((current,None))
records=[]
for bout,exit_row in starts:
 a=bout[0];b=bout[-1];t0=a['step'];t1=b['step'];loaded=[mr[r['step']]['cop'] for r in bout if mr[r['step']]['cop'] is not None];samples=[]
 for r in [a,b]:
  t=r['step'];point=np.asarray(r['observed_physical_support_xyz']);local=rot[t].T@(point-xyz[t]);load=r['contact_load'];samples.append(dict(step=t,physical_support_object_local_m=local.tolist(),physical_support_min_xy_core_margin_mm=float(min(core[:2]/2-abs(local[:2]))*1000),observed_load_N=load['observed_vertical_load_n'],filtered_load_N=load['filtered_vertical_load_n'],z_bias_mm=load['applied_z_bias_m']*1000,desired_z_below_actual_support_mm=float((r['observed_support_xyz'][2]-r['target_xyz'][2])*1000)))
 x0=np.asarray(a['observed_support_xyz'])[:2];x1=np.asarray(b['observed_support_xyz'])[:2];relative=(x1-x0)-(xyz[t1,:2]-xyz[t0,:2]);bias=np.array([r['contact_load']['applied_z_bias_m'] for r in bout]);load=np.array([r['contact_load']['observed_vertical_load_n'] for r in bout]);errors=np.array([(r['observed_support_xyz'][2]-r['target_xyz'][2])*1000 for r in bout])
 records.append(dict(start=t0,end=t1,push_frames=len(bout),exit_reason=exit_row.get('last_recontact_reason') if exit_row else 'episode_end',observed_support_xy_travel_mm=float(np.linalg.norm(x1-x0)*1000),object_xy_travel_mm=float(np.linalg.norm(xyz[t1,:2]-xyz[t0,:2])*1000),hand_minus_object_xy_change_mm=(relative*1000).tolist(),relative_slide_norm_mm=float(np.linalg.norm(relative)*1000),object_signed_y_progress_mm=float(direction*(xyz[t1,1]-xyz[t0,1])*1000),median_load_N=float(np.median(load)),minimum_load_N=float(load.min()),bias_at_negative_limit_frames=int(np.sum(abs(bias+.006)<1e-10)),median_desired_z_below_actual_support_mm=float(np.median(errors)),first_cop_radius_mm=loaded[0]['xy_radius_mm'] if loaded else None,last_cop_radius_mm=loaded[-1]['xy_radius_mm'] if loaded else None,samples=samples))
source={str(p/name):sha(p/name) for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','FRONT_INITIAL_CONTACT_MOMENT_DIAGNOSTIC.json']};source[str(Path(__file__))]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episode=p.name,scope=__doc__,bouts=records,total_lost_contact_exits=sum(r['exit_reason']=='lost_contact' for r in records),guard_frames=sum(r['mode']=='front_guard_lift' for r in rows),source_sha256=source,training_ready=False,next_hypotheses=['Limit forward relative hand/object slip using the verified current contact reference, preserving original pressure and safety guards; replay declared behavior before new physics.','Check whether existing normal-load control can recover sufficient sustained contact under bounded lateral advance; holding XY alone may only create a new stall.','If normal pressure still saturates, inspect measured joint-target residual before proposing independently verified load compensation; do not relax original force/geometry/quality gates.'])
dest=p/'FRONT_INITIAL_LOST_LOAD_DIAGNOSTIC.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps(dict(lost_contact_exits=out['total_lost_contact_exits'],guard_frames=out['guard_frames'],first_bout=records[0]),indent=2))
