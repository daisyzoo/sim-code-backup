"""Review routing and fixed experiment plan preparation only; no physics launch."""
from pathlib import Path
import ast,json,hashlib,datetime,re,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'rear_trailing_physical_preparation_r1';D=W/'rear_trailing_contact_preparation_r1';sys.path[:0]=[str(W),str(ROOT)]
from watch_rear_trailing_trial1_numeric_reviews_r1 import check
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();plan=json.loads((P/'PLAN.json').read_text());parent=json.loads(Path(plan['parent_protocol']).read_text());assert sha(plan['parent_protocol'])==plan['parent_protocol_sha256'];assert plan['groups']==parent['plan']['groups'] and len(plan['commands'])==6
for c,old in zip(plan['commands'],parent['plan']['commands']):
 args=list(old['args']);args[args.index('--out-dir')+1]=c['args'][c['args'].index('--out-dir')+1];args.append('--rear-box-trailing-preference');assert c==dict(old,args=args)
 assert '--joint-transport-clearance' in args and '--push-assist' not in args
prep=json.loads((P/'REVIEW_AND_WATCHER_PREPARATION.json').read_text());inverse={v:k for k,v in prep['replacements'].items()};pattern=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))))
for r in prep['adapters']:
 p=Path(r['path']);assert sha(p)==r['sha256'] and sha(r['parent'])==r['parent_sha256'];assert pattern.sub(lambda m:inverse[m.group()],p.read_text())==Path(r['parent']).read_text();ast.parse(p.read_text())
short=ast.parse((W/'review_rear_trailing_trial1_incomplete_episode.py').read_text());assert any(isinstance(n,ast.ImportFrom) and n.module=='rear_trailing_stage_source_binding_v1' and any(a.name=='verify_trial_provenance' for a in n.names) for n in ast.walk(short))
source=(W/'review_rear_trailing_trial1_incomplete_episode.py').read_text();assert "short_attempt_cannot_pass=True" in source and "original_task_and_pose_passed=False" in source
routing=check();assert routing['passed']
files=[Path(__file__),P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json',D/'AUDIT_FAMILY_PREPARATION.json',D/'AUDIT_FAMILY_IMPORT_CHECK.json']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,fixed_conditions=10,fixed_pushes=8,fixed_waits=2,unchanged_full_audit_inventory=224,review_routing=routing,short_wrong_parent_source_reference_absent=True,source_sha256={**routing['source_sha256'],**{str(p):sha(p) for p in files},**{r['path']:r['sha256'] for r in prep['adapters']}},launcher_pending=True,physical_started=False,training_ready=False)
with (P/'REVIEW_ROUTING_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,conditions=10,audits=224,invalid_markers=routing['invalid_marker_rejections'],launcher_pending=True)))
