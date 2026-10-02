"""Screen a causal +X recovery request against existing measured contact constraints.
All original rear trajectories are included, with ineligible states counted.
Uses recorded states, not counterfactual physics. No commands are executed or
training data admitted. Positive reference direction does not prove object motion.
"""
from pathlib import Path
import json, hashlib, datetime, collections
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
finding=json.loads((W/'REAR_CORRIDOR_LOSS_FINDINGS.json').read_text())
results=[];sources={str(W/'REAR_CORRIDOR_LOSS_FINDINGS.json'):sha(W/'REAR_CORRIDOR_LOSS_FINDINGS.json')}
for item in finding['episodes']:
 ep=W/item['episode'];fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan']
 key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1
 assert not plan.get('front_route_selected') and not plan.get('initial_top_selected') and plan['margin']==.02
 with np.load(ep/'trace.npz') as z:target=z[key].copy();obstacle=z[other].copy()
 with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
 rad={k:abs(rot[k])@sizes[k]/2 for k in sizes};core=np.array(plan['rear_cop_centering']['actual_core_size_xyz'])
 rows={r['step']:r for r in fr['rows']};counts=collections.Counter();details=[]
 for t,r in rows.items():
  if t>=len(target):continue
  counts['all_control_rows']+=1
  if not r['mode'].startswith('top_'):counts['pre_top_rows']+=1;continue
  needed_x=obstacle[t,0]+rad[other][t,0]+rad[key][t,0]+.02
  pending=direction*(target[t,1]-obstacle[t,1])<=rad[key][t,1]+rad[other][t,1]+.02
  if not pending or target[t,0]>=needed_x:counts['no_recovery_required']+=1;continue
  counts['corridor_deficit']+=1
  if r['mode']!='top_push':counts['original_non_push_preserved']+=1;continue
  feedback=r.get('rear_cop_centering',{})
  if not feedback.get('override'):counts['original_contact_guard_or_first_load_preserved']+=1;continue
  # Original parent eligibility includes valid previous solved contact >=0.3N.
  assert feedback['reason']=='loaded_rear_transverse_centering' and t-1 in rows
  prev=np.array(rows[t-1]['target_xyz']);parent=np.array(r['target_xyz']);ref=np.array(r['observed_support_xyz']);R=rot[key][t]
  cop=R.T@(np.array(feedback['cop_world'])-target[t]);near=np.flatnonzero(core[:2]/2-abs(cop[:2])<.010)
  current_table=min(target[t,0]-rad[key][t,0]-.28,.88-target[t,0]-rad[key][t,0],target[t,1]-rad[key][t,1]+.75,.75-target[t,1]-rad[key][t,1])
  table_ok=current_table>=.005 and needed_x+rad[key][t,0]<=.875
  if not table_ok:counts['table_guard_required']+=1;continue
  # Hold the last emitted Y; preserve parent Z and existing X slew/lead bounds.
  low=max(0.,ref[0]-.030-prev[0]);high=min(.002,ref[0]+.030-prev[0],needed_x-target[t,0])
  a=[];b=[]
  for axis in near:
   sign=1. if cop[axis]>=0 else -1.
   a.append(sign*R[0,axis]);b.append(-sign*R[2,axis]*(parent[2]-prev[2]))
  lo,hi=low,high
  for coef,rhs in zip(a,b):
   if abs(coef)<1e-12:
    if rhs < -1e-12:lo,hi=1.,0.
   elif coef>0:hi=min(hi,rhs/coef)
   else:lo=max(lo,rhs/coef)
  feasible=bool(lo<=hi+1e-12)
  lp=None if low>high else linprog([-1.],A_ub=np.array(a).reshape(-1,1) if a else None,b_ub=np.array(b) if b else None,bounds=[(low,high)],method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
  assert feasible==(lp is not None and lp.success),(ep,t,lo,hi,lp)
  if feasible:assert abs(hi-lp.x[0])<1e-8,(ep,t,hi,lp.x)
  positive=bool(feasible and hi>=.0001)
  counts['eligible_loaded_recovery_requests']+=1
  counts['positive_X_reference_at_least_0p1mm' if positive else 'requires_recontact_or_new_direction']+=1
  if positive:
   delta=np.array([hi,0.,parent[2]-prev[2]])
   assert abs(delta[0])<=.002+1e-12 and abs(prev[0]+delta[0]-ref[0])<=.030+1e-12
   assert all(np.sign(cop[i])*(R.T@delta)[i]<=1e-10 for i in near)
  details.append(dict(step=t,rear_gap_mm=float((target[t,0]-obstacle[t,0]-rad[key][t,0]-rad[other][t,0])*1000),near_core_axes=near.tolist(),feasible=feasible,max_reference_dx_mm=float(hi*1000) if feasible else None,positive_X_reference=positive,analytic_interval_m=[float(lo),float(hi)],lp_crosscheck=True))
 results.append(dict(episode=item['episode'],original_task_passed=item['task_passed'],counts=dict(counts),first_eligible=details[0] if details else None,key_frames=[d for d in details if d['step'] in [224,699,1052]],rows=details))
 for name in ['frontal_bypass.json','trace.npz','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=results,source_sha256=sources,analyzer_sha256=sha(__file__),training_ready=False,limitations=['Fixed observed streams; no predicted contact or physical counterfactual','Not a full joint-space feasibility test','Mode/recontact/first-load guards retained; new route recovery still needs actual controller integration and independent full audits','0.1mm is a diagnostic reporting threshold, not a relaxed quality or safety gate'])
p=W/'REAR_CORRIDOR_RECOVERY_DIRECTION_SCREEN.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([{k:v for k,v in r.items() if k!='rows'} for r in results],indent=2))
