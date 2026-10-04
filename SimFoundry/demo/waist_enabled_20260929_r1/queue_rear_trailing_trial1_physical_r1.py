"""One-shot separate rear trial after exact parent and prior reserve actual reviews.
No automatic visual approval, retries, training or data admission. Original CPU
checks may overlap; full parent audit closure remains mandatory for comparison.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,time,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'rear_trailing_physical_preparation_r1';R=W/'rear_trailing_physical_r1';BASE=W/'joint_transport_physical_r1';EARLIER=W/'joint_transport_reserve_physical_r1';Q=W/'joint_transport_reserve_physical_preparation_r1';sys.path[:0]=[str(W),str(ROOT)]
from run_rear_trailing_trial1_physical_r1 import configuration,parent_readiness,earlier_trial_readiness,identity
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def prepare():
 assert not R.exists();plan,config=configuration();check=read(P/'ORCHESTRATION_CHECK.json');assert check['passed'] and check['parent_inflight_preflight_rejected']
 frozen=dict(check['source_sha256'])
 for p in [Path(__file__),P/'ORCHESTRATION_CHECK.json',P/'LAUNCHER_CLOSURE_PREPARATION.json',P/'CONFIGURATION_CHECK.json',Q/'LAUNCH_QUEUE_V2_PLAN.json',Q/'CONFIGURATION_CHECK.json']:
  frozen[str(p)]=sha(p)
 for p,h in frozen.items():assert sha(p)==h,p
 protocol=read(BASE/'PROTOCOL.json');audit=read(BASE/'AUDIT_STATUS.json');dependencies=[]
 for pid,script in [(protocol['producer_pid'],'run_joint_transport_trial1_physical_r1.py'),(audit['pid'],'watch_joint_transport_trial1_physical_audits_r1.py')]:
  info=identity(pid);assert info is not None and info['state']!='Z' and str(W/script).encode() in info['cmd'];dependencies.append(dict(pid=pid,start=info['start'],script=str(W/script)))
 previous=read(Q/'LAUNCH_QUEUE_V2_STATUS.json');pid=previous['pid'];info=identity(pid);script=str(W/'queue_joint_transport_reserve_trial1_physical_r2.py');assert info is not None and info['state']!='Z' and script.encode() in info['cmd']
 prior=dict(pid=pid,start=info['start'],script=script,queue_plan_sha256=sha(Q/'LAUNCH_QUEUE_V2_PLAN.json'))
 result=dict(created_at_utc=now(),scope=__doc__,dependencies=dependencies,earlier_queue=prior,parent_protocol_sha256=sha(BASE/'PROTOCOL.json'),source_sha256=frozen,launch_script=str(W/'run_rear_trailing_trial1_physical_r1.py'),target=str(R),expected_conditions=10,expected_audits=224,requires_both_runs_ten_actual_reviews=True,training_ready=False)
 with (P/'LAUNCH_QUEUE_PLAN.json').open('x') as f:json.dump(result,f,indent=2)
 return result

def check_earlier_identity(plan):
 dep=plan['earlier_queue'];info=identity(dep['pid'])
 if info is not None and info['state']!='Z':assert info['start']==dep['start'] and dep['script'].encode() in info['cmd'],'earlier queue PID replaced'
 else:assert read(Q/'LAUNCH_QUEUE_V2_STATUS.json')['status']=='launched_once','earlier queue ended without successful one-shot launch'
 assert sha(Q/'LAUNCH_QUEUE_V2_PLAN.json')==dep['queue_plan_sha256']
 if (Q/'LAUNCH.json').exists():
  launch=read(Q/'LAUNCH.json');assert launch['plan_sha256']==dep['queue_plan_sha256'];child=identity(launch['producer_pid'])
  if child is not None and child['state']!='Z':assert child['start']==launch['producer_start'] and str(W/'run_joint_transport_reserve_trial1_physical_r1.py').encode() in child['cmd']
  else:assert (EARLIER/'STATUS.json').exists() and read(EARLIER/'STATUS.json')['status']=='collection_complete_audits_visual_pending','earlier producer ended incomplete'
  if (EARLIER/'PROTOCOL.json').exists():assert read(EARLIER/'PROTOCOL.json')['producer_pid']==launch['producer_pid']

def main():
 plan=read(P/'LAUNCH_QUEUE_PLAN.json');assert plan['target']==str(R) and not R.exists()
 for p,h in plan['source_sha256'].items():assert sha(p)==h,p
 fd=os.open(P/'LAUNCH_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 def save(status,**kw):
  dest=P/'LAUNCH_QUEUE_STATUS.json';tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=now(),training_ready=False,**kw),indent=2));tmp.replace(dest)
 env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OMNI_KIT_ACCEPT_EULA='yes',EXP_PATH='/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/isaacsim/apps',PYTHONUNBUFFERED='1')
 try:
  while True:
   for p,h in plan['source_sha256'].items():assert sha(p)==h,p
   assert sha(BASE/'PROTOCOL.json')==plan['parent_protocol_sha256'];state=read(BASE/'STATUS.json');assert state['status']!='runtime_or_audit_failed',state
   for dep in plan['dependencies']:
    info=identity(dep['pid'])
    if info is not None and info['state']!='Z':assert info['start']==dep['start'] and dep['script'].encode() in info['cmd'],'original dependency PID replaced'
    elif 'run_joint_transport_trial1' in dep['script']:assert state['status']=='collection_complete_audits_visual_pending','original producer ended early'
    else:assert read(BASE/'AUDIT_STATUS.json')['status']=='complete','original audit ended incomplete'
   check_earlier_identity(plan);parent=parent_readiness();prior=earlier_trial_readiness()
   if not parent['ready'] or not prior['ready']:save('waiting_for_parent_and_prior_reserve_actual_reviews',parent=parent,earlier_reserve=prior);time.sleep(15);continue
   gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True)
   if gpu.stdout.strip():save('waiting_for_gpu',parent=parent,earlier_reserve=prior);time.sleep(15);continue
   assert not R.exists();save('launching_once',parent=parent,earlier_reserve=prior)
   with (P/'producer.log').open('x') as log:child=subprocess.Popen([sys.executable,plan['launch_script']],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   child_id=identity(child.pid);assert child_id is not None
   launch=dict(created_at_utc=now(),producer_pid=child.pid,producer_start=child_id['start'],queue_pid=os.getpid(),target=str(R),plan_sha256=sha(P/'LAUNCH_QUEUE_PLAN.json'),training_ready=False)
   with (P/'LAUNCH.json').open('x') as f:json.dump(launch,f,indent=2)
   while child.poll() is None and not (R/'PROTOCOL.json').exists():time.sleep(2)
   assert (R/'PROTOCOL.json').exists(),('launch failed without retry',child.poll())
   protocol=read(R/'PROTOCOL.json');assert protocol['producer_pid']==child.pid and protocol['plan']==read(P/'PLAN.json');save('launched_once',launch=launch,protocol_sha256=sha(R/'PROTOCOL.json'));return
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
 if args.prepare:print(json.dumps(prepare(),indent=2))
 else:main()
