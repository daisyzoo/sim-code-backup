"""Full frozen configuration and actual premature-preflight rejection, no physics."""
from pathlib import Path
import sys,json,hashlib,datetime
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'rear_trailing_physical_preparation_r1';D=W/'rear_trailing_contact_preparation_r1';sys.path[:0]=[str(W),str(ROOT)]
from run_rear_trailing_trial1_physical_r1 import configuration,preflight,parent_readiness,earlier_trial_readiness,identity
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();plan,config=configuration();assert config['passed'] and config['conditions']==10 and config['expected_audits']==224
parent=parent_readiness();priority=earlier_trial_readiness();assert not parent['ready'] and not priority['ready']
rejected=False
try:preflight()
except AssertionError as e:
 assert e.args and isinstance(e.args[0],dict) and e.args[0]['ready'] is False and 'parent_collection_incomplete' in e.args[0]['pending'];rejected=True
assert rejected and not (W/'rear_trailing_physical_r1').exists() and not (P/'LAUNCH_PREFLIGHT.json').exists()
p=Path('/proc/98251');state=(p/'stat').read_text().split(') ',1)[1].split();assert state[19]=='93420759' and state[0]!='Z'
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,conditions=10,expected_audits=224,frozen_sources=len(config['source_sha256']),parent_inflight_preflight_rejected=True,existing_reserve_priority_pending=priority,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'CONFIGURATION_CHECK.json',P/'PLAN.json',P/'LAUNCHER_STRUCTURE_CHECK.json',P/'LAUNCHER_CLOSURE_PREPARATION.json',P/'REVIEW_ROUTING_CHECK.json',W/'run_rear_trailing_trial1_physical_r1.py',W/'close_rear_trailing_trial1_physical_v1.py',W/'summarize_rear_trailing_trial1_actual_reviews.py',D/'NATIVE_FRONT_840023_V3_CHECK.json']},new_physics_started=False,training_ready=False)
with (P/'ORCHESTRATION_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,frozen_sources=len(config['source_sha256']),parent_inflight_preflight_rejected=True,earlier_reserve_has_priority=True,physical_started=False)))
