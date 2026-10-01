"""Compare synthetic recovery durations at their original recorded step indices
with the frozen physical protocol budget. No remapping, extended task budget,
physical success claim or training admission. New rollouts may follow different
states, so this is a concrete timing risk, not a measured new-policy outcome.
"""
from pathlib import Path
import json,hashlib
w=Path(__file__).resolve().parent;fixture=w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json';protocol=w/'rear_short_recovery_groups_r1/PROTOCOL.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();data=json.loads(fixture.read_text());p=json.loads(protocol.read_text());rows=[]
for case in data['rows']:
 cid=int(case['episode'].split('_')[1]);command=next(c for c in p['commands'] if c['layout_id']==cid and not c['wait']);args=command['args'];budget=int(args[args.index('--steps')+1]);assert budget==1200
 for plant in case['plants']:
  trace=plant['trace'];assert trace[-1]['kind']=='handover';assert [e['context']['step'] for e in trace]==list(range(case['step'],case['step']+len(trace)));assert len(trace)==plant['summary']['iterations'];finish=trace[-1]['context']['step']
  rows.append(dict(episode=case['episode'],start=case['step'],plant=plant['summary']['plant'],events=len(trace),handover_step=finish,original_budget_frames=budget,remaining_frames_at_start=budget-case['step'],within_original_budget=finish<budget,overrun_frames=max(0,finish-(budget-1))))
out=dict(scope=__doc__,rows=rows,within_budget=sum(r['within_original_budget'] for r in rows),outside_budget=sum(not r['within_original_budget'] for r in rows),maximum_overrun_frames=max(r['overrun_frames'] for r in rows),source_sha256={str(f):sha(f) for f in [Path(__file__),fixture,protocol]},physical_validation=False,training_ready=False)
(w/'RECONTACT_ORIGINAL_BUDGET_SCREEN.json').write_text(json.dumps(out,indent=2));print(out['within_budget'],out['outside_budget'],out['maximum_overrun_frames'])
