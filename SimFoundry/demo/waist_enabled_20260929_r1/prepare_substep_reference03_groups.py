"""Freeze full original0.03 8push2wait plus read-only substep instrumentation."""
from pathlib import Path
import json,hashlib,datetime,copy,shutil
W=Path(__file__).resolve().parent;parent=W/'box_inward_groups_r1';run=W/'substep_reference03_groups_r1';stage=W/'staged_substep_observer';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not run.exists()
for r in [parent,W/'tilt05_groups_r1']:
 d=json.loads((r/'RESULT.json').read_text());assert d['status']=='diagnostic_closed_not_training_admission' and len(d['rows'])==10 and d['actual_sampled_visual_review_complete']
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  state=json.loads((r/name).read_text());assert not Path(f"/proc/{state['pid']}/cmdline").exists()
 if r==parent:assert all(x['all_audits_passed'] for x in d['rows'])
p=json.loads((parent/'PROTOCOL.json').read_text());files=copy.deepcopy(p['frozen_files_sha256'])
for name,h in files.items():assert sha(name)==h,name
checks=['SUBSTEP_RUNTIME_BRIDGE_GPU_CHECK.json','SUBSTEP_RECORDING_CHECK.json','SUBSTEP_FILE_AUDIT_CHECK.json','SUBSTEP_SOURCE_BINDING_CHECK.json','SUBSTEP_AUDIT_VERSION_CHECK.json','SUBSTEP_DRIVER_VERSION_CHECK.json','staged_substep_observer/REFERENCE03_PRELAUNCH_CHECK.json']
for name in checks:
 f=W/name;d=json.loads(f.read_text());assert d['passed']
 for source,h in d.get('source_sha256',{}).items():
  assert sha(source)==h,(name,source)
  # Test data bindings are verified here; only live code/contract sources need
  # repeated runtime freeze checks. Closed evidence retains its own hashes.
  q=Path(source)
  if q.suffix=='.py' or q.parent in (W,stage):files[str(q)]=h
 for row in d.get('rows',[]):
  if 'new' in row:
   assert sha(row['new'])==row['new_sha256'] and sha(row['parent'])==row['parent_sha256'];files[row['new']]=row['new_sha256'];files[row['parent']]=row['parent_sha256']
 files[str(f)]=sha(f)
for q in stage.iterdir():
 if q.is_file():files[str(q)]=sha(q)
for pattern in ['audit_substep*.py','substep_*.py','*substep_groups.py','watch_substep_audits.py','prepare_substep_reference03_groups.py']:
 for q in W.glob(pattern):files[str(q)]=sha(q)
for q in [parent/'PROTOCOL.json',parent/'RESULT.json',parent/'PRESSURE_SETTING_BINDING.json',W/'tilt05_groups_r1/RESULT.json',W/'tilt05_groups_r1/MICRO_GUARD_SCOPE_CORRECTION.json',W/'IMMUTABLE_ARCHIVE_DEDUP_RESULT.json']:
 files[str(q)]=sha(q)
commands=copy.deepcopy(p['commands'])
for before,c in zip(p['commands'],commands):
 c['args']=[v.replace(str(parent),str(run)) for v in c['args']]+['--trace-substep-contacts']
 assert float(c['args'][c['args'].index('--expert-top-tilt-recontact-rad')+1])==.03
 assert [v.replace(str(run),str(parent)) for v in c['args'][:-1]]==before['args']
assert len(commands)==6 and sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
# Budget keeps the unchanged30GiB per-case guard with a concrete full-run reserve.
parent_bytes=sum(q.stat().st_size for q in parent.rglob('*') if q.is_file())
reserved=int(parent_bytes*1.25+1.0*1024**3);free=shutil.disk_usage(W).free
assert free-reserved>30*1024**3,(free,reserved)
run.mkdir();(run/'layouts').mkdir()
for q in (parent/'layouts').glob('*.json'):
 dest=run/'layouts'/q.name;dest.write_bytes(q.read_bytes());files[str(dest)]=sha(dest)
protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Original0.03 closed inward baseline, only additional independent read-only substep observations. Same8push2wait/layouts/seeds/order1200/70frames/5N/camera/waist/240recoveryticks;36primary80control56additional+10substep audits,10actualreviews. No controller feedback replacement, no assist, graph/physics unchanged. Diagnostic only; instrumentation may perturb numerical execution and is not a control improvement.',training_ready=False)
(run/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2))
(run/'STORAGE_BUDGET.json').write_text(json.dumps(dict(parent_logical_bytes=parent_bytes,reserved_run_bytes=reserved,free_bytes_before=free,remaining_after_reserve=free-reserved,unchanged_per_case_guard_bytes=30*1024**3,training_ready=False),indent=2))
(run/'INPUT_COMPARISON.json').write_text(json.dumps(dict(reference='box_inward_groups_r1',internal_withdrawal_rad=.03,extra_flag='--trace-substep-contacts',same_tasks_layouts_seeds_budgets_order_pressure_camera=True,parent_collector_recovered_byte_exact=True,controller_feedback_unchanged=True,training_ready=False),indent=2))
print('PREPARED_NOT_STARTED',run,'frozen',len(files),'reserved_GiB',reserved/1024**3,'free_GiB',free/1024**3)
