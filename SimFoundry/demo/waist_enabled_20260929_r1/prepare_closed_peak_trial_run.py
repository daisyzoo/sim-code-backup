"""Freeze original12-group fresh collection after complete diagnostic closure."""
from pathlib import Path
import datetime,hashlib,json,shutil,ast
W=Path(__file__).resolve().parent;ROOT=W.parents[1];RUN=W/'fresh_closed_peak_trials_r1';STAGE=W/'staged_closed_peak_trial'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 assert not RUN.exists()
 current=W/'instant_guard_groups_r1';result=json.loads((current/'RESULT.json').read_text())
 assert result['status']=='diagnostic_closed_not_training_admission' and result['actual_sampled_visual_review_complete'] and len(result['rows'])==10 and all(r['full_length'] and r['all_audits_passed'] for r in result['rows'])
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  d=json.loads((current/name).read_text());assert not (Path('/proc')/str(d['pid'])/'cmdline').exists()
 assert (current/'PRESSURE_SETTING_BINDING.json').is_file()
 # Single collector only; don't infer inactivity from stale status files.
 for p in Path('/proc').glob('[0-9]*/cmdline'):
  try:parts=p.read_bytes().split(b'\0')
  except (OSError,PermissionError):continue
  assert not any(Path(v.decode(errors='replace')).name=='collect_paired_sorting.py' for v in parts if v),str(p)
 files=dict(json.loads((W/'peak_guard_groups_r1/PROTOCOL.json').read_text())['frozen_files_sha256'])
 checks=['staged_closed_peak_trial/CLI_CHECK.json','CLOSED_PEAK_TRIAL_SOURCE_BINDING_CHECK_R2.json','CLOSED_PEAK_TRIAL_AUDIT_VERSION_CHECK.json','CLOSED_PEAK_TRIAL_DRIVER_CHECK.json','CLOSED_PEAK_TRIAL_CONVERSION_PREPARATION.json','CLOSED_PEAK_TRIAL_DIAGNOSTIC_REJECTION.json']
 for name in checks:
  p=W/name;d=json.loads(p.read_text())
  if 'passed' in d:assert d['passed'] is True
  bindings=d.get('source_sha256',d.get('sources',{}))
  if isinstance(bindings,str):
   assert name=='CLOSED_PEAK_TRIAL_DIAGNOSTIC_REJECTION.json'
   bindings={str(W/'closed_peak_trial_data_audit.py'):bindings}
  for src,h in bindings.items():assert sha(src)==h,src;files[src]=h
  for row in d.get('rows',[]):
   if 'new' in row:
    assert sha(row['parent'])==row['parent_sha256'] and sha(row['new'])==row['new_sha256'];files[row['parent']]=row['parent_sha256'];files[row['new']]=row['new_sha256']
  files[str(p)]=sha(p)
 driver=json.loads((W/'CLOSED_PEAK_TRIAL_DRIVER_CHECK.json').read_text());commands=driver['commands'];assert len(commands)==36 and sum(len(c['tasks']) for c in commands)==60
 for c in commands:
  cp=Path(c['contract_path']);assert sha(cp)==c['contract_sha256'];files[str(cp)]=sha(cp)
  contract=json.loads(cp.read_text());assert sha(STAGE/'collect_paired_sorting.py')==contract['pilot_collector_sha256']
  for rel,h in contract['controller_source_sha256'].items():assert sha(ROOT/rel)==h;files[str(ROOT/rel)]=h
 for p in STAGE.iterdir():
  if p.is_file():files[str(p)]=sha(p)
 for pattern in ['*closed_peak_trial*.py','*closed_peak_trials.py','check_closed_peak_trial*.py']:
  for p in W.glob(pattern):files[str(p)]=sha(p)
 for p in [Path(__file__),current/'RESULT.json',current/'PRESSURE_SETTING_BINDING.json',W/'peak_guard_groups_r1/RESULT.json']:
  files[str(p)]=sha(p)
 # Every actual audit entry point is syntax-checked; transitive original math is in the inherited frozen set.
 for p in files:
  if Path(p).suffix=='.py' and Path(p).parent==W:ast.parse(Path(p).read_text())
 for p,h in files.items():assert sha(p)==h,p
 estimate=json.loads((W/'CLOSED_PEAK_TRIAL_STORAGE_ESTIMATE.json').read_text());reserve=estimate['full60_collection_reserve_bytes'];free=shutil.disk_usage(W).free
 assert free-reserve>30*2**30,(free/2**30,reserve/2**30)
 RUN.mkdir()
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(STAGE/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,reference_result_sha256=sha(W/'peak_guard_groups_r1/RESULT.json'),latest_single_change_result_sha256=sha(current/'RESULT.json'),selection='Use closed peak profile: instantaneous-load addition did not change7/8+2/2 outcome and still fails rear box. This is collection-only, not universal expert feasibility.',scope='Original12pre-outcome groups,8train4validation, four families each3,48push+12wait, both category assignments. Original1200/70,5N,.03withdrawal,waist1rad,camera,graph,noassist,zero-start,quality retained. Real fresh pilot only. Every failed condition/group remains visible; no diagnostic promotion or automatic training.',training_ready=False)
 (RUN/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));(RUN/'STORAGE_BUDGET.json').write_text(json.dumps(dict(reserved_full_collection_bytes=reserve,free_before=free,remaining_after_reserve=free-reserve,unchanged_per_case_guard_bytes=30*2**30,training_checkpoint_budget_separate=True),indent=2))
 print(json.dumps(dict(run=str(RUN),frozen_files=len(files),conditions=60,freeGiB=free/2**30,reserveGiB=reserve/2**30,remaining_after_reserveGiB=(free-reserve)/2**30,prepared_not_started=True),indent=2))

if __name__=='__main__':main()
