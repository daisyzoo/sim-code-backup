"""Independent geometry of every recorded late recovery waiting context.
Explains actual eligibility gaps; no relaxed gate or new control trajectory.
"""
from pathlib import Path
import collections,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();r=W/'front_recontact_headroom_physical_r1';ep=r/'case_840023/layout_840023_nudge_mailer_to_bin';native=json.loads((r/'FIRST_BAG_RECOVERY_DIAGNOSIS.json').read_text());assert native['independent_native_stream']['passed'];a=SelectionAudit(ROOT,S);events=json.loads((ep/'front_recontact_center.json').read_text())['rows'];records=[]
for e in events:
 if not e.get('reason','').startswith('waiting_for_'):continue
 c=e['context'];g,_=a.geometry(c['current'],c['scene']);fail=[]
 if g['active_above_top_m']<.004:fail.append('active_below_original4mm_unloaded_clearance')
 if min(g['hand_parcel_gaps_m'].values())<.01:fail.append('original_other_parcel_gap')
 if g['elbow_gap_m']<.005-2e-7:fail.append('original_elbow_gap')
 if g['inactive_lowest_z_m']<.84-2e-7:fail.append('inactive_below_original840mm')
 if not g['physical_bounds']:fail.append('original_joint_bounds')
 assert bool(fail) is (not g['accepted'])
 if g['accepted'] and g['inactive_lowest_z_m']<.841:fail.append('inactive_below_entry841mm')
 assert fail
 records.append(dict(step=e['step'],counter=e['real_recontact_index'],parent_mode=c['parent_mode'],reason=e['reason'],inactive_z_mm=g['inactive_lowest_z_m']*1000,active_clearance_mm=g['active_above_top_m']*1000,failed_predicates=fail))
summaries=[]
for counter in sorted({x['counter'] for x in records}):
 rr=[x for x in records if x['counter']==counter];good=[x for x in rr if x['failed_predicates']==['inactive_below_entry841mm']]
 summaries.append(dict(counter=counter,waiting_frames=len(rr),predicate_counts=dict(collections.Counter(k for x in rr for k in x['failed_predicates'])),otherwise_eligible_height_range_mm=[min(x['inactive_z_mm'] for x in good),max(x['inactive_z_mm'] for x in good)] if good else None,otherwise_eligible_steps=[x['step'] for x in good],last_wait=rr[-1]))
files=[Path(__file__),r/'FIRST_BAG_RECOVERY_DIAGNOSIS.json',ep/'front_recontact_center.json',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_events.py'];out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summaries=summaries,records=records,source_sha256={str(p):sha(p) for p in files},original_gates_unchanged=True,training_ready=False)
with (r/'LATE_RECOVERY_WINDOW_DIAGNOSIS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(summaries,indent=2))
