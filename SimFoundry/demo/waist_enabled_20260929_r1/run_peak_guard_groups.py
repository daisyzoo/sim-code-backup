"""Full original8push2wait physical attempt, default-off pose flag enabled.
Source changes or unexpected collector crashes stop the run. Audited numerical
or expected guard failures stay visible and do not erase remaining conditions.
"""
from pathlib import Path
import sys,os,json,subprocess,datetime,shutil
from peak_guard_run_contract import primary,run_audit,sha
w=Path(__file__).resolve().parent;repo=w.parents[1];r=Path(sys.argv[1]).resolve();p=json.loads((r/'PROTOCOL.json').read_text());records=[]
def status(state,**kw):
 path=r/'STATUS.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=state,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(path)
def frozen():
 for path,h in p['frozen_files_sha256'].items():assert sha(path)==h,path
frozen();env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];status('starting')
try:
 for item in p['commands']:
  frozen();assert shutil.disk_usage(repo).free>30*1024**3
  case=r/f"case_{item['layout_id']}";assert not case.exists()
  with (r/f"case_{item['layout_id']}.log").open('w') as log:
   child=subprocess.Popen([sys.executable,p['collector'],*item['args'],'--out-dir',str(case)],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
   status('running',collector_pid=child.pid,current_layout=item['layout_id']);code=child.wait()
  frozen();state=json.loads((case/'STATUS.json').read_text());assert code in (0,1)
  assert state['status']=='numeric_pass_visual_review_pending' or (state['status']=='blocked_quality_or_runtime' and state['error'] in ['Quality gate failed. Stop; no retries or training export. See manifest.json.','Wait quality gate failed.']),(code,state)
  prov=json.loads((case/'provenance.json').read_text());assert prov['args']['peak_load_bias_guard'] is True and prov['args']['trace_substep_contacts'] is True and prov['args']['expert_top_tilt_recontact_rad']==.03 and prov['args']['rear_box_inward_correction'] is True and prov['args']['rear_box_entry_lift'] is True and prov['args']['rear_box_center_preference'] is True and prov['args']['rear_slow_drag'] is True and prov['args']['minimum_motion_recontact'] is True and prov['args']['rear_joint_edge_parent_seed_retry'] is True and prov['args']['precise_clearance_task_ik'] is True and prov['args']['recontact_interior_preference'] is True and prov['args']['unloaded_recontact_pose'] is True
  for rel,h in prov['source_sha256'].items():assert sha(case/'source_snapshot'/rel)==h==p['frozen_files_sha256'][str(repo/rel)],rel
  for task in item['tasks']:
   ep=case/f"layout_{item['layout_id']}_{task}";quality=json.loads((ep/'quality.json').read_text());clear=json.loads((ep/'self_clearance.json').read_text());frames=clear['recorded_frames'];requested=70 if item['wait'] else 1200;assert clear['requested_frames']==requested and frames<=requested
   if frames<requested:assert not quality['passed'] and clear['failure'] is not None
   rows=[]
   for script in primary(item['wait']):
    frozen();rows.append(run_audit(ep,script));print(json.dumps(rows[-1]),flush=True)
   (ep/'PRIMARY_AUDIT_EXECUTION.json').write_text(json.dumps(dict(rows=rows,completed=True,training_ready=False),indent=2))
   frozen();observer_row=run_audit(ep,'audit_peak_guard_contacts.py');print(json.dumps(observer_row),flush=True)
   (ep/'OBSERVATION_AUDIT_EXECUTION.json').write_text(json.dumps(dict(rows=[observer_row],completed=True,training_ready=False),indent=2))
   frozen();pressure_row=run_audit(ep,'audit_peak_guard_pressure.py');print(json.dumps(pressure_row),flush=True)
   (ep/'PRESSURE_AUDIT_EXECUTION.json').write_text(json.dumps(dict(rows=[pressure_row],completed=True,training_ready=False),indent=2))
   records.append(dict(layout_id=item['layout_id'],task=task,wait=item['wait'],quality=quality,executed_frames=frames,requested_frames=requested,primary_audits_passed=all(x['returncode']==0 for x in rows),clearance_failure=clear['failure'],training_ready=False))
   (r/'COLLECTION_EXECUTION.json').write_text(json.dumps(records,indent=2))
 status('collection_complete_audits_visual_pending',original_task_gates_passed=sum(x['quality']['passed'] for x in records),total_conditions=len(records))
except Exception as exc:
 status('runtime_or_audit_failed',error=repr(exc));raise
