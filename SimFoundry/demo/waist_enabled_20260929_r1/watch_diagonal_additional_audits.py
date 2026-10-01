"""Audit fully saved new-diagonal episodes after independent geometry audit.
Explicitly retain any failed optimality or unsupported execution checks. No
simulation restart, data changes, new thresholds, or training admission.
"""
from pathlib import Path
import json,sys,subprocess,hashlib,datetime,time,os
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]).resolve();rows=[];done=set();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
scripts=['audit_region_causal_xy_continuity_live.py','audit_region_measured_bounds_live.py','audit_rear_joint_xy_live.py','audit_front_diagonal_entry_live.py','audit_diagonal_unchanged_loaded_execution.py','audit_self_clearance_task_optimality.py']
manifest={str(w/n):sha(w/n) for n in scripts};manifest[str(Path(__file__))]=sha(__file__)
(r/'ADDITIONAL_AUDIT_PROTOCOL.json').write_text(json.dumps(dict(source_sha256=manifest,scope=__doc__,training_ready=False),indent=2))
def save(stage):
 p=r/'ADDITIONAL_AUDIT_EXECUTION.json';temp=p.with_suffix('.tmp');temp.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_episodes=sorted(done),rows=rows,source_sha256=manifest,training_ready=False),indent=2));temp.replace(p)
save('running')
while True:
 for n,h in manifest.items():assert sha(n)==h
 for ep in sorted(r.glob('case_*/layout_*')):
  if 'wait' in ep.name or ep.name in done or not (ep/'SELF_CLEARANCE_LIVE_AUDIT.json').exists():continue
  geometry=json.loads((ep/'SELF_CLEARANCE_LIVE_AUDIT.json').read_text())
  if not geometry.get('episode_clearance_passed'):
   rows.append(dict(episode=ep.name,returncode=1,reason='Incomplete geometry-verified physical episode; no full execution claim'));done.add(ep.name);save('running');continue
  for script in scripts:
   log=ep/(script+'.log');result=subprocess.run([sys.executable,str(w/script),str(ep)],capture_output=True,text=True);log.write_text(result.stdout+'\n'+result.stderr)
   row=dict(episode=ep.name,script=script,returncode=result.returncode,raw_sha256=sha(ep/'raw.npz'),auditor_sha256=sha(w/script),log_sha256=sha(log));rows.append(row);print(json.dumps(row),flush=True);save('running')
  done.add(ep.name);save('running')
 try:state=json.loads((r/'STATUS.json').read_text())['status']
 except (FileNotFoundError,json.JSONDecodeError):time.sleep(5);continue
 if len(done)==8 or state not in ['starting','running']:
  save('complete' if len(done)==8 else 'incomplete');break
 time.sleep(15)
