"""Frozen diagnostic whole swap groups; numeric failures retained, runtime stops."""
from pathlib import Path
import sys,os,json,hashlib,subprocess,datetime,shutil
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];r=Path(sys.argv[1]).resolve();p=json.loads((r/'PROTOCOL.json').read_text());records=[]
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def status(stage,**kw):
 tmp=r/'STATUS.tmp';tmp.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2));tmp.replace(r/'STATUS.json')
def frozen():
 for n,h in p['auditor_dependency_sha256'].items():assert sha(w/n)==h,n
 for relative,digest in p['source_sha256'].items():assert sha(repo/relative)==digest,relative
 for path,digest in p['layout_sha256'].items():assert sha(path)==digest,path
 assert sha(__file__)==p['runner_sha256']
 assert sha(w/'audit_region_x_follow_live.py')==p['audit_sha256']
def startup(case):
 prov=json.loads((case/'provenance.json').read_text());assert prov['source_sha256']==p['source_sha256']
 for relative,digest in p['source_sha256'].items():assert sha(case/'source_snapshot'/relative)==digest
 a=prov['args'];assert a['role']=='diagnostic' and a['region_top_approach'] and a['region_tracking_residual'] and not a['waist_pilot_contract'] and not a['expert_top_contact_bout_yaw_hold']
 (case/'STARTUP_SOURCE_CHECK.json').write_text(json.dumps(dict(passed=True,archived_sources=len(p['source_sha256']),training_ready=False),indent=2))
env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1')
status('running')
try:
 for item in p['commands']:
  frozen();assert shutil.disk_usage(repo).free>30*1024**3
  case=r/f"case_{item['layout_id']}"
  recovered=False;assert not case.exists()
  with (r/f"case_{item['layout_id']}.log").open('w') as log:
   child=subprocess.Popen([sys.executable,p['collector'],*item['args'],'--out-dir',str(case)],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
   status('running',collector_pid=child.pid,current_layout=item['layout_id'])
   try:code=child.wait(timeout=1800)
   except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=60);raise
  frozen();startup(case)
  state=json.loads((case/'STATUS.json').read_text());failure=state.get('status')=='blocked_quality_or_runtime' and state.get('error') in ('Quality gate failed. Stop; no retries or training export. See manifest.json.','Wait quality gate failed.')
  assert code in (0,1) and (state['status']=='numeric_pass_visual_review_pending' or failure),(code,state)
  for task in item['tasks']:
   ep=case/f"layout_{item['layout_id']}_{task}";quality=json.loads((ep/'quality.json').read_text())
   with np.load(ep/'raw.npz') as raw:
    assert raw['q'].shape==raw['action'].shape==(70 if item['wait'] else 1200,23)
    assert str(raw['task_id'])==task and np.max(abs(raw['q'][0,12:]))==np.max(abs(raw['action'][0,12:]))==0
    meta=json.loads(str(raw['collect_meta']));assert meta['assist_frames']==0 and not meta.get('waist_pilot_contract_sha256')
   records.append(dict(episode=ep.name,quality=quality,raw_sha256=sha(ep/'raw.npz'),collector_process_returncode=None if recovered else code,recovered_complete_case=recovered))
  (r/'COLLECTION_EXECUTION.json').write_text(json.dumps(records,indent=2))
  if not item['wait']:
   for script in ['audit_contacts.py','review_diagnostics.py']:
    with (r/f"{item['layout_id']}_{script}.log").open('w') as log:subprocess.run([sys.executable,str(w/script),str(case)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
   for task in item['tasks']:
    ep=case/f"layout_{item['layout_id']}_{task}"
    with (ep/'audit_region_action_live.log').open('w') as log:subprocess.run([sys.executable,str(w/'audit_region_x_follow_live.py'),str(ep)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  else:
   ep=case/f"layout_{item['layout_id']}_wait_no_package"
   with (ep/'wait_audit.log').open('w') as log:ret=subprocess.run([sys.executable,str(w/'audit_normal_wait.py'),str(ep)],env=env,stdout=log,stderr=subprocess.STDOUT)
   report=json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text());assert ret.returncode==(0 if report['passed'] else 1)
   subprocess.run([sys.executable,str(w/'render_episode_frames.py'),str(ep),*[str(x) for x in report['sampled_rgb_frames']]],env=env,check=True)
 status('numeric_complete_actual_visual_review_pending',original_tasks_passed=sum(x['quality']['passed'] for x in records),total_conditions=len(records))
except Exception as exc:
 status('runtime_or_control_audit_failed',error=repr(exc),completed_conditions=len(records));raise
