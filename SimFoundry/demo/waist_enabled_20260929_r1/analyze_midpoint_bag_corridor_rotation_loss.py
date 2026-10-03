"""Decompose actual bag corridor loss, without modifying any control or quality gate.
Uses saved pre-action positions and orientations, independently transformed 3D
shell corners, and exact source-bound current records. Counterfactual fixed
orientation is geometric only: no dynamics or executable-route assertion.
"""
from pathlib import Path
import hashlib,json,datetime,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'front_corridor_midpoint_physical_r1';ep=R/'case_840023/layout_840023_nudge_mailer_to_bin'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
log=json.loads((ep/'frontal_bypass.json').read_text());rows=log['rows'];plan=log['plan'];assert len(rows)==1199
with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in ['box','mailer']}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in ['box','mailer']}
assert all(len(v)==1200 for v in [*tr.values(),*ori.values()])
sys.path.insert(0,str(W));from audit_front_corridor_midpoint_observations import inspect
route=inspect(rows,plan,tr,ori,enabled=True,expected_steps=range(1,1200));assert route['passed']
sgn=np.array([[i,j,k] for i in [-1,1] for j in [-1,1] for k in [-1,1]])
def geometry(key,t):
 size=np.array([.15,.145,.04] if key=='mailer' else [.14,.09,.045]);rot=Rotation.from_quat(ori[key][t]);corners=(sgn*size/2)@rot.as_matrix().T
 return np.max(np.abs(corners),axis=0),float(rot.as_euler('xyz',degrees=True)[2])
first=next(r['step'] for r in rows if r['mode']=='front_guard_lift');outrows=[]
r0,yaw0=geometry('mailer',1);o0,_=geometry('box',1);x0=tr['box'][1,0];initial_width=float(x0-o0[0]-2*r0[0]-.012-.285)
for row in rows:
 t=row['step'];rad,yaw=geometry('mailer',t);other,oyaw=geometry('box',t);tc=tr['mailer'][t];oc=tr['box'][t];rec=row['front_corridor_midpoint'];lo=.285+rad[0];hi=oc[0]-other[0]-rad[0]-.012;width=hi-lo
 np.testing.assert_allclose(row['observed_target'],tc,rtol=0,atol=1e-12)
 np.testing.assert_allclose(rec['target_radii_xy'],rad[:2],rtol=0,atol=1e-12);np.testing.assert_allclose(rec['other_radii_xy'],other[:2],rtol=0,atol=1e-12)
 np.testing.assert_allclose(rec['safe_interval_x'],[lo,hi],rtol=0,atol=1e-12)
 delta_other_x=float(oc[0]-x0);delta_other_radius=float(-(other[0]-o0[0]));delta_target_radius=float(-2*(rad[0]-r0[0]));np.testing.assert_allclose(width,initial_width+delta_other_x+delta_other_radius+delta_target_radius,rtol=0,atol=1e-12)
 margin=float(min(tc[0]-rad[0]-.28,.88-tc[0]-rad[0],tc[1]-rad[1]+.75,.75-tc[1]-rad[1]));gaps=[float(oc[0]-tc[0]-other[0]-rad[0]),float(abs(oc[1]-tc[1])-other[1]-rad[1])]
 np.testing.assert_allclose(rec['current_table_margin_m'],margin,rtol=0,atol=1e-12)
 np.testing.assert_allclose(rec['current_parcel_axis_gap_m'],max(gaps),rtol=0,atol=1e-12)
 outrows.append(dict(step=t,mode=row['mode'],route_stage=row['route_stage'],changed=rec['changed'],target_center_xyz=tc.tolist(),other_center_xyz=oc.tolist(),target_yaw_deg=yaw,target_radius_x_m=float(rad[0]),other_radius_x_m=float(other[0]),safe_interval_x=[float(lo),float(hi)],safe_interval_width_m=float(width),current_table_margin_m=margin,current_gap_x_y_m=gaps,width_change_from_first_m=dict(other_translation_x=delta_other_x,other_rotation_radius=delta_other_radius,target_rotation_radius=delta_target_radius),fixed_initial_target_orientation_width_m=float(oc[0]-other[0]-2*r0[0]-.012-.285)))
assert first==553 and rows[first-1]['route_stop_reason']=='front_corridor_no_table_margin'
assert all(r['mode']=='front_guard_lift' for r in rows if r['step']>=first)
lookup={r['step']:r for r in outrows};selected=[lookup[t] for t in [1,166,172,173,309,552,553,1199]]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,full_observation_replay={k:v for k,v in route.items() if k!='goals'},first_guard_step=first,guard_frames=1200-first,first_width_m=initial_width,selected_frames=selected,first_nonpositive_interval_step=next(r['step'] for r in outrows if r['safe_interval_width_m']<=0),interpretation=['The unchanged non-target center does not cause interval loss: target orientation increases its X envelope, counted twice in corridor width.','Positive current table margin at first guard is not actual table penetration. The exhausted interval concerns completing passage at the obstacle Y position.','Positive Y separation at first guard is before passing the obstacle; it cannot prove a safe lateral continuation.','Fixed-initial-orientation width is an arithmetic counterfactual only. No orientation controller, alternate route or globally impossible placement is established.','Midpoint gain delays stop but complete task still fails; original stop remains latched.'],source_sha256={str(p):sha(p) for p in [Path(__file__),ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'raw.npz',ep/'FRONT_CORRIDOR_MIDPOINT_STAGE_NUMERIC_REVIEW.json',W/'audit_front_corridor_midpoint_observations.py',W/'audit_front_corridor_midpoint_record.py']},training_ready=False)
with (R/'BAG_CORRIDOR_ROTATION_LOSS_DIAGNOSTIC.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(first_guard=first,changed=len(route['changed_steps']),first=lookup[1],guard=lookup[first]),indent=2))
