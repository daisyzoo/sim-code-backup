"""Actual original3mm regression plus independent1.5mm boundary and metadata checks."""
from pathlib import Path
import json,hashlib,sys,copy,ast
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)];stage=w/'staged_rear_slow_drag';parent=w/'minimum_motion_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
from audit_minimum_motion_rear_xy import reconstruct as original
from audit_slow_drag_rear_xy import reconstruct as revised
from slow_drag_step_contract import verify_declared_step
records=[];sources=[Path(__file__),w/'audit_minimum_motion_rear_xy.py',w/'audit_slow_drag_rear_xy.py',w/'audit_slow_drag_region_continuity.py',w/'slow_drag_step_contract.py',stage/'region_top_contact.py']
for ep in sorted(parent.glob('case_*/layout_*')):
 if not (ep/'frontal_bypass.json').exists():continue
 f=json.loads((ep/'frontal_bypass.json').read_text());plan=f['plan']
 if not plan.get('rear_cop_centering',{}).get('enabled'):continue
 key='box' if 'push_box' in ep.name else 'mailer';region=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next((r['step'] for r in region if r['solver'] and r['solver'].get('handover')),None)
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
 packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 before=original(f['rows'],plan,xyz,quat,packets,key,handover);after=revised(f['rows'],plan,xyz,quat,packets,key,handover);assert before==after and after['passed'],(ep,after['errors'])
 records.append(dict(episode=ep.name,full_rows=len(f['rows']),overrides=after['overrides_checked'],exact3mm_reconstruction_equal=True))
 sources.extend(ep/n for n in ['frontal_bypass.json','region_approach.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json'])
assert len(records)==2
# Exercise each revised Y reconstruction expression independently around both stop boundaries.
formula='base[1] + np.clip(direction * min(0.34, direction * base[1] + drag_step) - base[1], -drag_step, drag_step)'
expressions=[]
for name in ['audit_slow_drag_rear_xy.py','audit_slow_drag_region_continuity.py']:
 matches=[n for n in ast.walk(ast.parse((w/name).read_text())) if isinstance(n,ast.BinOp) and ast.unparse(n)==formula];assert len(matches)==1,name;expressions.append(compile(ast.Expression(matches[0]),name,'eval'))
cases=0
for direction in [-1,1]:
 for y in [-.35,-.34,-.3395,-.2,0.,.2,.3395,.34,.35]:
  for step in [.0015,.003]:
   goal=direction*min(.34,direction*y+step);expected=y+max(-step,min(step,goal-y));base=np.array([0.,y,0.])
   for expr in expressions:assert abs(eval(expr,dict(np=np,base=base,direction=direction,drag_step=step))-expected)<1e-15
   cases+=1
args=dict(rear_slow_drag=True,expert_frontal_top_drag_step_m=.003);meta=dict(rear_slow_drag=True);rejections=[]
for rear in [False,True]:
 plan=dict(top_recontact=dict(drag_step_m=.0015 if rear else .003,continuous_drag=True),rear_cop_centering=dict(enabled=rear),front_route_selected=not rear,initial_top_selected=False)
 assert verify_declared_step(args,plan,meta)==(.0015 if rear else .003)
 for kind in ['flag','raw_flag','global_step','effective_step','nan','bool_step','continuous','route_conflict']:
  a,p,m=copy.deepcopy(args),copy.deepcopy(plan),copy.deepcopy(meta)
  if kind=='flag':a['rear_slow_drag']=False
  elif kind=='raw_flag':m['rear_slow_drag']=False
  elif kind=='global_step':a['expert_frontal_top_drag_step_m']=.0015
  elif kind=='effective_step':p['top_recontact']['drag_step_m']=.003 if rear else .0015
  elif kind=='nan':p['top_recontact']['drag_step_m']=float('nan')
  elif kind=='bool_step':p['top_recontact']['drag_step_m']=True
  elif kind=='continuous':p['top_recontact']['continuous_drag']=False
  elif kind=='route_conflict':
   if not rear:continue
   p['front_route_selected']=True
  try:verify_declared_step(a,p,m)
  except AssertionError:rejections.append([rear,kind])
  else:raise AssertionError(('corruption accepted',rear,kind))
out=dict(passed=True,original_complete_rear_episodes=records,independent_boundary_cases=cases,metadata_corruptions_rejected=rejections,source_sha256={str(p):sha(p) for p in sources},new_physics=False,training_ready=False)
(stage/'RECONSTRUCTION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS complete original3mm episodes',records,'boundary cases',cases,'metadata rejections',len(rejections),flush=True)
