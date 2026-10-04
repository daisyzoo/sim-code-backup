"""Verify uninstalled10mm endpoint candidate on recorded reset geometry and boundary cases.
No physical, arm, reach, contact or training success inferred from object envelopes.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from tabletop_endpoint_headroom_candidate_v1 import candidate_routes
from simfoundry.data.tabletop_route_candidates import tabletop_route_candidates
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());rows=[];sources={str(Path(__file__)):sha(Path(__file__))};headroom=.01
for ep in sorted((W/'front_loaded_z_quarter_physical_r2').glob('case_*/layout_*')):
 if 'wait_no_package' in ep.name:continue
 fr=read(ep/'frontal_bypass.json');plan=fr['plan'];right='push_box' in ep.name;target='box' if right else 'mailer';other='mailer' if right else 'box';size=(.14,.09,.045) if right else (.15,.145,.04);other_size=(.15,.145,.04) if right else (.14,.09,.045)
 with np.load(ep/'parcel_orientation.npz',allow_pickle=False) as z:tq=z[target][0].tolist();oq=z[other][0].tolist()
 margin=.012 if plan.get('front_route_selected') else .02;args=[plan['initial_target_xyz'],plan['obstacle_initial_xyz'],size,other_size,tq,oq,-1 if right else 1,margin];saved=copy.deepcopy(args)
 parent=tabletop_route_candidates(*args);off=candidate_routes(*args);on=candidate_routes(*args,endpoint_headroom_m=headroom);assert args==saved and off==parent
 # Bind the actual initial envelope when that route was selected.
 if plan.get('initial_top_selected'):
  expected=plan['initial_top_proposal'];assert parent['goal_y']==expected['goal_y'];assert next(x for x in parent['candidates'] if x['route']=='direct')==expected['direct_envelope']
 elif plan.get('front_route_selected'):
  expected=plan['front_route_candidates']
  for key in ['goal_y','candidates','target_radii_xy','other_radii_xy']:assert parent[key]==expected[key],(ep.name,key)
 assert abs((on['goal_y']-parent['goal_y'])*args[6]-headroom)<1e-12
 rows.append(dict(episode=ep.name,defaultoff_exact=True,reset_geometry_bound=bool(plan.get('initial_top_selected') or plan.get('front_route_selected')),headroom_m=headroom,original_goal=parent['goal_y'],candidate_goal=on['goal_y'],routes=[dict(route=a['route'],original_eligible=a['object_envelope_eligible'],candidate_eligible=b['object_envelope_eligible'],candidate_separation_m=b['min_object_axis_separation_m'],candidate_table_margin_m=b['target_table_margin_m']) for a,b in zip(parent['candidates'],on['candidates'])]))
 for p in [ep/'frontal_bypass.json',ep/'parcel_orientation.npz']:sources[str(p)]=sha(p)
assert len(rows)==8
boundary=[]
for direction in [-1,1]:
 for kind in ['table','other_object']:
  if kind=='table':args=[[.45,direction*.51,.77],[.8,-direction*.4,.77],[.15,.145,.04],[.14,.09,.045],[0,0,0,1],[0,0,0,1],direction,.02]
  else:args=[[.45,0,.77],[.45,direction*.32,.77],[.14,.09,.045],[.14,.09,.045],[0,0,0,1],[0,0,0,1],direction,.02]
  old=next(x for x in candidate_routes(*args)['candidates'] if x['route']=='direct');new=next(x for x in candidate_routes(*args,endpoint_headroom_m=headroom)['candidates'] if x['route']=='direct');assert old['object_envelope_eligible'] and not new['object_envelope_eligible'];boundary.append(dict(direction=direction,kind=kind,original=old,extended=new))
negative=[]
for value in [True,False,float('nan'),float('inf'),-.001,.020001]:
 try:candidate_routes(*args,endpoint_headroom_m=value)
 except ValueError:negative.append(repr(value))
 else:raise AssertionError('Invalid headroom accepted')
for p in [W/'tabletop_endpoint_headroom_candidate_v1.py',ROOT/'simfoundry/data/tabletop_route_candidates.py',ROOT/'simfoundry/data/top_contact_bypass.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,boundary_rejections=boundary,invalid_parameter_rejections=negative,source_sha256=sources,headroom_m=headroom,original_release_and_geometry_thresholds_unchanged=True,installed=False,physical_success_proven=False,robot_clearance_proven=False,training_ready=False)
p=W/'endpoint_headroom_candidate_r1';p.mkdir(exist_ok=False)
with (p/'GEOMETRY_CHECK_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,actual_resets=len(rows),boundary_rejections=len(boundary),invalid_parameter_rejections=len(negative),installed=False)))
