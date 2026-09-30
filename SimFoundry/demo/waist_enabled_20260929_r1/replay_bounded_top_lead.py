"""Unexecuted waypoint comparison on fixed completed poses, not a rollout."""
from pathlib import Path
from types import SimpleNamespace as NS
import json,sys,hashlib
import numpy as np
from bounded_top_lead_candidate import BoundedTopLead,route_goal
root=Path(__file__).resolve().parent;p=Path(sys.argv[1]).resolve();d=json.loads((p/'frontal_bypass.json').read_text());plan=d['plan'];side='right' if 'push_box' in p.name else 'left';key='box' if side=='right' else 'mailer'
with np.load(p/'trace.npz') as z:positions=z[key].copy()
cal={x['step']:x for x in json.loads((p/'contact_center_calibration.json').read_text())['rows']};state=NS(rear=NS(plan=plan),route_report=plan.get('front_route_candidates'));results=[]
for lead in (.012,.024,.030):
 helper=BoundedTopLead(lead);records=[];protected=0
 for row in d['rows']:
  t=row['step'];goal=route_goal(state,row)
  if goal is None or not cal[t]['calibrated_after']:
   helper.previous=None;protected+=1;continue
  out=helper.update(row['mode'],positions[t,:2],goal,row['observed_support_xyz'][:2]);records.append(dict(step=t,route_stage=row.get('route_stage'),current_command_xy=row['target_xyz'][:2],actual_command_lead_xy_m=(np.asarray(row['target_xyz'][:2])-positions[t,:2]).tolist(),**out))
 results.append(dict(lead_m=lead,frames=len(records),protected_or_uncalibrated_unchanged=protected,max_desired_axis_lead_m=max(max(abs(r['desired_xy'][i]-positions[r['step'],i]) for i in (0,1)) for r in records),max_candidate_command_axis_lead_m=max(max(abs(v) for v in r['command_relative_object_xy_m']) for r in records),max_recorded_command_axis_lead_m=max(max(abs(v) for v in r['actual_command_lead_xy_m']) for r in records),max_slew_m=max(max(abs(r['command_xy'][i]-r['previous_xy'][i]) for i in (0,1)) for r in records),records=records))
out=dict(results=results,source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ('raw.npz','trace.npz','frontal_bypass.json','contact_center_calibration.json')},helper_sha256=hashlib.sha256((root/'bounded_top_lead_candidate.py').read_bytes()).hexdigest(),scope='Shadow waypoints on unchanged measured object/hand poses. Three lead values are hypothesis checks, not measured performance; historic12mm offset-anchor candidate stalled with a different reference/controller. No collector integration, changed simulation, guaranteed realized contact/lead or data admission.',training_ready=False)
(p/'BOUNDED_TOP_LEAD_SHADOW.json').write_text(json.dumps(out,indent=2));print(p.name,json.dumps([{k:v for k,v in r.items() if k!='records'} for r in results],indent=2))
