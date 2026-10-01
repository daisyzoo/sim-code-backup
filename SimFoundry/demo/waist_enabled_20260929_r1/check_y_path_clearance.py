"""Isolated candidate against actual known failure and separated-path records."""
from pathlib import Path
import sys,json,hashlib,importlib.util,math
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));stage=w/'staged_y_path_clearance'
from simfoundry.data.initial_top_route import ClearanceFeedback as Old
spec=importlib.util.spec_from_file_location('isolated_y_path',stage/'initial_top_route.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);New=module.ClearanceFeedback
rows=[]
for label,target,obstacle,goal,required in [('negative_away',[.5,-.25,.77],[.5,.15,.77],-.45,False),('negative_toward_crossing',[.5,-.25,.77],[.5,.15,.77],.4,True),('positive_away',[.5,.4,.77],[.5,.15,.77],.55,False),('positive_toward_crossing',[.5,.4,.77],[.5,.15,.77],-.4,True)]:
 args=(target,obstacle,(.14,.09,.045),(.15,.145,.04),(0,0,0,1),(0,0,0,1),target,target,goal)
 old=Old(target[0],obstacle[0]).propose(*args);new=New(target[0],obstacle[0]).propose(*args)
 assert new['eligible'] and new['needs_x_corridor']==required
 assert new['object_goal_xy'][0]==(old['object_goal_xy'][0] if required else target[0])
 assert max(abs(new['command_xy'][i]-target[i]) for i in (0,1))<=.00300000001
 rows.append(dict(case=label,needs_x_corridor=required,old_goal=old['object_goal_xy'],new_goal=new['object_goal_xy'],remaining_y_gap_m=new['remaining_y_gap_m']))
actual=[]
for dirname,identifier,task,which in [('current_lateral_profile_r1',895000,'push_box_to_bin','first_push'),('current_lateral_profile_r1',895000,'nudge_mailer_to_bin','first_push'),('initial_near_contact_depth_r1',890003,'nudge_mailer_to_bin','first_guard'),('initial_top_short_recovery_depth_r1',880003,'nudge_mailer_to_bin','first_guard')]:
 ep=w/dirname/f'case_{identifier}/layout_{identifier}_{task}';log=json.loads((ep/'frontal_bypass.json').read_text());row=next(r for r in log['rows'] if (r['mode']=='top_push' if which=='first_push' else r.get('route_stop_reason')));t=row['step'];key='box' if 'push_box' in task else 'mailer';other='mailer' if key=='box' else 'box';size=(.14,.09,.045) if key=='box' else (.15,.145,.04);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'trace.npz') as z:target=z[key][t].astype(float);obstacle=z[other][t].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key][t];oquat=z[other][t]
 goal=log['plan']['initial_top_proposal']['goal_y'];initialx=log['plan']['initial_target_xyz'][0];initialotherx=log['plan']['obstacle_initial_xyz'][0];tip=row['observed_support_xyz'];args=(target,obstacle,size,osize,quat,oquat,tip,tip,goal);old=Old(initialx,initialotherx).propose(*args);new=New(initialx,initialotherx).propose(*args)
 if which=='first_push':assert new['eligible'] and not new['needs_x_corridor'] and new['object_goal_xy'][0]==initialx;assert abs(old['object_goal_xy'][0]-initialx)>.10
 else:assert not new['eligible'] and new['reason']==old['reason']=='planned_corridor_no_table_margin_5mm'
 actual.append(dict(episode=ep.name,frame=t,kind=which,old=old,new=new,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
# Actual original parcel guard remains first, independently of a distant finalY.
x=New(.5,.6).propose([.5,0,.77],[.6,0,.77],(.14,.09,.045),(.15,.145,.04),(0,0,0,1),(0,0,0,1),[.5,0,.8],[.5,0,.8],.4);assert not x['eligible'] and x['reason']=='preserve_original_parcel_clearance_10mm'
manifest=json.loads((stage/'MANIFEST.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in manifest['source_sha256'].items():assert sha(Path(p))==h,p
assert sha(stage/'initial_top_route.py')==manifest['candidate_sha256']
result=dict(synthetic_direction_checks=rows,actual_checks=actual,original_parcel_guard_preserved=True,live_sources_unchanged=True,scope='Counterfactual single-waypoint checks only. Demonstrates unnecessaryXdetour and retains actual nearbag corridor guards. No new contact trajectory, pose/task success or visibility proof.',training_ready=False);(stage/'CHECK.json').write_text(json.dumps(result,indent=2,default=lambda v:v.item()));print(json.dumps(dict(direction_cases=rows,actual_cases=[dict(episode=r['episode'],frame=r['frame'],old_goal=r['old'].get('object_goal_xy'),new_goal=r['new'].get('object_goal_xy'),reason=r['new'].get('reason')) for r in actual],original_parcel_guard_preserved=True),indent=2))
