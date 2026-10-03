"""Close current candidate only after exact original and supplement watchers exit.
Never marks unseen images reviewed, retries failed collection, waives task or
control failures, or admits diagnostic episodes to training.
"""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time
W=Path(__file__).resolve().parent; C=W/'front_initial_physical_r1'
from front_initial_stage_run_contract import primary, controls, ADDITIONAL
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  stat=(p/'stat').read_text().split();cmd=(p/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:return None
 return dict(start=stat[21],state=stat[2],cmd=[x.decode() for x in cmd if x])
def save(status,**kw):
 p=C/'CLOSURE_QUEUE_STATUS.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2));t.replace(p)
def main():
 lock=os.open(C/'CLOSURE_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(lock,str(os.getpid()).encode());os.close(lock)
 assert not (C/'RESULT.json').exists() and not (C/'RESULT_WITH_REGION_SUPPLEMENT.json').exists()
 protocol=read(C/'PROTOCOL.json');numeric=read(C/'NUMERIC_VISUAL_SUMMARY.json');collection=read(C/'STATUS.json')
 assert collection['completed_conditions']==10 and collection['status']=='collection_complete_audits_visual_pending'
 assert len(numeric['rows'])==10
 frozen={str(C/'NUMERIC_VISUAL_SUMMARY.json'):sha(C/'NUMERIC_VISUAL_SUMMARY.json')}
 for row in numeric['rows']:
  ep=next(C.glob('case_*/'+row['episode']))
  for name,key in [('ACTUAL_REVIEW_BINDING.json','actual_review_sha256'),('FRONT_INITIAL_STAGE_NUMERIC_REVIEW.json','numeric_sha256')]:
   assert sha(ep/name)==row[key];frozen[str(ep/name)]=row[key]
 expected=0
 for item in protocol['plan']['commands']:
  for task in item['tasks']:
   ep=C/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";scripts=primary(item['wait'])+['audit_front_initial_stage_contacts.py','audit_front_initial_stage_pressure.py']
   if not item['wait']:scripts+=controls(read(ep/'frontal_bypass.json')['plan'])+ADDITIONAL
   scripts+=['audit_front_initial_stage_release.py'];expected+=len(dict.fromkeys(scripts))
 for p in [Path(__file__),W/'front_initial_stage_run_contract.py',W/'close_front_initial_physical.py',W/'close_front_initial_with_region_supplement.py']:frozen[str(p)]=sha(p)
 watchers={}
 for name,script in [('AUDIT_STATUS.json','watch_front_initial_physical_audits.py'),('REGION_SUPPLEMENT_STATUS.json','watch_front_initial_region_supplement.py')]:
  state=read(C/name);info=identity(state['pid']);assert state['status'] in ('running','complete')
  if info is not None and info['state']!='Z':assert str(W/script) in info['cmd'] and str(C) in info['cmd']
  else:assert state['status']=='complete'
  watchers[name]=dict(pid=state['pid'],identity=info)
 started=time.monotonic()
 while True:
  for p,h in frozen.items():assert sha(p)==h,p
  done=True;states={}
  for name,watch in watchers.items():
   state=read(C/name);info=identity(watch['pid']);assert state['pid']==watch['pid'] and state['status'] in ('running','complete'),state
   if info is not None and info['state']!='Z':
    assert watch['identity'] is not None and info['start']==watch['identity']['start'] and info['cmd']==watch['identity']['cmd'];done=False
   else:assert state['status']=='complete','watcher exited before complete evidence'
   states[name]=state
  if done:break
  assert time.monotonic()-started<21600,'Timeout; retain evidence and stop without retry'
  save('waiting_for_exact_original_and_supplement_watchers',expected_original_audits=expected,audit_rows=len(states['AUDIT_STATUS.json']['rows']),supplement_rows=len(states['REGION_SUPPLEMENT_STATUS.json']['rows']),watchers=watchers,frozen_sha256=frozen)
  time.sleep(10)
 assert len(states['AUDIT_STATUS.json']['rows'])==expected and len(states['AUDIT_STATUS.json']['completed_episodes'])==10
 assert len(states['REGION_SUPPLEMENT_STATUS.json']['rows'])==8
 for script in ['close_front_initial_physical.py','close_front_initial_with_region_supplement.py']:
  save('closing_reports',script=script)
  with (C/(script+'.closure.log')).open('x') as f:subprocess.run([sys.executable,str(W/script),str(C),'--apply'],cwd=W.parents[1],stdout=f,stderr=subprocess.STDOUT,check=True)
 result=read(C/'RESULT_WITH_REGION_SUPPLEMENT.json');assert result['conditions']==10 and result['push_passed']==numeric['push_passed'] and result['wait_passed']==numeric['wait_passed']
 save('closed_original_and_separate_supplement_reports',original_result_sha256=sha(C/'RESULT.json'),supplement_result_sha256=sha(C/'RESULT_WITH_REGION_SUPPLEMENT.json'),unresolved_audits=result['unresolved_audits'],push_passed=result['push_passed'],wait_passed=result['wait_passed'])
if __name__=='__main__':
 try:main()
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
