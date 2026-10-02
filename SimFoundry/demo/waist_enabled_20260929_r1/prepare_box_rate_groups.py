"""Freeze complete rear-only slow drag diagnostic against closed minimum-motion trial."""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;parent=w/'minimum_motion_groups_r1';stage=w/'staged_rear_box_rate';run=w/'rear_box_rate_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def commands():
 p=json.loads((parent/'PROTOCOL.json').read_text());items=copy.deepcopy(p['commands'])
 for before,c in zip(p['commands'],items):
  c['args']=[v.replace(str(parent),str(run)) for v in c['args']]+['--rear-box-slow-drag']
  assert [v.replace(str(run),str(parent)) for v in c['args'][:-1]]==before['args']
 return p,items

def prepare():
 assert not run.exists();p,items=commands();files=copy.deepcopy(p['frozen_files_sha256'])
 comparator=w/'rear_slow_drag_groups_r1'
 complete=json.loads((comparator/'RESULT.json').read_text())
 assert complete['status']=='diagnostic_closed_not_training_admission' and complete['actual_sampled_visual_review_complete'] and len(complete['rows'])==10 and complete['original_control_invocations']==80 and complete['additional_invocations']==56 and not complete['training_ready']
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  status=json.loads((comparator/name).read_text());assert not Path(f"/proc/{status['pid']}/cmdline").exists()
 files.update(json.loads((comparator/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 for name in ['RESULT.json','PROTOCOL.json','PRESSURE_SETTING_BINDING.json']:files[str(comparator/name)]=sha(comparator/name)
 for name,h in files.items():assert sha(name)==h,name
 result=json.loads((parent/'RESULT.json').read_text());assert result['status']=='diagnostic_closed_not_training_admission' and result['push_total']==8 and len(result['rows'])==10 and result['actual_sampled_visual_review_complete'] and result['original_control_invocations']==80 and result['additional_invocations']==56 and not result['training_ready']
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  d=json.loads((parent/name).read_text());assert not Path(f"/proc/{d['pid']}/cmdline").exists()
 for name in ['RESULT.json','PROTOCOL.json','PRESSURE_SETTING_BINDING.json']:files[str(parent/name)]=sha(parent/name)
 for name in ['INTEGRATION_CHECK.json','RECONSTRUCTION_CHECK.json','RUN_PROTOCOL_CHECK.json']:
  d=json.loads((stage/name).read_text());assert d['passed'],name
  for path,h in d['source_sha256'].items():assert sha(path)==h,(name,path);files[path]=h
  files[str(stage/name)]=sha(stage/name)
 for q in stage.iterdir():
  if q.suffix in ['.py','.json']:files[str(q)]=sha(q)
 for pattern in ['audit_box_rate_*.py','box_rate_*.py','BOX_RATE_AUDIT_VERSION_MAP.json','*box_rate_groups.py','watch_box_rate_audits.py','check_box_rate_*.py','build_box_rate_versions.py','verify_top_pressure_setting.py']:
  for q in w.glob(pattern):files[str(q)]=sha(q)
 run.mkdir();(run/'layouts').mkdir()
 for q in (parent/'layouts').glob('*.json'):
  dst=run/'layouts'/q.name;dst.write_bytes(q.read_bytes());files[str(dst)]=sha(dst)
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=items,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Rear box selected COP route only: drag_step3mm to1mm. Rear bag and all front/initial route inputs unchanged from original minimum-motion baseline. Prior full uniform rear1.5mm trial must be closed first. Full8push2wait same layout seed order1200/70 frames5N original camera/waist limits/quality. Reentrant independent path audit; declared-step reconstruction. Original80+56 checks/36primary/10actualreviews. Not training admission or modelh10 proof.',training_ready=False)
 (run/'PROTOCOL.json').write_text(json.dumps(out,indent=2));(run/'INPUT_COMPARISON.json').write_text(json.dumps(dict(only_new_flag='--rear-box-slow-drag',rear_box_effective_drag_step_m=.001,rear_bag_effective_drag_step_m=.003,other_effective_drag_step_m=.003,same_tasks_layouts_seeds_budgets_order_pressure_camera=True,control_invocations=80,additional_invocations=56,training_ready=False),indent=2));print('prepared_not_started',run,len(files))
if __name__=='__main__':prepare()
