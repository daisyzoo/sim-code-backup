"""Read completed physics only: activation coverage, phase cost and pre-intervention divergence."""
from pathlib import Path
import json,hashlib,collections,datetime
import numpy as np
w=Path(__file__).resolve().parent;r=w/'minimum_motion_groups_r1';name='layout_840001_push_box_to_bin';ep=r/'case_840001'/name;old=w/'parent_seed_groups_r1/case_840001'/name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
events=json.loads((ep/'recontact_pose.json').read_text())['rows'];fr={x['step']:x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows']};plans=[e for e in events if e.get('planning')]
axis=np.asarray(plans[0]['planning']['minimum_motion_pose']['thin_axis_local']);blocked=[e for e in events if e.get('reason')=='initial_hand_below_unloaded_planning_height']
# Original runtime record explicitly names this guard; no relaxed bound or replay assertion.
blocked_groups=[]
for rec in sorted(set(e['context']['recontacts'] for e in blocked)):
 es=[e for e in blocked if e['context']['recontacts']==rec];ts=[e['step'] for e in es]
 blocked_groups.append(dict(recontacts=rec,frames=len(es),first_step=min(ts),last_step=max(ts),parent_modes=dict(collections.Counter(e['context']['parent_mode'] for e in es)),observed_support_z_range_m=[min(fr[t]['observed_support_xyz'][2] for t in ts),max(fr[t]['observed_support_xyz'][2] for t in ts)],observed_load_n_range=[min(e['context']['observed_load_n'] for e in es),max(e['context']['observed_load_n'] for e in es)]))
handover=[]
for e in events:
 if e['kind']!='handover':continue
 ctx=e['context'];R=np.asarray(ctx['observed_hand_pose'])[:3,:3]
 handover.append(dict(step=e['step'],ticks=e['ticks'],thin_axis_world_z_abs=float(abs((R@axis)[2])),selected_surface_local_xy=e['selected_surface_local_xy']))
divergence={}
with np.load(old/'raw.npz') as a,np.load(ep/'raw.npz') as b:
 for key in ['q','action']:
  d=np.max(abs(a[key]-b[key]),axis=1)
  divergence[key]=dict(first_any_difference=int(np.flatnonzero(d>0)[0]),first_over_1e6=int(np.flatnonzero(d>1e-6)[0]),max_abs_before_first_new_plan=float(max(d[:plans[0]['step']])))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episode=name,event_reason_counts=dict(collections.Counter(e.get('reason','active') for e in events)),actual_new_plan_steps=[e['step'] for e in plans],nominal_waypoints=[len(e['planning']['waypoints']) for e in plans],actual_handover=handover,blocked_groups=blocked_groups,pre_intervention_divergence=divergence,source_sha256={str(p):sha(p) for p in [Path(__file__),ep/'raw.npz',old/'raw.npz',ep/'frontal_bypass.json',ep/'recontact_pose.json']},interpretation='Only2 actual new paths.252 eligible frames skipped by original minimum hand height; path-count reduction does not establish fewer recovery cycles. Loaded push increased net progress but tilt recovery still dominant. Pre-plan divergence prevents attributing total progress change to new planner alone.',training_ready=False)
(r/'ACTIVATION_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','blocked_groups']},indent=2));print('blocked recovery groups',len(blocked_groups))
