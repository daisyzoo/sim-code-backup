"""Apply isolated optional normal constraint only after full parent review."""
from pathlib import Path
import json,hashlib,shutil,datetime
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_contact_normal';run=root/'terminal_hold_front09_groups_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
a=json.loads((run/'AUDIT_EXECUTION.json').read_text());assert len(a)==9 and all(x['returncode']==0 for x in a)
g=json.loads((run/'COMPLETE_GROUP_READINESS.json').read_text());assert len(g['rows'])==12 and all(e.endswith(': task/pose failed') for e in g['errors'])
r=json.loads((run/'RESULT.json').read_text());assert len(r['rows'])==12 and all(x['actual_sampled_visual_review']=='completed' for x in r['rows'])
for x in r['rows']:
 ep=run/('case_'+x['episode'].split('_')[1])/x['episode'];assert sha(ep/'raw.npz')==x['raw_sha256'] and sha(ep/'REVIEW_EVEN.jpg')==x['review_sheet_sha256']
m=json.loads((stage/'MANIFEST.json').read_text());checks=json.loads((stage/'WIRING_CHECK.json').read_text());assert checks['candidate_sha256']==m['candidate_sha256'] and len(checks['cli'])==5 and len(checks['measured_solver_fixtures'])==7 and checks['nonfront_top_active'] and checks['off_and_no_plan_inactive']
assert all(x['default_max_command_error_rad']==0 for x in checks['measured_solver_fixtures'])
math=json.loads((stage/'MATH_TESTS.json').read_text());assert math['passed'] and math['tests_run']==4 and math['helper_sha256']==sha(stage/'contact_normal_constraint.py')
for episode in ('layout_62013_nudge_mailer_to_bin','layout_62005_push_box_to_bin'):
 d=json.loads((stage/('CONTINUOUS_IK_CHECK_'+episode+'_with_lifts.json')).read_text());assert d['candidate_sha256']==m['candidate_sha256'] and d['includes_three_hypothetical_lifts']
 s=next(r['summary'] for r in d['results'] if r['summary']['normal_enabled']);assert s['max_active_error_after_initial_settle_m']<.005 and s['max_normal_error_after_initial_settle_deg']<3
for p,h in m['source_sha256'].items():assert sha(p)==h,p
for name,h in m['candidate_sha256'].items():assert sha(stage/name)==h,name
backup=root/'before_contact_normal';backup.mkdir(exist_ok=False);changes=[]
for name,h in m['candidate_sha256'].items():
 dst=repo/('scripts' if name=='collect_paired_sorting.py' else 'simfoundry/data')/name
 if dst.exists():shutil.copy2(dst,backup/name)
 shutil.copy2(stage/name,dst);assert sha(dst)==h;changes.append(dict(path=str(dst),sha256=h))
p=repo/'simfoundry/data/waist_pilot_protocol.py';shutil.copy2(p,backup/p.name);s=p.read_text();old="'simfoundry/data/terminal_joint_hold.py'}";assert s.count(old)==1;s=s.replace(old,"'simfoundry/data/terminal_joint_hold.py', 'simfoundry/data/contact_normal_constraint.py'}");p.write_text(s);changes.append(dict(path=str(p),sha256=sha(p)))
(root/'CONTACT_NORMAL_INTEGRATION.json').write_text(json.dumps(dict(changes=changes,parent_protocol_sha256=sha(run/'PROTOCOL.json'),applied_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Optional two-axis hand tilt constraint across top contact/recontact, free global yaw, disabled on guards/release; original quality gates unchanged. Kinematic checks are screen only; physical results pending.',training_ready=False),indent=2))
print('Applied default-off contact normal; fresh physical validation pending.')
