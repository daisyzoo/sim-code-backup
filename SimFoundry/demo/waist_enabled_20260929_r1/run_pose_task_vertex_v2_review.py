"""Uniform supplemental math revision over a frozen completed-episode inventory.
Never replaces native reports or group admission. Episodes lacking required
original pose evidence stay explicitly unverified rather than being skipped as
successes. Does not collect, train, alter source, or run concurrently per episode.
"""
from pathlib import Path
import sys,os,json,hashlib,datetime,subprocess
W=Path(__file__).resolve().parent;R=Path(sys.argv[1]).resolve();OUT=R/'POSE_TASK_VERTEX_V2_REVIEW_EXECUTION.json';assert not OUT.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();script=W/'audit_pose_task_optimality_vertices_v2.py';digest=sha(script);helper=W/'support_vertex_stationarity.py';hh=sha(helper);manifest=W/'POSE_TASK_VERTEX_V2_REVISION.json';mh=sha(manifest);episodes=[];rows=[]
for qp in sorted(R.glob('case_*/layout_*/quality.json')):
 if 'wait_no_package' in qp.parent.name:continue
 case=qp.parent.parent
 status=json.loads((case/'STATUS.json').read_text()) if (case/'STATUS.json').exists() else {}
 if status.get('status') not in ['numeric_pass_visual_review_pending','blocked_quality_or_runtime']:continue
 episodes.append(str(qp.parent))
def save(status,**kw):
 data=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),status=status,inventory=episodes,rows=rows,script_sha256=digest,helper_sha256=hh,revision_sha256=mh,scope=__doc__,native_reports_changed=False,training_ready=False,**kw);tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));tmp.replace(OUT)
save('running')
for name in episodes:
 ep=Path(name);assert sha(script)==digest and sha(helper)==hh and sha(manifest)==mh;quality=json.loads((ep/'quality.json').read_text());old=ep/'CLOSED_PEAK_TRIAL_POSE_TASK_OPTIMALITY_AUDIT.json';pose=ep/'CLOSED_PEAK_TRIAL_POSE_LIVE_AUDIT.json';new=ep/'POSE_TASK_OPTIMALITY_VERTEX_V2_AUDIT.json'
 if quality['frames']!=1200 or not old.exists() or not pose.exists() or not json.loads(pose.read_text()).get('passed',False):
  rows.append(dict(episode=ep.name,status='not_eligible_for_supplement',frames=quality['frames'],quality_passed=quality['passed'],native_task_report_present=old.exists(),native_pose_report_present=pose.exists(),passed=False,reason='Incomplete horizon or missing/failed original prerequisite; original rejection retained.'));save('running');continue
 save('running',current_episode=ep.name)
 if not new.exists():
  with (ep/'POSE_TASK_VERTEX_V2_REVIEW.log').open('x') as log:code=subprocess.run([sys.executable,str(script),str(ep)],stdout=log,stderr=subprocess.STDOUT).returncode
 else:code=None
 assert old.exists() and sha(script)==digest and sha(helper)==hh
 if not new.exists():rows.append(dict(episode=ep.name,status='supplement_failed_to_complete',returncode=code,passed=False));save('running');continue
 j=json.loads(new.read_text());assert j['auditor_sha256']==digest and j['vertex_certificate_source_sha256']==hh and j['math_revision_manifest_sha256']==mh and j['frozen_parent_result_sha256']==sha(old)
 for rel,h in j['source_sha256'].items():assert sha(ep/rel)==h
 if code is not None:assert code==(0 if j['passed'] else 1)
 native=json.loads(old.read_text());rows.append(dict(episode=ep.name,status='supplement_complete',passed=j['passed'],quality_passed=quality['passed'],native_passed=native['passed'],native_sha256=sha(old),revised_sha256=sha(new),original_failed_steps=[v['step'] for v in native['errors']],revised_failed_steps=[v['step'] for v in j['errors']],max_kkt_residual=j['max_kkt_residual'],returncode=code));save('running');print(json.dumps(rows[-1]),flush=True)
save('complete',inventoried_episodes=len(episodes),completed_supplements=sum(x['status']=='supplement_complete' for x in rows),supplements_passed=sum(x['passed'] for x in rows));print('complete',len(rows),flush=True)
