"""Install only after preceding physical run, audits and actual review close."""
from pathlib import Path
import json,hashlib,shutil,datetime,ast
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_trial_collection';run=w/'contact_bout_yaw_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for pid in [306492,306764,306765]:
 if Path('/proc',str(pid),'cmdline').exists():raise RuntimeError('Prior handle still alive: '+str(pid))
for proc in Path('/proc').glob('[0-9]*/cmdline'):
 try:args=proc.read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 if any(Path(x.decode(errors='replace')).name=='collect_paired_sorting.py' for x in args if x):raise RuntimeError('Another collector still alive')
assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
for p,digest in json.loads((run/'PROTOCOL.json').read_text())['source_sha256'].items():assert sha(p)==digest,p
result=json.loads((run/'RESULT.json').read_text());assert len(result['rows'])==8 and result['passed_conditions']==0
for row in result['rows']:
 ep=next(run.glob('case_*/'+row['episode']));assert row['actual_sampled_visual_review']=='completed';assert sha(ep/'raw.npz')==row['raw_sha256'] and sha(ep/'REVIEW_EVEN.jpg')==row['review_sheet_sha256']
batch=json.loads((run/'AUDIT_EXECUTION.json').read_text());assert len(batch)==9 and all(x['returncode']==0 for x in batch)
control=json.loads((run/'CONTROL_EVIDENCE_EXECUTION.json').read_text());assert control['stage']=='complete' and len(control['rows'])==80
watch=ast.parse((w/'watch_contact_bout_yaw_evidence.py').read_text());specs=ast.literal_eval(next(n.value for n in ast.walk(watch) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='report_specs' for t in n.targets)))
for row in control['rows']:
 ep=next(run.glob('case_*/'+row['episode']));filename,keys=specs[row['script']];assert row['returncode']==row['process_returncode']==0 and row['report_passed'];assert sha(ep/'raw.npz')==row['raw_sha256'] and sha(ep/filename)==row['report_sha256'] and sha(w/row['script'])==row['auditor_sha256'];value=json.loads((ep/filename).read_text())
 for key in keys:value=value[key]
 assert value is True
manifest=json.loads((stage/'MANIFEST.json').read_text());assert manifest['installed'] is False
for name,digest in manifest['candidate_sha256'].items():assert sha(stage/name)==digest,name
for name in ['SCHEMA_CHECK.json','COLLECTOR_LIFECYCLE_CHECK.json','DATA_ADMISSION_CHECK.json']:assert json.loads((stage/name).read_text())['passed'] is True
mapping={'collect_paired_sorting.py':repo/'scripts/collect_paired_sorting.py','waist_pilot_protocol.py':repo/'simfoundry/data/waist_pilot_protocol.py','waist_trial_collection.py':repo/'simfoundry/data/waist_trial_collection.py','build_trial_collection_contract.py':w/'build_trial_collection_contract.py','run_fresh_waist_pilot.py':w/'run_fresh_waist_pilot.py','watch_fresh_pilot_controls.py':w/'watch_fresh_pilot_controls.py'}
backup=w/'before_trial_collection_v2';backup.mkdir();records=[]
for name,dest in mapping.items():
 prior=sha(dest) if dest.exists() else None
 if dest.exists():shutil.copy2(dest,backup/name)
 records.append(dict(candidate=name,destination=str(dest),before_sha256=prior,after_sha256=sha(stage/name)))
# All gate/hash checks precede all mutations; no live collector is running.
for name,dest in mapping.items():shutil.copy2(stage/name,dest)
report=dict(installed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=records,preceding_result_sha256=sha(run/'RESULT.json'),scope='Collection-only v2; no archived diagnostic promotion, gate relaxation or training approval. Rejected yaw option stays off in builder. Original frozen12 plans unchanged.',training_ready=False)
(w/'TRIAL_COLLECTION_V2_INSTALLATION.json').write_text(json.dumps(report,indent=2));manifest['installed']=True;manifest['installation_sha256']=sha(w/'TRIAL_COLLECTION_V2_INSTALLATION.json');(stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(report,indent=2))
