"""Actual new front-bag recovery failure; compare recorded prefix, never predict success."""
from pathlib import Path
import sys,json,datetime,hashlib,collections
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';R=W/'front_inactive_clearance_physical_r1';E=R/'case_840023/layout_840023_nudge_mailer_to_bin';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_recontact_center_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());audit=RecoveryEventAudit(ROOT,S);events=read(E/'front_recontact_center.json')['rows'];fr=read(E/'frontal_bypass.json')['rows'];packets={r['after_action_step']:r for r in read(E/'solved_contact_forces.json')['rows']}
with np.load(E/'raw.npz') as z:q=z['q'][:,12:23].copy()
rows=[]
for r in events:
 if r['real_recontact_index']!=2 or r.get('reason')!='waiting_for_original_unloaded_geometry':continue
 c=r['context'];t=r['step'];np.testing.assert_array_equal(c['current'],q[t]);force=sum(abs(float(v['force_world_N'][2])) for v in packets[t-1]['parcel_contacts'] if any('left_wrist_roll' in s for s in v['shapes']) and any('/mailer/' in s for s in v['shapes']));assert force==c['observed_load_n']==0 and 0<=c['filtered_load_n']<=.05
 g,_=audit.geometry(q[t],c['scene']);assert not g['accepted'];reasons=[]
 if g['active_above_top_m']<.004:reasons.append('active_hand_below_original_4mm_precontact_clearance')
 if g['inactive_lowest_z_m']<.84-2e-7:reasons.append('inactive_hand_below_original_840mm')
 if g['elbow_gap_m']<.005-2e-7:reasons.append('elbow_gap_below_original5mm')
 if min(g['hand_parcel_gaps_m'].values())<.01:reasons.append('hand_parcel_gap_below_original10mm')
 if not g['physical_bounds']:reasons.append('physical_joint_bounds')
 assert reasons;rows.append(dict(step=t,reasons=reasons,independent_geometry=g))
stop=next(r for r in fr if r.get('route_stop_reason'));interval=stop['front_corridor_midpoint']['safe_interval_x'];assert interval[1]<interval[0]
summary=read(E/'quality.json');parent=W/'front_recontact_headroom_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin/quality.json';parentq=read(parent)
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,new_progress_mm=summary['metrics']['target_final_progress_m']*1000,parent_progress_mm=parentq['metrics']['target_final_progress_m']*1000,non_target_max_xy_mm=summary['metrics']['box_max_xy_m']*1000,preparations=[dict(step=r['step'],counter=r['real_recontact_index'],ticks=r['ticks']) for r in events if r.get('phase')=='inactive_clearance_preparation'],handovers=[dict(step=r['step'],counter=r['real_recontact_index']) for r in events if r['kind']=='handover'],original_unloaded_geometry_rejections=rows,rejection_counts=dict(collections.Counter(k for r in rows for k in r['reasons'])),first_parent_stop=dict(step=stop['step'],reason=stop['route_stop_reason'],safe_interval_width_mm=(interval[1]-interval[0])*1000,original_midpoint_record=stop['front_corridor_midpoint']),interpretation='Preparation and one actual capture occurred; later recovery lacks original unloaded geometry and parent corridor interval becomes empty. Finishing an unloaded center path alone does not prove sustained contact. Single rollout comparison does not isolate deterministic causal effect; no gate relaxation or training admission.',source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_recontact_center_events.py',E/'raw.npz',E/'quality.json',E/'front_recontact_center.json',E/'frontal_bypass.json',E/'solved_contact_forces.json',parent]},training_ready=False)
with (R/'FIRST_BAG_CLEARANCE_DIAGNOSIS.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:result[k] for k in ['new_progress_mm','parent_progress_mm','preparations','handovers','rejection_counts','non_target_max_xy_mm']}))
