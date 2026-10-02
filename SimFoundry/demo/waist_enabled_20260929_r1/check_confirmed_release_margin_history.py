"""Audit the release-margin bypass and screen a stricter observer on real history.
Original policy quality labels unchanged. No observations after the first changed
release decision constitute a counterfactual rollout of this candidate.
"""
from pathlib import Path
import json,hashlib,datetime,sys,collections,math
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease as Old
from margin_confirmed_position_release import ConfirmedPositionRelease as New
from simfoundry.data.reach_sweep import ready_to_release
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'CONFIRMED_RELEASE_MARGIN_HISTORY_CHECK.json';assert not dest.exists();rows=[];sources={}
for run in ['fresh_closed_peak_trials_r1','rear_transport_retry_physical_r1']:
 for ep in sorted((W/run).glob('case_*/layout_*')):
  if not (ep/'frontal_bypass.json').exists():continue
  fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];initial=plan['initial_target_xyz'][1];direction=plan['direction'];old=Old(initial,direction);new=New(initial,direction);ind=collections.deque(maxlen=10);first_changed=None;release=None;count=0
  for r in fr['rows']:
   if 'terminal_position_confirmed' not in r:continue
   xyz=r['observed_target'];a=old.observe(xyz);b=new.observe(xyz);ind.append(tuple(xyz));assert a is bool(r['terminal_position_confirmed']),(ep.name,r['step'],a,r['terminal_position_confirmed']);independent=(len(ind)==10 and direction*(xyz[1]-initial)>=.15 and all(direction*p[1]>=.20 for p in ind) and math.hypot(xyz[0]-ind[0][0],xyz[1]-ind[0][1])<=.01 and direction*xyz[1]>=max(.205,direction*initial+.16));assert b==independent;assert not b or a;count+=1
   if a and not b and first_changed is None:first_changed=dict(step=r['step'],measured_signed_y_mm=direction*xyz[1]*1000,measured_progress_mm=direction*(xyz[1]-initial)*1000,old_confirmed=True,new_confirmed=False)
   if r['mode']=='top_release' and release is None:release=dict(step=r['step'],reason=r.get('release_reason'),measured_progress_mm=direction*(xyz[1]-initial)*1000,measured_signed_y_mm=direction*xyz[1]*1000,original_ready_to_release=ready_to_release(initial,xyz[1],direction),confirmed_flag=a)
  quality=json.loads((ep/'quality.json').read_text());rows.append(dict(run=run,episode=ep.name,frames=quality['frames'],original_quality_passed=quality['passed'],first_changed_confirmation=first_changed,first_actual_release=release,observations_checked=count))
  for name in ['frontal_bypass.json','quality.json']:sources[str(ep/name)]=sha(ep/name)
assert sum(r['run']=='fresh_closed_peak_trials_r1' for r in rows)==48
out=dict(status='complete',passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,episodes=len(rows),original_confirmation_rows_reproduced=sum(r['observations_checked'] for r in rows),actual_confirmed_releases_bypassing_original_margin=sum(bool(r['first_actual_release'] and r['first_actual_release']['reason']=='confirmed_original_target_position' and not r['first_actual_release']['original_ready_to_release']) for r in rows),source_sha256=sources,code_sha256={str(p):sha(p) for p in [Path(__file__),W/'margin_confirmed_position_release.py',ROOT/'simfoundry/data/confirmed_position_release.py',ROOT/'simfoundry/data/reach_sweep.py']},physics=False,training_ready=False,remaining='Explicit collector/audit source-bound selection and fixed paired physical comparison. Do not relabel149.994mm as success.')
with dest.open('x') as f:json.dump(out,f,indent=2)
print({k:v for k,v in out.items() if k not in ['rows','source_sha256','code_sha256','scope']})
