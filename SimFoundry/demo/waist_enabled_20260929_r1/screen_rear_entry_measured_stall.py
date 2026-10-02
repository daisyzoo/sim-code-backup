"""First causal entry screen on every original rear-selected baseline.
Adds 30 consecutive actually executed parent top_push observations in the same
contact bout, positive measured/filtered load throughout, and <0.1mm target
progress over the past30 actions. Does not execute or validate a changed policy.
The future30 result is separately labelled descriptive, never an input.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;dest=W/'REAR_ENTRY_MEASURED_STALL_SCREEN.json';assert not dest.exists();B=W/'fresh_closed_peak_trials_r1';source=W/'REAR_RECOVERY_TRIGGER_SPECIFICITY.json';d=json.loads(source.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={str(source):sha(source)};outrows=[]
for summary in d['rows']:
 if not summary['rear_selected']:continue
 ep=next(B.glob('case_*/'+summary['episode']));fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};key='box' if 'push_box' in ep.name else 'mailer';direction=-1 if key=='box' else 1
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 trigger=None;eligible_count=0
 for t in summary['all_trigger_steps']:
  if t<31:continue
  history=[fr.get(j) for j in range(t-30,t+1)];current=fr[t]
  eligible=all(h is not None and h['mode']=='top_push' and h['recontacts']==current['recontacts'] and not h.get('route_stop_reason') and not h.get('release_reason') and h.get('contact_load',{}).get('observed_vertical_load_n',0)>0 and h.get('contact_load',{}).get('filtered_vertical_load_n',0)>0 for h in history)
  if not eligible:continue
  eligible_count+=1;progress=direction*(xyz[t,1]-xyz[t-30,1])
  if progress>=.0001:continue
  end=min(t+30,len(xyz)-1)
  trigger=dict(step=t,previous_actions=[t-30,t-1],same_contact_bout=current['recontacts'],past30_signed_y_mm=float(progress*1000),descriptive_future30_signed_y_mm=float(direction*(xyz[end,1]-xyz[t,1])*1000),future_frames=end-t);break
 outrows.append(dict(episode=ep.name,original_quality_passed=summary['original_quality_passed'],original_first_trigger=summary['first_trigger'],causal_same_bout_stall_first_trigger=trigger,eligible_prefix_checks=eligible_count))
 for n in ['trace.npz','frontal_bypass.json']:sources[str(ep/n)]=sha(ep/n)
summary=dict(rear_episodes=len(outrows),successful_quality_episodes=sum(r['original_quality_passed'] for r in outrows),original_entry_triggers=sum(r['original_first_trigger'] is not None for r in outrows),causal_stall_triggers=sum(r['causal_same_bout_stall_first_trigger'] is not None for r in outrows),successful_quality_with_stall_trigger=sum(r['original_quality_passed'] and r['causal_same_bout_stall_first_trigger'] is not None for r in outrows))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=outrows,source_sha256=sources,analyzer_sha256=sha(__file__),training_ready=False,physics=False,limitations=['Only first hypothetical trigger is usable; no continuation after a changed command was simulated.','Passing this screen does not establish safe delay: proximity/collision/quality guards would still be required.','Zero triggers in failed initial approaches do not mean those failures are fixed.'])
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(summary));print(json.dumps(outrows,indent=2))
