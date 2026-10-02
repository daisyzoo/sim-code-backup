"""Freeze original complete8push2wait single-change peak-bias experiment."""
from pathlib import Path
import copy,datetime,hashlib,json,shutil
W=Path(__file__).resolve().parent;parent=W/'substep_reference03_groups_r1';run=W/'peak_guard_groups_r1';stage=W/'staged_peak_load_guard';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not run.exists()
result=json.loads((parent/'RESULT.json').read_text());assert result['status']=='diagnostic_closed_not_training_admission' and len(result['rows'])==10 and result['actual_sampled_visual_review_complete'] and all(r['all_audits_passed'] for r in result['rows'])
for rel,h in result['evidence_sha256'].items():assert sha(parent/rel)==h,rel
for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
 d=json.loads((parent/name).read_text());assert not Path(f"/proc/{d['pid']}/cmdline").exists()
p=json.loads((parent/'PROTOCOL.json').read_text());files=copy.deepcopy(p['frozen_files_sha256'])
for path,h in files.items():assert sha(path)==h,path
checks=['PEAK_LOAD_BIAS_GUARD_BOUNDARY_CHECK.json','PEAK_LOAD_CONTROL_ADAPTER_CHECK.json','PEAK_LOAD_OBSERVATION_CHECK.json','PEAK_LOAD_UPDATE_MATH_CHECK.json','PEAK_GUARD_PRESSURE_STREAM_CHECK.json','PEAK_GUARD_SOURCE_BINDING_CHECK.json','PEAK_GUARD_AUDIT_VERSION_CHECK.json','PEAK_GUARD_DRIVER_VERSION_CHECK.json','staged_peak_load_guard/PRELAUNCH_CHECK.json']
for name in checks:
 f=W/name;d=json.loads(f.read_text());assert d['passed']
 for source,h in d['source_sha256'].items():
  q=Path(source);q=q if q.is_absolute() else W/q;assert sha(q)==h,(name,source)
  if q.suffix=='.py' or q.parent in (W,stage):files[str(q)]=h
 for row in d.get('rows',[]):
  if 'new' in row:
   assert sha(row['new'])==row['new_sha256'] and sha(row['parent'])==row['parent_sha256']
   files[row['new']]=row['new_sha256'];files[row['parent']]=row['parent_sha256']
 files[str(f)]=sha(f)
for q in stage.iterdir():
 if q.is_file():files[str(q)]=sha(q)
for pattern in ['*peak_guard*.py','peak_load_*.py','audit_peak_load_update_math.py','check_peak_load*.py']:
 for q in W.glob(pattern):files[str(q)]=sha(q)
for q in [parent/'PROTOCOL.json',parent/'RESULT.json',parent/'PRESSURE_SETTING_BINDING.json',parent/'CLOSED_AND_CANDIDATE_BINDING.json']:
 files[str(q)]=sha(q)
commands=copy.deepcopy(p['commands'])
for old,c in zip(p['commands'],commands):
 c['args']=[v.replace(str(parent),str(run)) for v in c['args']]+['--peak-load-bias-guard']
 assert [v.replace(str(run),str(parent)) for v in c['args'][:-1]]==old['args']
 assert c['args'].count('--trace-substep-contacts')==1
assert len(commands)==6 and sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
parent_bytes=sum(q.stat().st_size for q in parent.rglob('*') if q.is_file());reserve=int(parent_bytes*1.25+1024**3);free=shutil.disk_usage(W).free
assert free-reserve>30*1024**3,(free,reserve)
run.mkdir();(run/'layouts').mkdir()
for q in (parent/'layouts').glob('*.json'):
 dst=run/'layouts'/q.name;dst.write_bytes(q.read_bytes());files[str(dst)]=sha(dst)
protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Original complete8push2wait observed0.03 reference. Only previous-action24-substep peak>2x5N holds the negative pressure-bias increment; original filter, upward increments and phase guards retained. Same layouts/seeds/order1200/70,waist,camera,graph,5N,quality. Original36primary80control56extra10observer +10 independent pressure audits and10actualreviews. No training admission or modelh10 claim.',training_ready=False)
(run/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2))
(run/'STORAGE_BUDGET.json').write_text(json.dumps(dict(parent_logical_bytes=parent_bytes,reserved_run_bytes=reserve,free_bytes_before=free,remaining_after_reserve=free-reserve,unchanged_per_case_guard_bytes=30*1024**3,training_ready=False),indent=2))
(run/'INPUT_COMPARISON.json').write_text(json.dumps(dict(reference='substep_reference03_groups_r1',internal_withdrawal_rad=.03,top_load_n=5.,extra_flag='--peak-load-bias-guard',same_tasks_layouts_seeds_budgets_order_pressure_camera=True,parent_collector_recovered_byte_exact=True,negative_bias_increment_guard_only=True,original_filter_and_upward_relief=True,original_phase_guard_priority=True,training_ready=False),indent=2))
print('PREPARED_NOT_STARTED',run,'frozen',len(files),'reserve_GiB',reserve/1024**3,'remaining_after_reserve_GiB',(free-reserve)/1024**3)
