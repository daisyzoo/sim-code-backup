"""One-shot reserve launch after exact parent collection and ten actual reviews.
Never generates visual approval, retries a failed launch, trains or admits data.
Checks original process identities; parent CPU audits can continue concurrently.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,time,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'joint_transport_reserve_physical_preparation_r1';R=W/'joint_transport_reserve_physical_r1';BASE=W/'joint_transport_physical_r1';sys.path[:0]=[str(W),str(ROOT)]
from run_joint_transport_reserve_trial1_physical_r1 import configuration,parent_readiness,identity
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def prepare():
 assert not R.exists();plan,config=configuration();check=read(P/'ORCHESTRATION_CHECK.json');assert check['passed'] and check['parent_inflight_preflight_rejected']
 frozen=dict(check['source_sha256'])
 for name in ['ORCHESTRATION_CHECK.json','CLOSURE_PREPARATION.json']:
  p=P/name;frozen[str(p)]=sha(p)
 for p in [Path(__file__),W/'close_joint_transport_reserve_trial1_physical_v1.py',W/'summarize_joint_transport_reserve_trial1_actual_reviews.py',P/'PLAN.json',P/'CONFIGURATION_CHECK.json']:frozen[str(p)]=sha(p)
 for p,h in frozen.items():assert sha(p)==h,p
 proc=read(BASE/'PROTOCOL.json');audit=read(BASE/'AUDIT_STATUS.json');dependencies=[]
 for pid,script in [(proc['producer_pid'],'run_joint_transport_trial1_physical_r1.py'),(audit['pid'],'watch_joint_transport_trial1_physical_audits_r1.py')]:
  info=identity(pid);assert info is not None and info['state']!='Z' and str(W/script).encode() in info['cmd'];dependencies.append(dict(pid=pid,start=info['start'],script=str(W/script)))
 out=dict(created_at_utc=now(),scope=__doc__,dependencies=dependencies,parent_protocol_sha256=sha(BASE/'PROTOCOL.json'),source_sha256=frozen,launch_script=str(W/'run_joint_transport_reserve_trial1_physical_r1.py'),target=str(R),expected_conditions=10,expected_audits=224,requires_ten_actual_reviews=True,allow_parent_cpu_audit_overlap=True,training_ready=False)
 with (P/'LAUNCH_QUEUE_PLAN.json').open('x') as f:json.dump(out,f,indent=2)
 return out

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
    if info is not None and info['state']!='Z':assert info['start']==dep['start'] and dep['script'].encode() in info['cmd'],'dependency PID replaced'
    elif 'run_joint_transport_trial1' in dep['script']:assert state['status']=='collection_complete_audits_visual_pending','original producer ended early'
    else:assert read(BASE/'AUDIT_STATUS.json')['status']=='complete','original audit ended incomplete'
   ready=parent_readiness()
   if not ready['ready']:
    save('waiting_for_exact_parent_and_actual_reviews',parent=ready);time.sleep(15);continue
   gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True)
   if gpu.stdout.strip():save('waiting_for_gpu',parent=ready);time.sleep(15);continue
   # Runner performs full frozen-source/raw/actual-view/storage verification again before physics.
   assert not R.exists();save('launching_once',parent=ready)
   with (P/'producer.log').open('x') as log:child=subprocess.Popen([sys.executable,plan['launch_script']],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   child_id=identity(child.pid);assert child_id is not None
   launch=dict(created_at_utc=now(),producer_pid=child.pid,producer_start=child_id['start'],queue_pid=os.getpid(),target=str(R),plan_sha256=sha(P/'LAUNCH_QUEUE_PLAN.json'),training_ready=False)
   with (P/'LAUNCH.json').open('x') as f:json.dump(launch,f,indent=2)
   while child.poll() is None and not (R/'PROTOCOL.json').exists():time.sleep(2)
   assert (R/'PROTOCOL.json').exists(),('launch failed without retry',child.poll())
   protocol=read(R/'PROTOCOL.json');assert protocol['producer_pid']==child.pid and protocol['plan']==read(P/'PLAN.json');save('launched_once',**launch,protocol_sha256=sha(R/'PROTOCOL.json'));return
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
 if args.prepare:print(json.dumps(prepare(),indent=2))
 else:main()
