"""Inverse-restore launcher/closure adapters and inspect live pending dependencies.
No configuration freeze, preflight approval, GPU launch or simulated success.
"""
from pathlib import Path
import sys,json,hashlib,datetime,re,ast
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'rear_trailing_physical_preparation_r1';sys.path[:0]=[str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((P/'LAUNCHER_CLOSURE_PREPARATION.json').read_text());inverse={v:k for k,v in prep['replacements'].items()};pattern=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))))
for r in prep['adapters']:
 path=Path(r['path']);assert sha(path)==r['sha256'] and sha(r['parent'])==r['parent_sha256'];s=path.read_text();ast.parse(s)
 for e in reversed(r['edits']):assert s.count(e['new'])==1;s=s.replace(e['new'],e['old'])
 assert pattern.sub(lambda m:inverse[m.group()],s)==Path(r['parent']).read_text()
import run_rear_trailing_trial1_physical_r1 as runner
assert ('NATIVE_FRONT_840023_V3_CHECK.json','passed') in runner.CHECKS
assert len(runner.CHECKS)==10
parent=runner.parent_readiness();earlier=runner.earlier_trial_readiness();assert not parent['ready'] and not earlier['ready']
assert not (W/'rear_trailing_physical_r1').exists()
# Native process identity is checked now, rather than trusting a saved status file.
actual=runner.identity(26226);prior=runner.identity(98251)
assert actual is not None and actual['start']=='92657106' and actual['state']!='Z'
assert prior is not None and prior['start']=='93420759' and prior['state']!='Z'
assert str(W/'run_joint_transport_trial1_physical_r1.py').encode() in actual['cmd']
assert str(W/'queue_joint_transport_reserve_trial1_physical_r2.py').encode() in prior['cmd']
files=[Path(__file__),P/'LAUNCHER_CLOSURE_PREPARATION.json',P/'PLAN.json',*[Path(r['path']) for r in prep['adapters']]]
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,inverse_restored_adapters=len(prep['adapters']),required_native_reports=runner.CHECKS,parent_pending=parent,earlier_trial_pending=earlier,live_processes=[dict(pid=26226,start=actual['start'],state=actual['state']),dict(pid=98251,start=prior['start'],state=prior['state'])],source_sha256={str(p):sha(p) for p in files},full_configuration_pending=True,physical_started=False,training_ready=False)
with (P/'LAUNCHER_STRUCTURE_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,adapters=3,required_native_reports=10,parent_pending=True,earlier_reserve_pending=True,physical_started=False)))
