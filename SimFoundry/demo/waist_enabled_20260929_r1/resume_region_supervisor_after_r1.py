"""Wait for exact R1 controller/supervisor; no physical job restart."""
from pathlib import Path
import sys,json,time,subprocess,os,datetime
w=Path(__file__).resolve().parent;r=w/'region_patch_groups_r1';pid=863591
while (Path('/proc')/str(pid)/'cmdline').exists():time.sleep(5)
a=json.loads((r/'STATUS.json').read_text());assert a['pid']==pid and a['error']=="KeyError('push_assist')",a
assert not (Path('/proc')/'863637'/'cmdline').exists()
(r/'SUPERVISOR_R1_TERMINAL.json').write_text(json.dumps(a,indent=2))
with (r/'runner_r2.log').open('w') as log:
 p=subprocess.Popen([sys.executable,str(w/'run_region_patch_groups_r2.py'),str(r)],cwd=w.parents[1],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(r/'RUNNING_PROCESS_R2.json').write_text(json.dumps(dict(pid=p.pid,started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False),indent=2))
