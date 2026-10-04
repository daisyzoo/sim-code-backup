"""All original episodes: measured low-load push intervals and actual exits.
Uses last observed action force, not retrospective same-step action results.
No new trigger, source modification, or early-recontact efficacy claim.
"""
from pathlib import Path
import datetime,hashlib,json
W=Path(__file__).resolve().parent;R=W/'front_effective_height_physical_r1';D=W/'front_normal_nondegradation_audit_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={str(Path(__file__)):sha(Path(__file__))};episodes=[]
for p in sorted(R.glob('case_*/layout_*/frontal_bypass.json')):
 data=json.loads(p.read_text());rows=data['rows'];intervals=[];current=[];pushframes=0
 def end_interval(nextrow):
  if not current:return
  intervals.append(dict(start=current[0]['step'],end=current[-1]['step'],length=len(current),observed_load_n=[x['contact_load']['observed_vertical_load_n'] for x in current],exact_zero_count=sum(x['contact_load']['observed_vertical_load_n']==0 for x in current),route_stages=sorted(set(x.get('route_stage','unknown') for x in current)),next_step=None if nextrow is None else nextrow['step'],next_mode=None if nextrow is None else nextrow['mode'],next_recontact_reason=None if nextrow is None else nextrow.get('last_recontact_reason'),directly_exits_to_lost_contact=bool(nextrow is not None and nextrow['mode']!='top_push' and nextrow.get('last_recontact_reason')=='lost_contact')))
  current.clear()
 for row in rows:
  if row['mode']=='top_push':pushframes+=1
  load=row.get('contact_load',{}).get('observed_vertical_load_n')
  low=row['mode']=='top_push' and load is not None and load<.3
  if low:current.append(row)
  else:end_interval(row)
 end_interval(None)
 episodes.append(dict(episode=p.parent.name,pushframes=pushframes,low_load_push_frames=sum(x['length'] for x in intervals),exact_zero_push_frames=sum(x['exact_zero_count'] for x in intervals),low_load_intervals=len(intervals),direct_loss_exits=sum(x['directly_exits_to_lost_contact'] for x in intervals),intervals=intervals));sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=episodes,source_sha256=sources,training_ready=False,physics_started=False,limitations=['Low load can be transient and does not alone require immediate lift.','Not proof that changing hysteresis improves task completion; compare action/contact/COP before changing it.','Original runtime last_recontact_reason persists; only actual mode transitions count as exit evidence.'])
with (D/'LOW_LOAD_TRANSITION_CENSUS_V1.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps([{k:v for k,v in e.items() if k!='intervals'} for e in episodes]))
