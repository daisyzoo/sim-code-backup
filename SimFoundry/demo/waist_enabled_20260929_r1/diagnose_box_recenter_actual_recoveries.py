"""Actual right-box recovery execution and blockers, complete saved1200 frames.
Single-trial historical comparison, not a repeatability or full-audit claim.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_recenter_v3';R=W/'front_box_recenter_physical_r2';E=R/'case_840020/layout_840020_push_box_to_bin';P=W/'front_recontact_headroom_physical_r1/case_840020/layout_840020_push_box_to_bin';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_recontact_center_events import RecoveryEventAudit
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();audit=RecoveryEventAudit(ROOT,S);records=[];sources={}
for ep in [E,P]:
 events=read(ep/'front_recontact_center.json');fr=read(ep/'frontal_bypass.json')['rows'];quality=read(ep/'quality.json');load=[r.get('contact_load',{}).get('observed_vertical_load_n',0.) for r in fr];records.append(dict(run=ep.parent.parent.name,progress_mm=quality['metrics']['target_final_progress_m']*1000,quality_passed=quality['passed'],selected=events['selected'],event_kinds=dict(collections.Counter(r['kind'] for r in events['rows'])),reasons=dict(collections.Counter(str(r.get('reason')) for r in events['rows'])),handovers=[dict(step=r['step'],counter=r['real_recontact_index']) for r in events['rows'] if r['kind']=='handover'],modes=dict(collections.Counter(r['mode'] for r in fr)),observed_loaded_frames_over_0_3N=sum(v>=.3 for v in load),recovery_starts=[dict(step=r['step'],counter=r.get('recontacts'),reason=r.get('last_recontact_reason')) for i,r in enumerate(fr) if i and r.get('recontacts',0)>fr[i-1].get('recontacts',0)]))
 for p in [ep/'front_recontact_center.json',ep/'frontal_bypass.json',ep/'quality.json',ep/'raw.npz']:sources[str(p)]=sha(p)
with np.load(E/'raw.npz') as z:q=z['q'][:,12:23].copy()
packets={r['after_action_step']:r for r in read(E/'solved_contact_forces.json')['rows']};blocked=[]
for r in read(E/'front_recontact_center.json')['rows']:
 if r.get('reason')!='waiting_for_original_unloaded_geometry':continue
 c=r['context'];t=r['step'];np.testing.assert_array_equal(c['current'],q[t]);assert c['scene']['side']=='right';force=sum(abs(float(v['force_world_N'][2])) for v in packets[t-1]['parcel_contacts'] if any('right_wrist_roll' in s for s in v['shapes']) and any('/box/' in s for s in v['shapes']));assert abs(force-c['observed_load_n'])<1e-8 and force==0 and 0<=c['filtered_load_n']<=.05
 g,_=audit.geometry(q[t],c['scene']);assert not g['accepted'];reasons=[]
 if g['inactive_lowest_z_m']<.84-2e-7:reasons.append('inactive_left_below840mm')
 if g['active_above_top_m']<.004:reasons.append('active_below4mm_precontact_clearance')
 if min(g['hand_parcel_gaps_m'].values())<.01:reasons.append('hand_parcel_gap_below10mm')
 if g['elbow_gap_m']<.005-2e-7:reasons.append('elbow_gap_below5mm')
 if not g['physical_bounds']:reasons.append('joint_bounds')
 assert reasons;blocked.append(dict(step=t,counter=r['real_recontact_index'],reasons=reasons,geometry=g))
counts=dict(collections.Counter(x for r in blocked for x in r['reasons']));out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,comparisons=records,blocked_unloaded_contexts=blocked,rejection_counts=counts,interpretation='Actual new branch selected and one real handover occurred; loaded-frame count alone does not imply transport success. Original measured geometry prevents further takeover. Do not loosen original geometry gates; distinguish inactive clearance from active precontact clearance.',source_sha256={**sources,**{str(p):sha(p) for p in [Path(__file__),W/'audit_front_recontact_center_events.py',E/'solved_contact_forces.json']}},training_ready=False)
with (R/'BOX_RECENTER_ACTUAL_DIAGNOSIS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(comparisons=records,blocked=len(blocked),rejection_counts=counts)))
