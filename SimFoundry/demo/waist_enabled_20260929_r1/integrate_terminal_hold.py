"""Apply staged default-off hold only after parent evidence is complete."""
from pathlib import Path
import json,hashlib,shutil,datetime
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_terminal_hold';run=root/'contact_stability_groups_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((stage/'MANIFEST.json').read_text());checks=json.loads((stage/'CLI_AND_REPLAY_CHECK.json').read_text())
assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
a=json.loads((run/'AUDIT_EXECUTION.json').read_text());assert len(a)==9 and all(x['returncode']==0 for x in a)
g=json.loads((run/'COMPLETE_GROUP_READINESS.json').read_text());assert g['errors']==['layout_62013_nudge_mailer_to_bin: task/pose failed']
r=json.loads((run/'RESULT.json').read_text());assert len(r['rows'])==12 and all(x['actual_sampled_visual_review']=='completed' for x in r['rows'])
assert checks['candidate_sha256']==m['candidate_sha256'] and len(checks['cli'])==5 and len(checks['recorded_replays'])==3
for p,h in m['source_sha256'].items():assert sha(p)==h,p
for name,h in m['candidate_sha256'].items():assert sha(stage/name)==h,name
for x in r['rows']:
 ep=run/('case_'+x['episode'].split('_')[1])/x['episode'];assert sha(ep/'raw.npz')==x['raw_sha256'] and sha(ep/'REVIEW_EVEN.jpg')==x['review_sheet_sha256']
backup=root/'before_terminal_hold';backup.mkdir(exist_ok=False);changes=[]
for name,h in m['candidate_sha256'].items():
 dst=repo/('scripts' if name=='collect_paired_sorting.py' else 'simfoundry/data')/name
 if dst.exists():shutil.copy2(dst,backup/name)
 shutil.copy2(stage/name,dst);assert sha(dst)==h;changes.append(dict(path=str(dst),sha256=h))
p=repo/'simfoundry/data/waist_pilot_protocol.py';shutil.copy2(p,backup/p.name);s=p.read_text();old="'simfoundry/data/initial_top_route_candidate.py'}";assert s.count(old)==1;s=s.replace(old,"'simfoundry/data/initial_top_route_candidate.py', 'simfoundry/data/terminal_joint_hold.py'}");p.write_text(s);changes.append(dict(path=str(p),sha256=sha(p)))
(root/'TERMINAL_HOLD_INTEGRATION.json').write_text(json.dumps(dict(changes=changes,parent_protocol_sha256=sha(run/'PROTOCOL.json'),applied_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Optional terminal joint command hold, original gates unchanged; no physical proof yet.',training_ready=False),indent=2))
print('Applied default-off terminal hold; physical validation pending.')
