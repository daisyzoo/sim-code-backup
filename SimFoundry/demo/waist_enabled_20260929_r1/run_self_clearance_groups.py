"""Execute the unchanged8push2wait tasks with isolated clearance task IK.
Failures/early rejections stay in denominator; no retry, conversion or training.
Geometry audit does not replace original contact/controller/visual audits.
"""
from pathlib import Path
import sys,os,json,hashlib,subprocess,datetime,shutil
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];r=Path(sys.argv[1]).resolve();p=json.loads((r/'PROTOCOL.json').read_text());records=[]
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
def status(state,**kw):
 (r/'STATUS.json').write_text(json.dumps(dict(status=state,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,completed_conditions=len(records),**kw),indent=2))
def frozen():
 for path,h in p['frozen_files_sha256'].items():assert sha(path)==h,path
frozen();env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];status('starting')
try:
 for item in p['commands']:
  frozen();assert shutil.disk_usage(repo).free>30*1024**3
  case=r/f"case_{item['layout_id']}";assert not case.exists()
  with (r/f"case_{item['layout_id']}.log").open('w') as log:
   child=subprocess.Popen([sys.executable,p['collector'],*item['args'],'--out-dir',str(case)],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
   status('running',collector_pid=child.pid,current_layout=item['layout_id'])
   code=child.wait()
  frozen();state=json.loads((case/'STATUS.json').read_text());assert code in (0,1)
  assert state['status']=='numeric_pass_visual_review_pending' or (state['status']=='blocked_quality_or_runtime' and state['error'] in ['Quality gate failed. Stop; no retries or training export. See manifest.json.','Wait quality gate failed.']),(code,state)
  prov=json.loads((case/'provenance.json').read_text());assert prov['args']['self_clearance_task_ik'] is True
  for rel,h in prov['source_sha256'].items():assert sha(case/'source_snapshot'/rel)==h==p['frozen_files_sha256'][str(repo/rel)]
  for task in item['tasks']:
   ep=case/f"layout_{item['layout_id']}_{task}";quality=json.loads((ep/'quality.json').read_text());clearance=json.loads((ep/'self_clearance.json').read_text());frames=clearance['recorded_frames'];requested=70 if item['wait'] else 1200;assert clearance['requested_frames']==requested and frames<=requested
   if frames<requested:assert not quality['passed'] and clearance['failure'] is not None
   with (ep/'self_clearance_audit.log').open('w') as log:subprocess.run([sys.executable,str(w/'audit_self_clearance_live.py'),str(ep)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
   audit=json.loads((ep/'SELF_CLEARANCE_LIVE_AUDIT.json').read_text());assert audit['passed']
   if item['wait'] and frames==requested:
    with (ep/'wait_audit.log').open('w') as log:ret=subprocess.run([sys.executable,str(w/'audit_normal_wait.py'),str(ep)],env=env,stdout=log,stderr=subprocess.STDOUT)
    report=json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text());assert ret.returncode==(0 if report['passed'] else 1)
   records.append(dict(layout_id=item['layout_id'],task=task,wait=item['wait'],quality=quality,executed_frames=frames,requested_frames=requested,clearance_passed=audit['episode_clearance_passed'],clearance_failure=clearance['failure'],remaining_audits=['original contact/control','actual image review'],training_ready=False))
   (r/'COLLECTION_EXECUTION.json').write_text(json.dumps(records,indent=2))
 status('collection_and_geometry_audit_complete_original_audits_visual_pending',original_task_gates_passed=sum(x['quality']['passed'] for x in records),total_conditions=len(records))
except Exception as exc:
 status('runtime_or_audit_failed',error=repr(exc));raise
