"""Prepare exact original numeric reviews and image sheets once per ready episode.
Never mark images viewed, close audits, admit data, train, or retry a failed
review. Wait for the already authorized exact queued run; no physics launch.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_contact_window_physical_preparation_r1';R=W/'front_contact_window_physical_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(start=st[19],state=st[0],cmd=(p/'cmdline').read_bytes().split(b'\0')[:-1])
 except FileNotFoundError:return None

def selection(marker):
 n=marker['executed_frames'];expected=70 if marker['wait'] else 1200
 assert type(n) is int and marker['requested_frames']==expected and 1<n<=expected
 if n<expected:
  assert not marker['wait'] and marker['quality_passed'] is False
  return 'review_front_contact_window_trial1_incomplete_episode.py','FRONT_CONTACT_WINDOW_R1_INCOMPLETE_REVIEW.json','FRONT_CONTACT_WINDOW_R1_INCOMPLETE_REVIEW.jpg'
 return 'review_front_contact_window_trial1_v1_stage_episode.py','FRONT_CONTACT_WINDOW_R1_V1_STAGE_NUMERIC_REVIEW.json','FRONT_CONTACT_WINDOW_R1_REVIEW.jpg'

def verify_marker(marker,ep):
 assert marker['episode']==ep.name and marker['training_ready'] is False
 assert str(ep/'raw.npz') in marker['source_sha256']
 for name,h in marker['source_sha256'].items():assert sha(name)==h,name

def check():
 plan=read(P/'PLAN.json');assert len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 markers=read(W/'front_initial_physical_r1/COLLECTION_EXECUTION.json');assert len(markers)==10
 routes=[selection(m)[0] for m in markers];assert routes.count('review_front_contact_window_trial1_v1_stage_episode.py')==10
 push=next(m for m in markers if not m['wait']);short=dict(push,executed_frames=300,quality_passed=False);assert selection(short)[0]=='review_front_contact_window_trial1_incomplete_episode.py'
 invalid=[dict(short,quality_passed=True),dict(short,executed_frames=0),dict(short,executed_frames=1201),dict(short,requested_frames=1199),dict(short,wait=True,requested_frames=70,executed_frames=30)]
 for marker in invalid:
  try:selection(marker)
  except AssertionError:pass
  else:raise AssertionError('invalid marker accepted')
 sources={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',W/'review_front_contact_window_trial1_v1_stage_episode.py',W/'review_front_contact_window_trial1_incomplete_episode.py']}
 return dict(passed=True,original_complete_marker_routes=10,synthetic_short_route_checked=True,invalid_marker_rejections=len(invalid),source_sha256=sources,physical_review_executed=False,actual_visual_review=False,training_ready=False)

def main():
 result=check();fd=os.open(P/'NUMERIC_REVIEW_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 (P/'NUMERIC_REVIEW_QUEUE_CHECK.json').write_text(json.dumps(result,indent=2));frozen=result['source_sha256'];records=[];started=time.monotonic()
 def save(status,**kw):
  dest=P/'NUMERIC_REVIEW_QUEUE_STATUS.json';tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_reviews=len(records),rows=records,actual_visual_review='pending',training_ready=False,**kw),indent=2));tmp.replace(dest)
 try:
  protocol=read(R/'PROTOCOL.json');assert protocol['plan']==read(P/'PLAN.json')
  for name,h in frozen.items():assert protocol['frozen_files_sha256'][name]==h
  producer_id=identity(protocol['producer_pid']);assert producer_id is not None and str(W/'run_front_contact_window_trial1_physical_r2.py').encode() in producer_id['cmd']
  env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1')
  while True:
   for name,h in frozen.items():assert sha(name)==h,name
   done={r['episode'] for r in records}
   for item in protocol['plan']['commands']:
    for task in item['tasks']:
     ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";ready=ep/'READY_FOR_AUDIT.json'
     if ep.name in done or not ready.exists():continue
     marker=read(ready);verify_marker(marker,ep);script,report,sheet=selection(marker)
     assert not (ep/report).exists() and not (ep/sheet).exists(),'review output already exists; no adoption/retry'
     save('reviewing',current_episode=ep.name,reviewer=script)
     log=ep/'NUMERIC_REVIEW_QUEUE_EXECUTION.log'
     with log.open('x') as f:completed=subprocess.run([sys.executable,str(W/script),str(ep)],cwd=ROOT.parent,env=env,stdout=f,stderr=subprocess.STDOUT)
     assert completed.returncode==0,('review failed',ep.name,completed.returncode)
     verify_marker(marker,ep);r=read(ep/report);assert r['actual_visual_review']=='pending' and r['training_ready'] is False
     assert r['reviewer_sha256']==frozen[str(W/script)] and r['raw_sha256']==sha(ep/'raw.npz') and r['review_sheet_sha256']==sha(ep/sheet)
     if marker['executed_frames']<marker['requested_frames']:assert r['original_task_and_pose_passed'] is False and r['short_attempt_cannot_pass'] is True
     records.append(dict(episode=ep.name,requested_frames=marker['requested_frames'],executed_frames=marker['executed_frames'],original_task_and_pose_passed=r['original_task_and_pose_passed'],actual_visual_review='pending',training_ready=False,source_sha256={str(p):sha(p) for p in [ready,log,ep/report,ep/sheet,ep/'raw.npz']}));save('waiting_for_ready_episodes')
   if len(records)==10:save('numeric_reviews_complete_actual_visual_pending');return
   if (R/'STATUS.json').exists():
    state=read(R/'STATUS.json');assert state['status']!='runtime_or_audit_failed',state
    info=identity(protocol['producer_pid'])
    if info is None or info['state']=='Z':assert state['status']=='collection_complete_audits_visual_pending','producer ended before full collection'
    elif producer_id is not None:assert info['start']==producer_id['start'] and info['cmd']==producer_id['cmd']
   # Continue while the exact producer is alive; liveness/status checks above remain mandatory.
   time.sleep(10)
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
 if args.check_only:print(json.dumps(check(),indent=2))
 else:main()
