"""Measured terminal response and command-goal consistency; no physical causal claim.
Uses completed episodes only. Virtual support motion is explicitly not material slip.
"""
from pathlib import Path
import json,sys,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;R=W/'terminal_margin_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
for ep in sorted((R/'case_840014').glob('layout_*')):
 if not (ep/'quality.json').exists():continue
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy();task=str(z['task_id'])
 assert len(q)==1200
 key='box' if task=='push_box_to_bin' else 'mailer';direction=-1 if key=='box' else 1
 with np.load(ep/'trace.npz') as z:target=z[key].copy()
 d=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in d['rows']};coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};initial=d['plan']['initial_target_xyz'][1];release=[r for r in d['rows'] if r['mode']=='top_release'];goal=direction*max(.205,direction*initial+.16)
 details=[]
 for t in [900,1000,1100,1199]:
  row=rows[t];c=coords[t];feedback=row.get('clearance_feedback');i=c.get('task_inputs');record=dict(step=t,mode=row['mode'],target_y_m=float(target[t,1]),signed_remaining_to_release_mm=1000*direction*(goal-target[t,1]),past30_signed_target_y_mm=1000*direction*float(target[t,1]-target[t-30,1]),past30_target_xy_mm=1000*float(np.linalg.norm(target[t,:2]-target[t-30,:2])),vertical_load_n=row.get('contact_load',{}).get('observed_vertical_load_n'))
  if feedback:
   record.update(feedback_goal_y_m=feedback['object_goal_xy'][1],feedback_goal_equals_release_boundary=abs(feedback['object_goal_xy'][1]-goal)<1e-12,feedback_desired_y_lead_mm=1000*direction*(feedback['desired_support_xy'][1]-row['observed_support_xyz'][1]),feedback_stage=feedback['stage'])
  if i:
   current=np.array(i['current']);command=u[t];J=np.array(i['jacobian']);nominal=J@(command-current)
   record.update(min_nominal_joint_limit_margin_rad=float(np.min(np.minimum(command-i['lower'],np.array(i['upper'])-command))),waist_state_rad=float(q[t,0]),predicted_linear_task_delta=nominal.tolist(),active_task_error=np.array(i['error'])[:3].tolist(),q_tracking_previous_command_max_rad=float(np.max(abs(q[t]-u[t-1]))))
  details.append(record)
 records.append(dict(episode=ep.name,quality_passed=json.loads((ep/'quality.json').read_text())['passed'],release_step=release[0]['step'] if release else None,last_mode=rows[1199]['mode'],final_signed_remaining_to_release_mm=1000*direction*(goal-target[-1,1]),last300_signed_target_gain_mm=1000*direction*float(target[-1,1]-target[-301,1]),samples=details,source_sha256={str(ep/n):sha(ep/n) for n in ['raw.npz','trace.npz','frontal_bypass.json','coordination.json','quality.json']}))
assert len(records)==2
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=records,findings='Both direct-route feedback goals equal the release boundary exactly. Below12mm, desired support lead shrinks with remaining object error; this removes drive as the goal is approached. Bag retains measurable load yet remains short of the new release boundary at horizon. This supports testing bounded minimum directional lead, not relaxing quality/release thresholds. Controller/physical tracking, normal and inactive-arm costs may also matter; no unique friction or reachability cause is proven.',candidate_not_integrated=True,training_ready=False,script_sha256=sha(__file__))
out=R/'TERMINAL_SETTLING_FINDINGS.json';assert not out.exists();out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['scope','rows']},indent=2));print(json.dumps([{k:r[k] for k in ['episode','release_step','last_mode','final_signed_remaining_to_release_mm','last300_signed_target_gain_mm']} for r in records],indent=2))
