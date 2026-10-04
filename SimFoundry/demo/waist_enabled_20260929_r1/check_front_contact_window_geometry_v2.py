"""V2 eligibility and all eight original quarter front-bag loss-boundary records.
No dynamic claim; current support point eligibility is not whole-hand clearance.
"""
from pathlib import Path
import sys,json,hashlib,datetime
W=Path(__file__).resolve().parent;C=W/'front_contact_window_candidate_v1';sys.path.insert(0,str(C))
from contact_window_evidence_v2 import loss_counter_observation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());report=read(C/'RECORDED_INTERVAL_EVIDENCE_CHECK_V4.json');old=read(C/'READINESS_REVIEW_V1.json');assert report['passed'];negative=[];boundaries=[]
base=dict(enabled=True,selected_front=True,mode='top_push',action_step=10,after_action_step=9,vertical_load_n=[1.]*17+[0.]*7,instantaneous_load_n=0.)
for margin,expected in [(None,False),(-.001,False),(0.,False),(.009999,False),(.010,True),(.010001,True)]:
 r=loss_counter_observation(**base,current_support_core_margin_m=margin);assert r['additional_intermittent_evidence'] is expected;boundaries.append(dict(margin=margin,additional=expected))
for name,margin in [('nan',float('nan')),('infinite',float('inf')),('boolean',True),('text','0.02')]:
 try:loss_counter_observation(**base,current_support_core_margin_m=margin)
 except ValueError:negative.append(name)
 else:raise AssertionError(name)
q=next(r for r in report['episodes'] if r['episode']=='front_loaded_z_quarter_physical_r2/case_840023/layout_840023_nudge_mailer_to_bin');rows={r['step']:r for r in q['records']};events=[]
for t in [222,399,527,669,790,885,981,1098]:
 r=rows[t];interior=t in [790,885,981];assert r['phase_bound_to_native_pressure_trace'] and r['mode_at_pressure_update']=='top_push' and r['original_counter']==3
 assert r['candidate_counter']==(0 if interior else 3)
 assert r['additional_intermit'] is interior
 events.append({k:r[k] for k in ['step','mode_at_pressure_update','mode_after_update','current_support_core_margin_m','original_counter','candidate_counter','additional_intermit']})
paths=[Path(__file__),C/'contact_window_evidence_v2.py',C/'RECORDED_INTERVAL_EVIDENCE_CHECK_V4.json',C/'READINESS_REVIEW_V1.json'];result=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,events=events,geometry_boundary_checks=boundaries,negative_rejections=negative,prior_candidate_edge_delays=[527,669,1098],current_recorded_edge_delays=[],source_sha256={str(p):sha(p) for p in paths},native_base_v1_not_v2=True,native_front_route_verified=False,physics_verified=False,training_ready=False)
with (C/'GEOMETRY_ELIGIBILITY_CHECK_V2.json').open('x') as f:json.dump(result,f,indent=2)
readiness=dict(result,status='interior_eligible_observer_verified_native_v2_unwired',actual_episodes=12,actual_intervals=14388,candidate_source='contact_window_evidence_v2.py',do_not_promote_prior_native_base='top_contact_window.py uses unbounded-v1 evidence and is retained only as prior phase/pressure test; it must be versioned with geometry source binding before native front integration.',remaining=['Build native V2 with current geometry bound to the same update; preserve interval ownership through bypass/guard exits.','Actual FrontCopRoute construction and source/audit metadata wiring; disabled full native identity and enabled own-history phase/command replay.','Original native IK/final guards and fresh complete paired physics; all existing task/control/visual reviews unchanged.'])
with (C/'READINESS_REVIEW_V2.json').open('x') as f:json.dump(readiness,f,indent=2)
print(json.dumps(dict(passed=True,edge_events_preserved=5,intermittent_events_detected=3,boundaries=len(boundaries),negative_rejections=len(negative))))
