"""Prepare same-source internal0.05rad withdrawal only after full parent closure.
No new collector code, no formal quality threshold change and no launch here.
"""
from pathlib import Path
import json,hashlib,datetime,copy
w=Path(__file__).resolve().parent;parent=w/'box_inward_groups_r1';run=w/'tilt05_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare():
 assert not run.exists(),'new directory required'
 previous=json.loads((parent/'RESULT.json').read_text())
 assert previous['status']=='diagnostic_closed_not_training_admission' and len(previous['rows'])==10 and previous['push_total']==8 and previous['actual_sampled_visual_review_complete']
 assert previous['original_control_invocations']==80 and previous['additional_invocations']==56 and previous['training_ready'] is False
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  d=json.loads((parent/name).read_text());assert not Path(f"/proc/{d['pid']}/cmdline").exists(),'parent still live'
 p=json.loads((parent/'PROTOCOL.json').read_text());files=copy.deepcopy(p['frozen_files_sha256'])
 for name,h in files.items():assert sha(name)==h,name
 for name in ['RESULT.json','PROTOCOL.json','PRESSURE_SETTING_BINDING.json']:files[str(parent/name)]=sha(parent/name)
 for name in ['TILT05_DIAGNOSTIC_CONTRACT_CHECK.json','TILT05_RUN_PROTOCOL_CHECK.json','TILT05_INSPECTOR_PREPARATION.json']:
  path=w/name;d=json.loads(path.read_text());assert d['passed'] is True
  for source,h in d['source_sha256'].items():assert sha(source)==h,(name,source);files[source]=h
  files[str(path)]=sha(path)
 check=json.loads((w/'TILT05_RUN_PROTOCOL_CHECK.json').read_text());commands=check['commands'];assert len(commands)==6 and check['original_control_count']==80 and check['additional_count']==56 and check['primary_count']==36
 for before,c in zip(p['commands'],commands):
  assert c['tasks']==before['tasks'] and c['layout_id']==before['layout_id'] and c['wait']==before['wait']
  i=c['args'].index('--expert-top-tilt-recontact-rad')+1;assert float(c['args'][i])==.05 and float(before['args'][i])==.03
  restored=[v.replace(str(run),str(parent)) for v in c['args']];restored[i]=before['args'][i];assert restored==before['args']
 from tilt05_run_contract import controls
 assert sum(len(controls(json.loads((parent/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"/'frontal_bypass.json').read_text())['plan'])) for c in commands if not c['wait'] for task in c['tasks'])==80
 for pattern in ['tilt05_*.py','audit_tilt05_*.py','check_tilt05_*.py','*tilt05_groups.py','watch_tilt05_audits.py','TILT05_SOURCE_EXPECTATIONS.json','verify_top_pressure_setting.py']:
  for q in w.glob(pattern):files[str(q)]=sha(q)
 for row in json.loads((w/'TILT05_SOURCE_EXPECTATIONS.json').read_text())['rows']:
  assert sha(row['path'])==row['sha256'];files[row['path']]=row['sha256']
 run.mkdir();(run/'layouts').mkdir()
 for q in (parent/'layouts').glob('*.json'):
  dest=run/'layouts'/q.name;dest.write_bytes(q.read_bytes());files[str(dest)]=sha(dest)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=p['collector'],commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Exactly same frozen inward collector, sole runtime parameter internal expert tilt withdrawal0.03->0.05rad. Original formal0.20rad upright and support/task/zero/assist/non-target15mm/actualh10 requirements unchanged; micro-return internal0.03 remains unchanged. Same8push2wait layouts/seeds/order1200/70frames/5N/camera/waist/240recoveryticks, complete36primary80control56additional10actualreviews. Not proof of causality from a single pair, training admission or modelh10.',training_ready=False)
 (run/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));(run/'INPUT_COMPARISON.json').write_text(json.dumps(dict(same_collector_sha256=sha(p['collector']),only_runtime_parameter_changed='--expert-top-tilt-recontact-rad',old_internal_withdrawal_rad=.03,new_internal_withdrawal_rad=.05,unchanged_formal_upright_gate_rad=.20,unchanged_micro_return_guard_rad=.03,same_tasks_layouts_seeds_budgets_order_pressure_camera=True,training_ready=False),indent=2));print('prepared_not_started',run,len(files))
if __name__=='__main__':prepare()
