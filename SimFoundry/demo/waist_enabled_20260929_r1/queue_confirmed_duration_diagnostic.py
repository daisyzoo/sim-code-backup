"""Single-Isaac queue for the explicitly declared duration-only diagnostic."""
from pathlib import Path
import os,time,json,subprocess,hashlib,datetime
root=Path(__file__).resolve().parent;prior=root/'projected_confirmed_clearance_r1';own=root/'CONFIRMED_DURATION_QUEUE.json'
def status(stage,**kw):own.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2))
try:
 status('waiting_for_prior_terminal',prior_runner_pid=3779673)
 while (prior/'STATUS.json').exists() and json.loads((prior/'STATUS.json').read_text())['stage']=='running':time.sleep(10)
 assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
 while Path('/proc/3779673').exists():time.sleep(2)
 protocol=json.loads((prior/'PROTOCOL.json').read_text())
 for name,digest in protocol['source_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
 rows=[]
 for c in (62008,62009):rows+=json.loads((prior/f'case_{c}/POSE_AND_MOTION_REVIEW.json').read_text())['rows']
 assert len(rows)==4
 failed=[r['episode'] for r in rows if not(r['quality']['passed'] and r['pose']['search_success'])]
 assert failed==['layout_62008_push_box_to_bin'],failed
 # Duration is the only changed factor. All old failures remain retained.
 py='/home/user/miniconda3/envs/env_isaaclab/bin/python'
 with (root/'projected_confirmed_clearance_long_runner.log').open('w') as log:
  child=subprocess.Popen([py,str(root/'run_projected_confirmed_clearance_long.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  status('duration_diagnostic_running',runner_pid=child.pid,prior_original_task_pose='3/4')
  out=root/'projected_confirmed_clearance_long_r1'
  while not (out/'STATUS.json').exists():
   assert child.poll() is None,'Long runner exited before STATUS';time.sleep(1)
  with (root/'projected_confirmed_clearance_long_audits.log').open('w') as auditlog:
   watcher=subprocess.Popen([py,str(root/'complete_swap_audits.py'),str(out)],stdout=auditlog,stderr=subprocess.STDOUT,start_new_session=True)
  status('duration_diagnostic_running',runner_pid=child.pid,audit_watcher_pid=watcher.pid,prior_original_task_pose='3/4')
  (root/'RUNNING_PROCESS.json').write_text(json.dumps(dict(recorded_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_pid=child.pid,script=str(root/'run_projected_confirmed_clearance_long.py'),output=str(out),point_in_time_stage=json.loads((out/'STATUS.json').read_text()),runner_alive_verified=child.poll() is None,source_hash_verified=True,audit_watcher_pid=watcher.pid,queue_pid=os.getpid(),training_ready=False),indent=2))
  code=child.wait();status('duration_runner_terminal',runner_pid=child.pid,audit_watcher_pid=watcher.pid,returncode=code,actual_visual_review='pending')
except BaseException as exc:status('queue_failed',error=repr(exc));raise
