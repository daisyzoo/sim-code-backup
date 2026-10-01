"""Freeze independent precision trial against complete5N interior baseline.
The active full3N comparison must finish and close first. Original complete8push
2wait and every task/data gate retained. No camera/pressure/contact change.
"""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;parent=w/'recontact_interior_groups_r1';pressure=w/'recontact_interior_load3_groups_r1';stage=w/'staged_interior_task_precision';run=w/'precise_interior_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def commands():
 p=json.loads((parent/'PROTOCOL.json').read_text());out=copy.deepcopy(p['commands'])
 for before,c in zip(p['commands'],out):
  c['args']=[x.replace(str(parent),str(run)) for x in c['args']]+['--precise-clearance-task-ik']
  assert [x.replace(str(run),str(parent)) for x in c['args'][:-1]]==before['args']
  assert float(c['args'][c['args'].index('--expert-frontal-top-load-n')+1])==5.
 return p,out

def prepare():
 assert not run.exists();p,items=commands();files=copy.deepcopy(p['frozen_files_sha256'])
 for name,h in files.items():assert sha(name)==h,name
 for folder in [parent,pressure]:
  result=json.loads((folder/'RESULT.json').read_text());assert result['status']=='diagnostic_closed_not_training_admission' and result['push_total']==8 and len(result['rows'])==10 and result['actual_sampled_visual_review_complete'] and result['original_control_invocations']==80 and result['additional_invocations']==56 and not result['training_ready']
  for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
   d=json.loads((folder/name).read_text());assert not Path(f"/proc/{d['pid']}/cmdline").exists()
  files[str(folder/'RESULT.json')]=sha(folder/'RESULT.json');files[str(folder/'PROTOCOL.json')]=sha(folder/'PROTOCOL.json')
 reports=['INTEGRATION_CHECK.json','PRELAUNCH_CHECK.json','AUDIT_VERSION_CHECK.json','NATIVE_READER_CHECK.json','RUN_PROTOCOL_CHECK.json']
 for name in reports:
  d=json.loads((stage/name).read_text());assert d['passed'],name
  for path,h in d['source_sha256'].items():assert sha(path)==h,(name,path);files[path]=h
 for q in stage.iterdir():
  if q.suffix in ['.py','.json']:files[str(q)]=sha(q)
 for pattern in ['audit_precise_interior_*.py','audit_precision_source_contract.py','precise_interior_audit_context.py','PRECISE_INTERIOR_AUDIT_VERSION_MAP.json','precise_interior_run_contract.py','*precise_interior_groups.py','watch_precise_interior_audits.py','check_precise_interior_*.py']:
  for q in w.glob(pattern):files[str(q)]=sha(q)
 run.mkdir();(run/'layouts').mkdir()
 for q in (parent/'layouts').glob('*.json'):
  dst=run/'layouts'/q.name;dst.write_bytes(q.read_bytes());files[str(dst)]=sha(dst)
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=items,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),completed_pressure_result_sha256=sha(pressure/'RESULT.json'),scope='Independent precision trial versus original5N interior full8push2wait. Only optional ordinary task solver ftol1e-11->1e-13; same5N pressure,20mm preferred/12mm fallback, camera/layouts/seeds/order/budgets. Independent original80+56audit mathematics and original1e-6KKT unchanged, explicit new source-bound versions,10actual image reviews. Not training admission or modelh10 success.',training_ready=False)
 (run/'PROTOCOL.json').write_text(json.dumps(out,indent=2));(run/'INPUT_COMPARISON.json').write_text(json.dumps(dict(only_new_flag='--precise-clearance-task-ik',same_tasks_layouts_seeds_budgets_order_pressure_camera=True,control_invocations=80,additional_invocations=56,training_ready=False),indent=2));print('prepared_not_started',run,len(files))
if __name__=='__main__':prepare()
