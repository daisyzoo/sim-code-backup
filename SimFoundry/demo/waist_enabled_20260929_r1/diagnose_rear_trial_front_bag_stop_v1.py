"""Independent observed-envelope check at the first actual front-bag guard.
Compare selector phase coverage without altering actual observations or treating
an unissued command as a response. Original geometric margins unchanged.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));R=W/'rear_trailing_physical_r1';ep=R/'case_840023/layout_840023_nudge_mailer_to_bin'
from audit_front_corridor_lateral_record_v1 import verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();fr=json.loads((ep/'frontal_bypass.json').read_text());row=next(r for r in fr['rows'] if r.get('route_stop_reason'));assert row['step']==650 and row['route_stage']=='front_x';assert not next(r for r in fr['rows'] if r['step']==649).get('route_stop_reason')
with np.load(ep/'trace.npz') as z:target=z['mailer'][650];other=z['box'][650];initial=z['box'][0]
with np.load(ep/'parcel_orientation.npz') as z:quat=z['mailer'][650];oq=z['box'][650]
record=row['front_corridor_midpoint'];checks=[]
for flag in [False,True]:
 result=verify(record=record,original_goal_x=record['original_goal_x'],route_stage=row['route_stage'],target=target,obstacle=other,size=[.15,.145,.04],other_size=[.14,.09,.045],quat=quat,other_quat=oq,direction=1,planning_margin=.012,initial_other=initial,hand_obstacle_gap_m=row['hand_obstacle_gap_m'],parent_guard_reason=None,prior_stop_reason=None,lateral_y_enabled=flag);assert result['passed'] and not result['changed'];checks.append(dict(lateral_enabled=flag,**result))
width=1000*(record['safe_interval_x'][1]-record['safe_interval_x'][0]);assert width<0
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,first_guard_step=650,reason=row['route_stop_reason'],route_stage=row['route_stage'],independent_checks=checks,safe_interval_width_mm=width,actual_table_margin_mm=1000*record['current_table_margin_m'],actual_parcel_axis_gap_mm=1000*record['current_parcel_axis_gap_m'],findings=['No positive-width planned corridor at this observation under original margins.','The queued lateral-stage fix correctly does not bypass this front_x geometry rejection.','Reserve parent594 had positive0.940mm width in lateral_y; this is a distinct failure condition.','Rear-only preference cannot be credited with or blamed for left-bag score change from this one comparison.'],source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_corridor_lateral_record_v1.py',ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'REAR_TRAILING_R1_V1_STAGE_NUMERIC_REVIEW.json',ep/'ACTUAL_REVIEW_BINDING.json']},training_ready=False)
with (R/'FRONT_BAG_FIRST_GUARD_DIAGNOSIS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(step=650,width_mm=width,lateral_switch_correctly_preserves_stop=True)))
