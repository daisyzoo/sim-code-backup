"""Compare complete real loaded transitions; never changes control/data gates."""
from pathlib import Path
import json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;records=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for run in ['tracking_region_groups_r1','region_continuity_groups_r1']:
 ep=w/run/'case_840004/layout_840004_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];by={r['step']:r for r in fr};rows=[]
 for r in fr:
  t=r['step'];prev=by.get(t-1)
  if not prev or r['mode']!='top_push' or prev['mode']!='top_press':continue
  end=t
  while end+1 in by and by[end+1]['mode']=='top_push':end+=1
  rows.append(dict(step=t,push_frames=end-t+1,command_delta_xyz_m=(np.asarray(r['target_xyz'])-prev['target_xyz']).tolist(),measured_tracking_before_xyz_m=(np.asarray(r['observed_support_xyz'])-prev['target_xyz']).tolist(),initial_load_n=r['contact_load']['observed_vertical_load_n'],next_load_n=by[t+1]['contact_load']['observed_vertical_load_n'],first_samples=[dict(step=by[k]['step'],command_xyz=by[k]['target_xyz'],support_xyz=by[k]['observed_support_xyz'],surface_xyz=by[k]['parcel_top_xyz'],fixed_push_x_anchor_m=by[k]['push_x_anchor_m'],observed_load_n=by[k]['contact_load']['observed_vertical_load_n']) for k in range(t,min(end+1,t+8))],next_recontact_reason=by[end+1]['last_recontact_reason'] if end+1 in by else None))
 records.append(dict(run=run,episode=ep.name,quality=json.loads((ep/'quality.json').read_text()),transitions=rows,total_top_push_frames=sum(x['push_frames'] for x in rows),next_frame_loaded_transitions=sum(x['next_load_n']>.3 for x in rows),source_sha256={f:sha(ep/f) for f in ['raw.npz','frontal_bypass.json','quality.json']}))
a=dict(records=records,script_sha256=sha(Path(__file__)),scope='Two full development rollouts; commanded switch and measured next contact only. Candidate changed height margin and switch XY, not a single-variable experiment. Last solved substep loads, not integrated impulse. No unobserved new-controller response inferred.',training_ready=False)
(w/'region_continuity_groups_r1/LOADED_TRANSITION_COMPARISON.json').write_text(json.dumps(a,indent=2));print([{k:r[k] for k in ['run','total_top_push_frames','next_frame_loaded_transitions']} for r in records])
