"""Unissued lift proposals on actual late recovery contexts; no rollout.
Independent original geometry recheck at every sampled nominal/predicted point.
The fourth late window remains rejected under its original measured height gate.
"""
from pathlib import Path
import datetime,hashlib,json,sys,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';D=W/'inactive_hand_headroom_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from inactive_clearance_proposal import propose
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();R=W/'front_recontact_headroom_physical_r1';ep=R/'case_840023/layout_840023_nudge_mailer_to_bin';events=json.loads((ep/'front_recontact_center.json').read_text())['rows'];guard=ClearanceGuard(ROOT,S);audit=SelectionAudit(ROOT,S);records=[];neg=[]
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23];u=z['action'][:,12:23]
for t in [405,528,754]:
 e=next(v for v in events if v['step']==t);c=e['context'];s=c['scene'];np.testing.assert_array_equal(c['current'],q[t]);np.testing.assert_array_equal(c['previous_command'],u[t-1]);scene=RecontactScene(guard,s['side'],s['target_xyz'],s['target_quat'],s['core_size'],s['other_xyz'],s['other_quat'],s['other_size'])
 args=dict(enabled=True,selected=True,side='left',mode=c['parent_mode'],counter=c['recontacts'],guard_stop=c['guard_stop'],observed_load_n=c['observed_load_n'],filtered_load_n=c['filtered_load_n'],current=c['current'],previous_q=c['previous_q'],previous_command=c['previous_command'],decay=c['decay'],scene=scene)
 command,r=propose(**args)
 checked=[]
 if command is not None:
  assert r['applied'] and r['predicted_active_hold_error']<1e-7
  for name in ['nominal','predicted']:
   for x,stored in zip(r['sampled_paths'][name]['states'],r['sampled_paths'][name]['checks']):
    independent,_=audit.geometry(x,s);audit.compare_geometry(stored,independent);assert independent['accepted'];checked.append(independent)
   final,_=audit.geometry(r['command'] if name=='nominal' else r['predicted_q'],s);assert final['inactive_lowest_z_m']>=.8415-2e-7
  actual=np.asarray(r['command']);now=np.asarray(c['current']);prev=np.asarray(c['previous_command']);assert np.all(actual>=guard.lower-2e-7) and np.all(actual<=guard.upper+2e-7) and np.all(abs(actual-now)<=guard.limits+2e-7) and max(abs(actual-prev))<=.0550002
 elif t==754:assert r['reason']=='original_measured_geometry_rejected'
 records.append(dict(step=t,counter=c['recontacts'],proposal=r,independent_sampled_points=len(checked)));print(t,r['applied'],r['reason'],flush=True)
 if t==405:
  for label,changes in [('disabled',dict(enabled=False)),('other_task',dict(side='right')),('unselected',dict(selected=False)),('loaded',dict(observed_load_n=.1)),('filtered',dict(filtered_load_n=.051)),('parent_guard',dict(guard_stop=True)),('zero_counter',dict(counter=0)),('push_mode',dict(mode='top_push'))]:
   command,b=propose(**dict(args,**changes));assert command is None and not b['applied'];neg.append(label)
files=[Path(__file__),D/'inactive_clearance_proposal.py',ep/'raw.npz',ep/'front_recontact_center.json',R/'INACTIVE_ANCHOR_HEIGHT_DIAGNOSIS.json',S/'recontact_scene.py',S/'front_initial_center_plan.py',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_events.py']
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,negative_cases=neg,passed=True,source_sha256={str(p):sha(p) for p in files},collector_integrated=False,continuous_full_body_path_certified=False,actual_recovery_entry_verified=False,physical_started=False,training_ready=False)
with (D/'ACTUAL_CONTEXT_PROPOSAL_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(accepted_proposals=sum(v['proposal']['applied'] for v in records),total=len(records),negative_cases=len(neg),physical_started=False)))
