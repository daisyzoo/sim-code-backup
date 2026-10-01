"""Resume unchanged physical plan after verifier-only coverage defect."""
from pathlib import Path
import sys,json,time,subprocess,datetime,hashlib
w=Path(__file__).resolve().parent;r=w/'region_patch_groups_r1';pid=922378
while (Path('/proc')/str(pid)/'cmdline').exists():time.sleep(5)
a=json.loads((r/'STATUS.json').read_text());assert a['pid']==pid and a['stage']=='runtime_or_control_audit_failed' and 'audit_region_action_live.py' in a['error'] and 'CalledProcessError' in a['error'],a
assert not (Path('/proc')/'923384'/'cmdline').exists()
(r/'SUPERVISOR_R2_TERMINAL.json').write_text(json.dumps(a,indent=2));(r/'RECOVERY_R3.json').write_text(json.dumps(dict(reason='R1 region auditor wrongly expected rows before projected top support was active. R2 auditor derives exact expected steps from actual frontal reference log; physical guard failure remains failure. All completed cases revalidated, never recollected.',original_case_exit_codes='Existing complete cases revalidated by final status/source/raw; no reconstructed process exit code claimed.',training_ready=False),indent=2))
with (r/'runner_r3.log').open('w') as log:p=subprocess.Popen([sys.executable,str(w/'run_region_patch_groups_r3.py'),str(r)],cwd=w.parents[1],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(r/'RUNNING_PROCESS_R3.json').write_text(json.dumps(dict(pid=p.pid,started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False),indent=2))
time.sleep(20)
for old,script,logname in [(888782,'watch_region_patch_controls.py','control_watcher_resume.log'),(947159,'watch_region_failures.py','region_watcher_resume.log')]:
 if not (Path('/proc')/str(old)/'cmdline').exists():
  with (r/logname).open('w') as log:p=subprocess.Popen([sys.executable,str(w/script),str(r)],cwd=w.parents[1],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (r/(script+'.RESUMED.json')).write_text(json.dumps(dict(pid=p.pid,training_ready=False),indent=2))
