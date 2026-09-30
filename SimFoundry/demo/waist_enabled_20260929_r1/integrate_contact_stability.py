"""Apply reviewed diagnostic candidate after previous complete-group audit."""
from pathlib import Path
import json,hashlib,shutil,datetime
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_contact_stability';run=root/'projected_hysteresis_mirror1200_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((stage/'MANIFEST.json').read_text())
assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert all(x['returncode']==0 for x in json.loads((run/'AUDIT_EXECUTION.json').read_text()))
assert len(json.loads((run/'COMPLETE_GROUP_READINESS.json').read_text())['errors'])==2
r=json.loads((run/'RESULT.json').read_text());assert all(x['actual_sampled_visual_review']=='completed' for x in r['rows'])
t=json.loads((stage/'TESTS.json').read_text());assert t['passed'] and t['tests_run']==98 and t['candidate_sha256']==m['candidate_sha256']
f=json.loads((stage/'FACTORY_CHECK.json').read_text());assert len(f['rows'])==32 and len(f['cli'])==7 and f['candidate_sha256']==m['candidate_sha256']
for p,h in m['source_sha256'].items():assert sha(p)==h,p
for name,h in m['candidate_sha256'].items():assert sha(stage/name)==h,name
backup=root/'before_contact_stability';backup.mkdir(exist_ok=False)
changes=[]
for name,h in m['candidate_sha256'].items():
 dst=repo/('scripts' if name=='collect_paired_sorting.py' else 'simfoundry/data')/name
 if dst.exists():shutil.copy2(dst,backup/name)
 shutil.copy2(stage/name,dst);assert sha(dst)==h
 changes.append(dict(path=str(dst),sha256=h))
p=repo/'simfoundry/data/waist_pilot_protocol.py';shutil.copy2(p,backup/p.name);s=p.read_text();old="'assets/robots/g1_hand_support_vertices.json', 'simfoundry/data/object_relative_push.py'}";assert s.count(old)==1;s=s.replace(old,"'assets/robots/g1_hand_support_vertices.json', 'simfoundry/data/object_relative_push.py',\n    'simfoundry/data/confirmed_position_release.py', 'simfoundry/data/initial_top_route.py',\n    'simfoundry/data/initial_top_route_candidate.py'}");p.write_text(s)
(root/'CONTACT_STABILITY_INTEGRATION.json').write_text(json.dumps(dict(changes=changes,applied_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_protocol_sha256=sha(run/'PROTOCOL.json'),tests=98,cli_checks=7,training_ready=False,scope='Optional diagnostic control only, physical trials pending. Original gates unchanged.'),indent=2))
print('Applied diagnostic candidate; physics still pending.')
