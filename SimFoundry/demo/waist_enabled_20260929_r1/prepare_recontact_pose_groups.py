"""Freeze original full8push2wait and only the unloaded pose feature flag.
All runtime source/checker bindings must be current before any output directory
is created. Never reuse existing experiment directories or relax quality gates.
"""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'rear_short_recovery_groups_r1';oldstage=w/'staged_rear_short_recovery';stage=w/'staged_recontact_pose';r=w/'recontact_pose_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare():
 assert not r.exists()
 closed=json.loads((parent/'RESULT.json').read_text());assert closed['status']=='diagnostic_closed_rejected' and closed['push_total']==8 and closed['waits_passed']==2 and closed['actual_sampled_visual_review_complete']
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json','SUPPLEMENTAL_AUDIT_EXECUTION.json']:
  state=json.loads((parent/name).read_text());assert not Path(f"/proc/{state['pid']}/cmdline").exists()
 reports=['INTEGRATION_CHECK.json','COMMAND_ENTRY_CHECK.json','COLLECTOR_ENTRY_CHECK.json','INDEPENDENT_EVENTS_CHECK.json','FINAL_ACTION_CHECK.json','NORMAL_CHECK.json','LIVE_FILES_CHECK.json','TASK_OPTIMALITY_CHECK.json','LOADED_EXECUTION_CHECK.json','SELF_CLEARANCE_CHECK.json','HEIGHT_CHECK.json','REGION_CHAIN_CHECK.json','REFERENCE_DEPENDENTS_CHECK.json','RUN_PROTOCOL_CHECK.json']
 for name in reports:
  d=json.loads((stage/name).read_text());assert d['passed'],name
  for path,h in d['source_sha256'].items():assert sha(path)==h,(name,path)
  if 'fixture_sha256' in d:assert sha(w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json')==d['fixture_sha256']
 old=json.loads((parent/'PROTOCOL.json').read_text());files={}
 for name,h in old['frozen_files_sha256'].items():
  assert sha(name)==h,name
  path=Path(name.replace(str(oldstage),str(stage)))
  if str(path).startswith(str(parent/'layouts')):continue
  if path.exists():files[str(path)]=sha(path)
 commands=copy.deepcopy(old['commands'])
 for c in commands:c['args']=[x.replace(str(parent),str(r)) for x in c['args']]+['--unloaded-recontact-pose']
 for a,b in zip(old['commands'],commands):assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and [x.replace(str(r),str(parent)) for x in b['args'][:-1]]==a['args']
 assert sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
 # All new direct and transitive checker/runtime inputs join the original freeze.
 for path in stage.iterdir():
  if path.suffix in ['.py','.json']:files[str(path)]=sha(path)
 for name in reports:
  for path,h in json.loads((stage/name).read_text())['source_sha256'].items():files[path]=h
 for pattern in ['audit_recontact_*.py','check_recontact_*.py','*recontact_pose_groups.py','watch_recontact_pose_audits.py','recontact_audit_context.py','recontact_run_contract.py','RECONTACT_REGION_VERSION_MAP.json','screen_recontact_original_budget.py']:
  for path in w.glob(pattern):files[str(path)]=sha(path)
 r.mkdir();(r/'layouts').mkdir()
 for src in (parent/'layouts').glob('*.json'):
  dest=r/'layouts'/src.name;dest.write_bytes(src.read_bytes());files[str(dest)]=sha(dest)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Same original8push2wait/tasks/layouts/seeds/1200push70wait/order. Only unloaded-recontact-pose added. Original80controls with3 named versions plus56extra, independent pose/final geometry and10actualimage reviews. Original1e-6KKT/loaded math unchanged; no precision candidate or training admission.',training_ready=False)
 (r/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(same_tasks_layouts_seeds_horizons_order=True,new_flag='--unloaded-recontact-pose',commands=6,control_invocations=80,additional_invocations=56,training_ready=False),indent=2));print(r)
if __name__=='__main__':prepare()
