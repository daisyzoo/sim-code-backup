"""Continue to full mirror diagnostics after actual parent review; no auto approval."""
from pathlib import Path
import os,time,json,subprocess,hashlib,datetime
root=Path(__file__).resolve().parent;prior=root/'projected_clearance_hysteresis_1200_r1';own=root/'HYSTERESIS_MIRROR_QUEUE.json'
def status(stage,**kw):
 own.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2))
try:
 status('waiting_for_parent_terminal_and_actual_review',prior_runner_pid=201800)
 while json.loads((prior/'STATUS.json').read_text())['stage']=='running':time.sleep(10)
 assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
 while Path('/proc/201800').exists():time.sleep(2)
 rows=[]
 for i in (62008,62009):rows+=json.loads((prior/f'case_{i}/POSE_AND_MOTION_REVIEW.json').read_text())['rows']
 assert len(rows)==4 and all(r['quality']['passed'] and r['pose']['search_success'] for r in rows),'Parent full original quality/pose failed'
 while True:
  audit=prior/'AUDIT_EXECUTION.json';ready=prior/'COMPLETE_GROUP_READINESS.json'
  if audit.exists() and ready.exists():
   checks=json.loads(audit.read_text());readiness=json.loads(ready.read_text())
   if len(checks)==9 and all(v['returncode']==0 for v in checks) and readiness.get('complete_group_feasibility_passed') and not readiness.get('errors'):break
  time.sleep(10)
 protocol=json.loads((prior/'PROTOCOL.json').read_text())
 for p,h in protocol['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 active=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:args=(p/'cmdline').read_bytes().split(b'\0')
  except OSError:continue
  if any(x.endswith(b'/collect_paired_sorting.py') for x in args):active.append(p.name)
 assert not active,active
 py='/home/user/miniconda3/envs/env_isaaclab/bin/python';out=root/'projected_hysteresis_mirror1200_r1'
 with (root/'hysteresis_mirror1200_runner.log').open('w') as log:
  child=subprocess.Popen([py,str(root/'run_hysteresis_mirror1200.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  status('mirror_starting',runner_pid=child.pid)
  while not (out/'STATUS.json').exists():
   assert child.poll() is None,'Runner stopped before STATUS';time.sleep(1)
  with (root/'hysteresis_mirror1200_audits.log').open('w') as log:
   watcher=subprocess.Popen([py,str(root/'complete_swap_audits.py'),str(out)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  status('mirror_running',runner_pid=child.pid,audit_watcher_pid=watcher.pid)
  (root/'RUNNING_PROCESS.json').write_text(json.dumps(dict(recorded_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_pid=child.pid,script=str(root/'run_hysteresis_mirror1200.py'),output=str(out),point_in_time_stage=json.loads((out/'STATUS.json').read_text()),runner_alive_verified=child.poll() is None,source_hash_verified=True,audit_watcher_pid=watcher.pid,queue_pid=os.getpid(),training_ready=False),indent=2))
  code=child.wait();status('mirror_runner_terminal',runner_pid=child.pid,audit_watcher_pid=watcher.pid,returncode=code,actual_visual_review='pending')
except BaseException as exc:status('queue_failed',error=repr(exc));raise
