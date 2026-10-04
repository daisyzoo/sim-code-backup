"""One isolated quarter-Z trial after exact front-box producer finishes and ten actual reviews.
Keep original full comparison and all224audits; never synthesize reviews, retry
physical failures, or admit diagnostic data. Wait for GPU/storage without bypass.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,time,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_loaded_z_quarter_physical_preparation_r2';R=W/'front_loaded_z_quarter_physical_r2';EARLIER=W/'front_box_trailing_physical_r2';sys.path[:0]=[str(W),str(ROOT)]
from run_front_loaded_z_quarter_trial2_physical_r2 import configuration,identity,parent_readiness
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def prepare():
 assert not R.exists();plan,config=configuration();previous=read(EARLIER/'PROTOCOL.json');pid=previous['producer_pid'];info=identity(pid);script=str(W/'run_front_box_trailing_trial2_physical_r2.py')
 if info and info['state']!='Z':assert script.encode() in info['cmd']
 else:
  state=read(EARLIER/'STATUS.json');assert state['status']=='collection_complete_audits_visual_pending' and state['completed_conditions']==10
 frozen=dict(config['source_sha256'])
 for p in [Path(__file__),P/'CONFIGURATION_CHECK.json',EARLIER/'PROTOCOL.json']:frozen[str(p)]=sha(p)
 result=dict(created_at_utc=now(),scope=__doc__,previous_producer=dict(pid=pid,start=None if info is None else info['start'],script=script),target=str(R),source_sha256=frozen,conditions=10,audit_count=224,training_ready=False)
 with (P/'LAUNCH_QUEUE_PLAN.json').open('x') as f:json.dump(result,f,indent=2)
 return result

def main():
 os.chdir(ROOT.parent);plan=read(P/'LAUNCH_QUEUE_PLAN.json');assert plan['target']==str(R) and not R.exists();fd=os.open(P/'LAUNCH_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 def save(status,**kw):
  p=P/'LAUNCH_QUEUE_STATUS.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=now(),training_ready=False,**kw),indent=2));t.replace(p)
 try:
  while True:
   for p,h in plan['source_sha256'].items():assert sha(p)==h,p
   previous=plan['previous_producer'];info=identity(previous['pid']);state=read(EARLIER/'STATUS.json');assert state['status']!='runtime_or_audit_failed',state
   if info and info['state']!='Z':assert info['start']==previous['start'] and previous['script'].encode() in info['cmd'];save('waiting_for_exact_front_box_producer',completed_conditions=state['completed_conditions']);time.sleep(15);continue
   assert state['status']=='collection_complete_audits_visual_pending' and state['completed_conditions']==10,'front-box producer ended incomplete'
   if not (EARLIER/'NUMERIC_VISUAL_SUMMARY.json').exists():save('waiting_for_ten_actual_front_box_reviews');time.sleep(15);continue
   summary=read(EARLIER/'NUMERIC_VISUAL_SUMMARY.json');assert summary['actual_reviews']==10 and len(summary['rows'])==10 and not summary['training_ready']
   for p,h in summary['source_sha256'].items():assert sha(p)==h,p
   ready=parent_readiness();assert ready['ready'],ready
   gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True)
   if gpu.stdout.strip():save('waiting_for_gpu');time.sleep(15);continue
   from rear_corridor_storage_budget import require_storage
   try:storage=require_storage(ROOT,read(P/'PLAN.json')['commands'])
   except AssertionError as e:save('waiting_for_original_storage_minimum',reason=str(e));time.sleep(15);continue
   assert not R.exists();save('launching_once',storage=storage)
   env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OMNI_KIT_ACCEPT_EULA='yes',EXP_PATH='/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/isaacsim/apps',PYTHONUNBUFFERED='1')
   with (P/'producer.log').open('x') as f:child=subprocess.Popen([sys.executable,str(W/'run_front_loaded_z_quarter_trial2_physical_r2.py')],cwd=ROOT.parent,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
   ci=identity(child.pid);assert ci is not None;launch=dict(created_at_utc=now(),producer_pid=child.pid,producer_start=ci['start'],queue_pid=os.getpid(),plan_sha256=sha(P/'LAUNCH_QUEUE_PLAN.json'),training_ready=False)
   with (P/'LAUNCH.json').open('x') as f:json.dump(launch,f,indent=2)
   while child.poll() is None and not (R/'PROTOCOL.json').exists():time.sleep(2)
   assert (R/'PROTOCOL.json').exists(),('launch terminated before protocol',child.poll());assert read(R/'PROTOCOL.json')['producer_pid']==child.pid;save('launched_once',launch=launch);return
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
 if args.prepare:prepare();print('QUEUE_PREPARED_NO_PHYSICS')
 else:main()
