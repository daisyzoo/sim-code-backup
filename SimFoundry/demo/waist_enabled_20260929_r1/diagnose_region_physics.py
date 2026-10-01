"""Read complete region rollout; distinguish planned q and next measured q."""
from pathlib import Path
import json,sys,hashlib,collections
import numpy as np
p=Path(sys.argv[1]);assert (p/'quality.json').exists();rows=json.loads((p/'region_approach.json').read_text())['rows'];by={x['step']:x for x in rows};fr={x['step']:x for x in json.loads((p/'frontal_bypass.json').read_text())['rows']};quality=json.loads((p/'quality.json').read_text());coordinates={x['step']:x for x in json.loads((p/'coordination.json').read_text())}
with np.load(p/'raw.npz') as raw:q=raw['q'].copy();action=raw['action'].copy()
first=next((x for x in rows if x['abort_reason']),None);overrides=[x for x in rows if x['solver'] and x['solver'].get('joint_override')];events=[]
interesting=set()
if first:interesting.update(range(max(1,first['step']-5),min(len(q),first['step']+4)))
if overrides:interesting.add(overrides[0]['step'])
for t in sorted(interesting):
 r=by[t];s=r['solver'];prev=by.get(t-1,{}).get('solver');f=fr[t];co=coordinates[t]
 e=dict(step=t,mode=r['mode'],active=r['active'],abort_reason=r['abort_reason'],solver=s,observed_support_xyz=f.get('observed_support_xyz'),physical_support_xyz=f.get('observed_physical_support_xyz'),target_xyz=f.get('observed_target'),contact_load=f.get('contact_load'),selected_surface_local_xy=r['selected_surface_local_xy'],current_upper_q=q[t,12:23].tolist(),actual_upper_action=action[t,12:23].tolist())
 if prev and prev.get('joint_override'):
  error=q[t,12:23]-np.asarray(prev['next_q']);e.update(previous_proposal_tracking_error_rad=error.tolist(),max_previous_proposal_tracking_error_rad=float(np.max(abs(error))),previous_executed_tracking_error_rad=(q[t,12:23]-action[t-1,12:23]).tolist(),previous_slew_adjustment_rad=(action[t-1,12:23]-np.asarray(prev['next_q'])).tolist())
 events.append(e)
load=json.loads((p/'solved_contact_forces.json').read_text());packets=[x for x in load['rows'] if first and first['step']-3<=x['after_action_step']<=first['step']]
report=dict(episode=p.name,quality=quality,region_rows=len(rows),mode_counts=dict(collections.Counter(x['mode'] for x in rows)),overridden_steps=len(overrides),first_override_step=overrides[0]['step'] if overrides else None,first_abort=first,handover_steps=[x['step'] for x in overrides if x['solver'].get('handover')],event_rows=events,near_event_solved_packets=packets,source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ['raw.npz','region_approach.json','coordination.json','frontal_bypass.json','quality.json','solved_contact_forces.json']},scope='Complete actual trace around first region abort; candidate q and actual next-step tracking distinguished. Source, task/pose and actual visuals remain separate. No success inferred from ideal FK.',training_ready=False)
(p/'REGION_PHYSICS_DIAGNOSIS.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['event_rows','near_event_solved_packets','source_sha256']},indent=2))
