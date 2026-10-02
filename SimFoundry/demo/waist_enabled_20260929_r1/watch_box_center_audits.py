"""Run the original80 control checks with3 explicit versions and56 extra checks.
Every attempted condition remains in the denominator; failures are recorded.
Wait for primary audit marker so no consumer reads a partially saved episode.
"""
from pathlib import Path
import sys,json,time,os,datetime
from box_center_run_contract import controls,ADDITIONAL,run_audit,sha
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]).resolve();protocol=json.loads((r/'PROTOCOL.json').read_text());control=[];extra=[];done=set()
def save(stage):
 for name,rows in [('CONTROL_EVIDENCE_EXECUTION.json',control),('ADDITIONAL_AUDIT_EXECUTION.json',extra)]:
  path=r/name;tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_episodes=sorted(done),rows=rows,training_ready=False),indent=2));tmp.replace(path)
def frozen():
 for path,digest in protocol['frozen_files_sha256'].items():assert sha(path)==digest,path
save('running')
while True:
 frozen()
 for item in protocol['commands']:
  if item['wait']:continue
  for task in item['tasks']:
   ep=r/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}"
   if ep.name in done or not (ep/'PRIMARY_AUDIT_EXECUTION.json').exists():continue
   if not (ep/'raw.npz').exists():
    failure=dict(episode=ep.name,returncode=1,reason='Missing raw episode; no admission');control.append(failure);extra.append(failure);done.add(ep.name);save('running');continue
   plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']
   for phase,scripts in [(control,controls(plan)),(extra,ADDITIONAL)]:
    for script in scripts:
     frozen();row=run_audit(ep,script);phase.append(row);print(json.dumps(row),flush=True);save('running')
   done.add(ep.name);save('running')
 try:status=json.loads((r/'STATUS.json').read_text())['status']
 except (FileNotFoundError,json.JSONDecodeError):time.sleep(5);continue
 if len(done)==8:save('complete');break
 if status not in ('starting','running'):save('incomplete');break
 time.sleep(10)
