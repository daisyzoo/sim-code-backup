"""Freeze complete rear-only slow drag diagnostic against closed minimum-motion trial."""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;parent=w/'minimum_motion_groups_r1';stage=w/'staged_rear_slow_drag';run=w/'rear_slow_drag_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def commands():
 p=json.loads((parent/'PROTOCOL.json').read_text());items=copy.deepcopy(p['commands'])
 for before,c in zip(p['commands'],items):
  c['args']=[v.replace(str(parent),str(run)) for v in c['args']]+['--rear-slow-drag']
  assert [v.replace(str(run),str(parent)) for v in c['args'][:-1]]==before['args']
 return p,items

def prepare():
 assert not run.exists();p,items=commands();files=copy.deepcopy(p['frozen_files_sha256'])
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
 for pattern in ['audit_slow_drag_*.py','slow_drag_*.py','SLOW_DRAG_AUDIT_VERSION_MAP.json','*slow_drag_groups.py','watch_slow_drag_audits.py','check_slow_drag_*.py','build_slow_drag_versions.py','verify_top_pressure_setting.py']:
  for q in w.glob(pattern):files[str(q)]=sha(q)
 run.mkdir();(run/'layouts').mkdir()
 for q in (parent/'layouts').glob('*.json'):
  dst=run/'layouts'/q.name;dst.write_bytes(q.read_bytes());files[str(dst)]=sha(dst)
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=items,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Rear selected COP route only: drag_step3mm to1.5mm. All front/initial route inputs unchanged. Full8push2wait same layout seed order1200/70 frames5N original camera/waist limits/quality. Reentrant independent path audit; declared-step reconstruction. Original80+56 checks/36primary/10actualreviews. Not training admission or modelh10 proof.',training_ready=False)
 (run/'PROTOCOL.json').write_text(json.dumps(out,indent=2));(run/'INPUT_COMPARISON.json').write_text(json.dumps(dict(only_new_flag='--rear-slow-drag',rear_effective_drag_step_m=.0015,other_effective_drag_step_m=.003,same_tasks_layouts_seeds_budgets_order_pressure_camera=True,control_invocations=80,additional_invocations=56,training_ready=False),indent=2));print('prepared_not_started',run,len(files))
if __name__=='__main__':prepare()
