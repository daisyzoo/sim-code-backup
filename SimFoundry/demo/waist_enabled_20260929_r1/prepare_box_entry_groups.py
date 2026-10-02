"""Freeze next complete entry-lift diagnostic only after full predecessor closure."""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;parent=w/'box_center_groups_r1';stage=w/'staged_box_entry_lift';run=w/'box_entry_lift_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def commands():
 p=json.loads((parent/'PROTOCOL.json').read_text());items=copy.deepcopy(p['commands'])
 for before,c in zip(p['commands'],items):
  c['args']=[v.replace(str(parent),str(run)) for v in c['args']]+['--rear-box-entry-lift']
  assert [v.replace(str(run),str(parent)) for v in c['args'][:-1]]==before['args']
 return p,items

def prepare():
 assert not run.exists();p,items=commands();result=json.loads((parent/'RESULT.json').read_text())
 assert result['status']=='diagnostic_closed_not_training_admission' and len(result['rows'])==10 and result['push_total']==8 and result['actual_sampled_visual_review_complete'] and result['original_control_invocations']==80 and result['additional_invocations']==56 and not result['training_ready']
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  d=json.loads((parent/name).read_text());assert not Path(f"/proc/{d['pid']}/cmdline").exists()
 files=copy.deepcopy(p['frozen_files_sha256'])
 for name,h in files.items():assert sha(name)==h,name
 for name in ['RESULT.json','PROTOCOL.json','PRESSURE_SETTING_BINDING.json']:files[str(parent/name)]=sha(parent/name)
 checks=[stage/n for n in ['INTEGRATION_CHECK.json','PRELAUNCH_CHECK.json','AUDIT_VERSION_CHECK.json','RECONSTRUCTION_CHECK.json','NATIVE_CHECK.json','REJECTED_PLAN_CHECK.json','RUN_PROTOCOL_CHECK.json']]+[w/n for n in ['BOX_ENTRY_LIFT_TRACKING_CHECK.json','BOX_ENTRY_LIFT_COMBINED_CHECK.json','BOX_ENTRY_LIFT_GUARDED_CHECK.json','BOX_ENTRY_LIFT_EVENT_AUDIT_CHECK.json']]
 for path in checks:
  d=json.loads(path.read_text())
  if path.name=='BOX_ENTRY_LIFT_COMBINED_CHECK.json':assert d['complete'] and d['all_completed_within_budget'] and len(d['rows'])==13
  else:assert d['passed'],path
  for name,h in d['source_sha256'].items():assert sha(name)==h,(path,name);files[name]=h
  files[str(path)]=sha(path)
 for name in ['box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py']:assert sha(stage/name)==sha(w/name)
 for q in stage.iterdir():
  if q.suffix in ['.py','.json']:files[str(q)]=sha(q)
 for pattern in ['audit_box_entry_*.py','box_entry_*.py','box_recovery_entry_lift.py','BOX_ENTRY_AUDIT_VERSION_MAP.json','*box_entry_groups.py','watch_box_entry_audits.py','check_box_entry_*.py','prepare_box_entry_*.py','build_box_entry_audits.py','verify_top_pressure_setting.py']:
  for q in w.glob(pattern):files[str(q)]=sha(q)
 run.mkdir();(run/'layouts').mkdir()
 for q in (parent/'layouts').glob('*.json'):
  dst=run/'layouts'/q.name;dst.write_bytes(q.read_bytes());files[str(dst)]=sha(dst)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=items,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Default-off right-rear unloaded entry lift to measured original0.84m gate before unchanged1.5mm/400center recontact. Same full8push2wait, layout seed order1200/70 frames5N original camera/waist/quality. Combined recovery240ticks; pending phase guards stop on changed scene/contact/history or rejected subsequent plan. Original80+56 checks/36primary/10actualreviews. Not training admission or modelh10.',training_ready=False)
 (run/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));(run/'INPUT_COMPARISON.json').write_text(json.dumps(dict(only_new_flag='--rear-box-entry-lift',same_tasks_layouts_seeds_budgets_order_pressure_camera=True,unchanged_loaded_controls=True,original_entry_height_m=.84,nominal_lift_height_m=.845,maximum_lift_ticks=40,combined_recovery_ticks=240,control_invocations=80,additional_invocations=56,training_ready=False),indent=2));print('prepared_not_started',run,len(files))
if __name__=='__main__':prepare()
