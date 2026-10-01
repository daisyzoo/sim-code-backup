"""Freeze causal minimum-motion recontact against the closed parent-seed baseline."""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;parent=w/'parent_seed_groups_r1';stage=w/'staged_minimum_motion_recontact';run=w/'minimum_motion_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def commands():
 p=json.loads((parent/'PROTOCOL.json').read_text());out=copy.deepcopy(p['commands'])
 for before,c in zip(p['commands'],out):
  c['args']=[x.replace(str(parent),str(run)) for x in c['args']]+['--minimum-motion-recontact']
  assert [x.replace(str(run),str(parent)) for x in c['args'][:-1]]==before['args']
  assert float(c['args'][c['args'].index('--expert-frontal-top-load-n')+1])==5.
 return p,out

def prepare():
 assert not run.exists();p,items=commands();files=copy.deepcopy(p['frozen_files_sha256'])
 for name,h in files.items():assert sha(name)==h,name
 result=json.loads((parent/'RESULT.json').read_text());assert result['status']=='diagnostic_closed_not_training_admission' and result['push_total']==8 and len(result['rows'])==10 and result['actual_sampled_visual_review_complete'] and result['original_control_invocations']==80 and result['additional_invocations']==56 and not result['training_ready']
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  d=json.loads((parent/name).read_text());assert not Path(f"/proc/{d['pid']}/cmdline").exists()
 for name in ['RESULT.json','PROTOCOL.json','PRESSURE_SETTING_BINDING.json']:files[str(parent/name)]=sha(parent/name)
 for name in ['INTEGRATION_CHECK.json','PRELAUNCH_CHECK.json','AUDIT_VERSION_CHECK.json','RUNTIME_PLANNER_CHECK.json','INDEPENDENT_AUDIT_CHECK.json','LIFECYCLE_CHECK.json','LIVE_FILES_CHECK.json','RUN_PROTOCOL_CHECK.json']:
  d=json.loads((stage/name).read_text());assert d.get('passed',d.get('complete',False)),name
  for path,h in d['source_sha256'].items():assert sha(path)==h,(name,path);files[path]=h
  files[str(stage/name)]=sha(stage/name)
 for q in stage.iterdir():
  if q.suffix in ['.py','.json']:files[str(q)]=sha(q)
 for pattern in ['audit_minimum_motion_*.py','minimum_motion_audit_context.py','MINIMUM_MOTION_AUDIT_VERSION_MAP.json','minimum_motion_run_contract.py','*minimum_motion_groups.py','watch_minimum_motion_audits.py','check_minimum_motion_*.py','build_minimum_motion_audit_versions.py','verify_top_pressure_setting.py']:
  for q in w.glob(pattern):files[str(q)]=sha(q)
 run.mkdir();(run/'layouts').mkdir()
 for q in (parent/'layouts').glob('*.json'):
  dst=run/'layouts'/q.name;dst.write_bytes(q.read_bytes());files[str(dst)]=sha(dst)
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=items,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Causal minimum-motion unloaded recontact pose and fully sampled straight/raised path preference only. Parent loaded control remains; its task-to-edge execution chain has dedicated independent audit. Full8push2wait same layouts/seed/order/budgets/5N/camera/precision1e-13 and original loaded objective/bounds/1e-6KKT. Original80+56 audits with explicit new source/path versions;10actual image reviews. Not training admission or modelh10 success.',training_ready=False)
 (run/'PROTOCOL.json').write_text(json.dumps(out,indent=2));(run/'INPUT_COMPARISON.json').write_text(json.dumps(dict(only_new_flag='--minimum-motion-recontact',same_tasks_layouts_seeds_budgets_order_pressure_camera=True,control_invocations=80,additional_invocations=56,training_ready=False),indent=2));print('prepared_not_started',run,len(files))
if __name__=='__main__':prepare()
