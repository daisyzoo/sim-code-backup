"""Bind missed within-action load peaks to subsequent recorded pressure feedback.
Observed temporal association only; does not prove an alternative controller works.
"""
from pathlib import Path
import json,sys,hashlib,datetime
import numpy as np
p=Path(sys.argv[1]).resolve();h=json.loads((p/'SUBSTEP_LOAD_HISTORY.json').read_text());fr={r['step']:r for r in json.loads((p/'frontal_bypass.json').read_text())['rows']};events=[]
for row in h['rows']:
 t=row['action_step'];before=fr.get(t,{}).get('contact_load');after=fr.get(t+1,{}).get('contact_load')
 if after is None:continue
 values=row['vertical_load_n'];assert abs(values[-1]-after['observed_vertical_load_n'])<1e-5
 peak=max(values);mean=float(np.mean(values));final=values[-1]
 if peak>10 and final<=.3:
  events.append(dict(action_step=t,mode=fr.get(t,{}).get('mode'),mean_abs_vertical_n=mean,peak_abs_vertical_n=peak,final_abs_vertical_n=final,next_mode=fr[t+1]['mode'],next_filtered_load_n=after['filtered_vertical_load_n'],prior_z_bias_m=None if before is None else before['stored_z_bias_m'],next_z_bias_m=after['stored_z_bias_m'],bias_change_m=None if before is None else after['stored_z_bias_m']-before['stored_z_bias_m'],maximum_substep_tilt_rad=row['max_target_tilt_rad']))
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,events=events,count=len(events),finding='Transient peaks above10N can end with sampled load<=0.3N; the next recorded low-pass pressure feedback may request further negative Z bias. Per-interval mean is also low in these examples, so using the mean alone is not established as a solution.',next_hypothesis_not_implemented='After complete group review, evaluate bounded pressure feedback that considers transient peak and contact loss, rather than increasing tilt threshold. Need preserve original task/non-target/zero/no-assist requirements and compare full groups.',training_ready=False,source_sha256={n:sha(p/n) for n in ['SUBSTEP_LOAD_HISTORY.json','frontal_bypass.json']},script_sha256=sha(__file__))
dest=p/'SUBSTEP_PRESSURE_FEEDBACK_FINDING.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps(events,indent=2))
