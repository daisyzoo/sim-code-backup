"""Install reviewed isolated candidate only after full predecessor audit shutdown."""
from pathlib import Path
import json,hashlib,shutil,datetime,os
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_contact_bout_yaw';prior=w/'y_path_nearhalf_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();manifest=json.loads((stage/'MANIFEST.json').read_text())
for pid in [31356,31530,31531]:
 assert not Path(f'/proc/{pid}').exists(),f'Parent process still exists:{pid}'
for p in Path('/proc').glob('[0-9]*/cmdline'):
 try:parts=p.read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 assert not any(Path(os.fsdecode(x)).name=='collect_paired_sorting.py' for x in parts if x),'Another collector is live'
assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
controls=json.loads((prior/'CONTROL_EVIDENCE_EXECUTION.json').read_text());assert controls['stage']=='complete' and len(controls['rows'])==72 and all(r['report_passed'] and r['returncode']==0 for r in controls['rows'])
audits=json.loads((prior/'AUDIT_EXECUTION.json').read_text());assert len(audits)==9 and all(r['returncode']==0 for r in audits)
review=json.loads((prior/'RESULT.json').read_text());assert len(review['rows'])==8
for r in review['rows']:
 ep=prior/('case_'+r['episode'].split('_')[1])/r['episode'];assert r['actual_sampled_visual_review']=='completed';assert sha(ep/'raw.npz')==r['raw_sha256'] and sha(ep/'REVIEW_EVEN.jpg')==r['review_sheet_sha256']
for name in ['PURE_CHECK.json','WIRING_CHECK.json','AUDITOR_CHECK.json']:assert json.loads((stage/name).read_text())['passed']
for p,h in manifest['source_sha256'].items():assert sha(p)==h,p
for n,h in manifest['candidate_sha256'].items():assert sha(stage/n)==h,n
planp=w/'CONTACT_BOUT_YAW_PLAN.json';plan=json.loads(planp.read_text());backup=w/'before_contact_bout_yaw';backup.mkdir(exist_ok=False);changes=[]
for name,dest in [('contact_bout_yaw.py',repo/'simfoundry/data/contact_bout_yaw.py'),('waist_coordination.py',repo/'simfoundry/data/waist_coordination.py'),('collect_paired_sorting.py',repo/'scripts/collect_paired_sorting.py')]:
 old=sha(dest) if dest.exists() else None
 if dest.exists():shutil.copy2(dest,backup/name)
 shutil.copy2(stage/name,dest);changes.append(dict(path=str(dest),old_sha256=old,new_sha256=sha(dest)))
for p,h in plan['source_sha256'].items():assert sha(p)==h,p
plan.update(parent_result_sha256=sha(prior/'RESULT.json'),preceding_result_sha256=sha(prior/'RESULT.json'),execution_ready=True);planp.write_text(json.dumps(plan,indent=2));manifest['installed']=True;manifest['installed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
report=dict(installed_at_utc=manifest['installed_at_utc'],changes=changes,plan_sha256=sha(planp),parent_result_sha256=sha(prior/'RESULT.json'),parent_processes_stopped=True,post_install_checks_pending=True,training_ready=False);(w/'CONTACT_BOUT_YAW_INSTALLATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
