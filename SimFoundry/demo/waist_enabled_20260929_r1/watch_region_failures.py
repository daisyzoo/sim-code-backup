"""Generate actual completed-region event evidence, never approve images/data."""
from pathlib import Path
import json,sys,subprocess,time,os,datetime,hashlib
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]);done=set();records=[]
if (r/'REGION_DIAGNOSTIC_EXECUTION.json').exists():
 records=json.loads((r/'REGION_DIAGNOSTIC_EXECUTION.json').read_text())['rows'];done={x['episode'] for x in records if x['returncode']==0}
def save(stage):
 p=r/'REGION_DIAGNOSTIC_EXECUTION.tmp';p.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),rows=records,updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False),indent=2));p.replace(r/'REGION_DIAGNOSTIC_EXECUTION.json')
save('running')
while True:
 for ep in sorted(r.glob('case_*/layout_*')):
  if ep.name in done or not (ep/'quality.json').exists() or not (ep/'region_approach.json').exists():continue
  with (ep/'region_physics_diagnosis.log').open('w') as log:ret=subprocess.run([sys.executable,str(w/'diagnose_region_physics.py'),str(ep)],stdout=log,stderr=subprocess.STDOUT)
  entry=dict(episode=ep.name,returncode=ret.returncode,actual_visual_review='pending')
  if ret.returncode==0:
   d=json.loads((ep/'REGION_PHYSICS_DIAGNOSIS.json').read_text());event=d['first_abort']['step'] if d['first_abort'] else d['handover_steps'][0] if d['handover_steps'] else 600;frames=sorted(set([0,max(0,event-3),max(0,event-1),event,min(1199,event+1),min(1199,event+5),min(1199,event+60),1199]));subprocess.run([sys.executable,str(w/'render_episode_frames.py'),str(ep),*map(str,frames)],check=True)
   entry.update(first_abort_step=d['first_abort']['step'] if d['first_abort'] else None,abort_reason=d['first_abort']['abort_reason'] if d['first_abort'] else None,handover_steps=d['handover_steps'],report_sha256=hashlib.sha256((ep/'REGION_PHYSICS_DIAGNOSIS.json').read_bytes()).hexdigest())
  records.append(entry);done.add(ep.name);save('running')
 state=json.loads((r/'STATUS.json').read_text())['stage']
 if state!='running':save('complete' if state=='numeric_complete_actual_visual_review_pending' else 'upstream_stopped');break
 time.sleep(10)
