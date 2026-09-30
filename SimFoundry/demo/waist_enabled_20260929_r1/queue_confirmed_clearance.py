"""Wait for the full frozen batch and audits, then test and run the next diagnostic.

This queue never admits data and never marks actual visual review complete.
"""
from pathlib import Path
import os,json,time,subprocess,datetime,hashlib
root=Path(__file__).resolve().parent;project=root.parents[1];prior=root/'projected_recovery_xhold_long_r1';record=root/'CONFIRMED_CLEARANCE_QUEUE.json';py='/home/user/miniconda3/envs/env_isaaclab/bin/python'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def status(stage,**kw):record.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2))
try:
 status('waiting_for_full_prior_and_audits',prior_runner_pid=3618118)
 while json.loads((prior/'STATUS.json').read_text())['stage']=='running':time.sleep(10)
 assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
 while Path('/proc/3618118').exists():time.sleep(2)
 while True:
  audit=json.loads((prior/'AUDIT_EXECUTION.json').read_text()) if (prior/'AUDIT_EXECUTION.json').exists() else []
  assert all(x['returncode']==0 for x in audit),'Prior audit failed'
  if len(audit)==9:break
  assert Path('/proc/3618346').exists(),'Prior watcher exited before all nine audits'
  time.sleep(10)
 assert json.loads((prior/'TERMINAL_SOURCE_VERIFICATION.json').read_text()).get('verified_at_utc')
 protocol=json.loads((prior/'PROTOCOL.json').read_text())
 for p,h in protocol['source_sha256'].items():assert sha(p)==h,p
 rows=[]
 for i in (62008,62009):rows+=json.loads((prior/f'case_{i}/POSE_AND_MOTION_REVIEW.json').read_text())['rows']
 assert len(rows)==4
 failed=[r['episode'] for r in rows if not(r['quality']['passed'] and r['pose']['search_success'])]
 assert failed==['layout_62008_push_box_to_bin'],failed
 env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONPATH=str(project)+':'+str(project/'tests'))
 # Preserve complete original numerical/source evidence before changing code.
 with (prior/'pre_change_complete_group_audit.log').open('w') as log:subprocess.run([py,str(root/'audit_waist_complete_group.py'),str(prior)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 status('integrating_and_testing',prior_original_task_pose='3/4',prior_visual_review='pending_actual_view')
 subprocess.run([py,'/tmp/integrate_confirmed_clearance.py'],env=env,check=True)
 tests=['test_front_clearance_progress','test_front_clearance_confirmed','test_established_x_and_clearance_recovery','test_front_top_route','test_top_contact_bypass','test_projected_route_parameters','test_projected_support_reference']
 with (root/'confirmed_clearance_tests.log').open('w') as log:subprocess.run([py,'-m','unittest',*tests],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 with (root/'projected_confirmed_clearance_runner.log').open('w') as log:
  child=subprocess.Popen([py,str(root/'run_projected_confirmed_clearance.py')],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  out=root/'projected_confirmed_clearance_r1'
  while not(out/'STATUS.json').exists():
   assert child.poll() is None,'Runner exited before STATUS';time.sleep(1)
  for p,h in json.loads((out/'PROTOCOL.json').read_text())['source_sha256'].items():assert sha(p)==h,p
  with (root/'projected_confirmed_clearance_audits.log').open('w') as log:
   watcher=subprocess.Popen([py,str(root/'complete_swap_audits.py'),str(out)],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  status('candidate_running',runner_pid=child.pid,audit_watcher_pid=watcher.pid,tests_passed=True,prior_visual_review='pending_actual_view')
  (root/'RUNNING_PROCESS.json').write_text(json.dumps(dict(recorded_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_pid=child.pid,script=str(root/'run_projected_confirmed_clearance.py'),output=str(out),point_in_time_stage=json.loads((out/'STATUS.json').read_text()),runner_alive_verified=child.poll() is None,source_hash_verified=True,audit_watcher_pid=watcher.pid,queue_pid=os.getpid(),previous_batch_audits_complete=True,training_ready=False),indent=2))
  code=child.wait();status('candidate_terminal',runner_pid=child.pid,audit_watcher_pid=watcher.pid,returncode=code,actual_visual_review='pending')
except BaseException as exc:status('queue_failed',error=repr(exc));raise
