"""Read-only launch/route validation. No physics or GPU reservation."""
from pathlib import Path
import sys,json,hashlib,datetime,ast,copy
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'joint_transport_reserve_physical_preparation_r1';sys.path[:0]=[str(W),str(ROOT)]
from run_joint_transport_reserve_trial1_physical_r1 import configuration,parent_readiness,preflight
from watch_joint_transport_reserve_trial1_numeric_reviews_r1 import check,selection
from joint_transport_reserve_r2_v4_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan,config=configuration();routing=check();assert routing['passed'];readiness=parent_readiness()
# With a currently verified-live parent and incomplete data, preflight must reject before GPU launch.
assert readiness['ready'] is False and 'parent_collection_incomplete' in readiness['pending']
try:preflight()
except AssertionError as e:assert 'parent_collection_incomplete' in str(e)
else:raise AssertionError('In-flight parent was accepted')
# Preserve all parent math checks and route short failures to candidate-source reviewer.
short=W/'review_joint_transport_reserve_trial1_incomplete_episode.py';tree=ast.parse(short.read_text());imports=[n.module for n in tree.body if isinstance(n,ast.ImportFrom)];assert 'joint_transport_reserve_stage_source_binding_v2' in imports and 'inactive_transport_stage_source_binding_v2' not in imports
source=(W/'watch_joint_transport_reserve_trial1_physical_audits_r1.py').read_text();assert 'joint_transport_j2_' not in source and 'run_joint_transport_reserve_trial1_physical_r1.py' in source
inventory=[]
for c in plan['commands']:
 for task in c['tasks']:
  ep=W/'front_box_recenter_physical_r2'/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"
  scripts=primary(c['wait'])+['audit_joint_transport_reserve_r2_v1_stage_contacts.py','audit_joint_transport_reserve_r2_v1_stage_pressure.py']
  if not c['wait']:scripts+=controls(json.loads((ep/'frontal_bypass.json').read_text())['plan'])+ADDITIONAL
  scripts+=['audit_joint_transport_reserve_r2_v1_stage_release.py'];scripts=list(dict.fromkeys(scripts));assert all(x in REPORTS for x in scripts);inventory.append(dict(episode=ep.name,scripts=scripts))
assert len(inventory)==10 and sum(len(r['scripts']) for r in inventory)==224
proof=json.loads((W/'joint_transport_reserve_preparation_r1/AUDIT_FAMILY_V2_IMPORT_CHECK.json').read_text());assert [r['scripts'] for r in inventory]==[r['scripts'] for r in proof['inventory']]
files=[Path(__file__),P/'CONFIGURATION_CHECK.json',W/'run_joint_transport_reserve_trial1_physical_r1.py',W/'watch_joint_transport_reserve_trial1_numeric_reviews_r1.py',W/'watch_joint_transport_reserve_trial1_physical_audits_r1.py',short,W/'review_joint_transport_reserve_trial1_v1_stage_episode.py']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,configuration_sources=len(config['source_sha256']),numeric_routing=routing,parent_readiness=readiness,parent_inflight_preflight_rejected=True,correct_short_source_binding=True,audit_conditions=10,audit_invocations=224,source_sha256={str(p):sha(p) for p in files},launch_ready=False,simulation_started=False,training_ready=False)
with (P/'ORCHESTRATION_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','numeric_routing','scope']},indent=2))
