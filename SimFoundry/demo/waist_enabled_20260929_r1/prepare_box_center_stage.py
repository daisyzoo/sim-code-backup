from pathlib import Path
import ast,json,hashlib
w=Path('/home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1');old=w/'staged_rear_slow_drag';stage=w/'staged_box_center_preference';assert not stage.exists();stage.mkdir();sha=lambda s:hashlib.sha256(s.encode()).hexdigest();changes={}
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
for p in old.iterdir():
 if p.suffix not in ['.py','.json'] or p.name.endswith('CHECK.json') or p.name=='CHANGE_MANIFEST.json':continue
 s=p.read_text();original=s
 if p.name=='collect_paired_sorting.py':
  s=one(s,'parser = argparse.ArgumentParser()','parser = argparse.ArgumentParser()\nparser.add_argument(\'--rear-box-center-preference\',action=\'store_true\',help=\'Diagnostic rear box:400/m2 unloaded center preference and1.5mm drag; rear bag retains3mm. Default off.\')')
  s=one(s,'args = parser.parse_args()',"args = parser.parse_args()\nif args.rear_box_center_preference and not (args.rear_slow_drag and args.minimum_motion_recontact and args.role=='diagnostic'):\n    parser.error('Box center preference requires complete rear-slow/minimum-motion diagnostic')")
  s=one(s,'recontact_lifecycle=RecontactLifecycle(enabled=True,prefer_interior=args.recontact_interior_preference)',"recontact_extra = dict(box_center_preference=(side=='right')) if args.rear_box_center_preference else {}\n        recontact_lifecycle=RecontactLifecycle(enabled=True,prefer_interior=args.recontact_interior_preference,**recontact_extra)")
  s=one(s,'rear_slow_drag=args.rear_slow_drag, rear_cop_enabled=True',"rear_slow_drag=bool(args.rear_slow_drag and (not args.rear_box_center_preference or side=='right')), rear_cop_enabled=True")
  s=one(s,".0015 if args.rear_slow_drag and frontal_plan.get('rear_cop_centering',{}).get('enabled',False)",".0015 if args.rear_slow_drag and (not args.rear_box_center_preference or side=='right') and frontal_plan.get('rear_cop_centering',{}).get('enabled',False)")
  needle="frontal_plan['unloaded_recontact_pose']['minimum_motion_pose']=dict(enabled=True,alignment_abs_min=.8,preferred_inset_m=.020,seed_policy=['original_endpoint','current_observed'],lift_heights_m=[.015,.030,.060],original_fallback=True,whole_sampled_path_check=True,maximum_ticks=240,training_ready=False)"
  s=one(s,needle,needle+"\n                        if args.rear_box_center_preference and side=='right':\n                            frontal_plan['unloaded_recontact_pose']['box_center_preference']=dict(enabled=True,center_weight_per_m2=400.,parent='same_observation_minimum_motion',side='right',original_fallback=True,original_constraints_unchanged=True)")
  s=one(s,"    if args.rear_slow_drag:\n        episode.collect_meta['rear_slow_drag']=True", "    if args.rear_box_center_preference:\n        episode.collect_meta['rear_box_center_preference']=True\n    if args.rear_slow_drag:\n        episode.collect_meta['rear_slow_drag']=True")
  s=one(s,"    for path in paths:\n        snapshot", "    if args.rear_box_center_preference:\n        paths.append(STAGE/'box_center_preference_plan.py')\n    for path in paths:\n        snapshot")
 elif p.name=='minimum_motion_lifecycle.py':
  s=one(s,'maximum_ticks=240,prefer_interior=False):','maximum_ticks=240,prefer_interior=False,box_center_preference=False):')
  s=one(s,'        self.prefer_interior=prefer_interior',"        if type(box_center_preference) is not bool:raise ValueError('Invalid box center preference')\n        self.box_center_preference=box_center_preference\n        self.prefer_interior=prefer_interior")
  s=one(s,'prefer_interior=self.prefer_interior,minimum_motion_pose=True)','prefer_interior=self.prefer_interior,minimum_motion_pose=True,box_center_preference=self.box_center_preference)')
 elif p.name=='recontact_plan.py':
  s=one(s,'prefer_interior=False,minimum_motion_pose=False):','prefer_interior=False,minimum_motion_pose=False,box_center_preference=False):')
  s=one(s,"    if type(minimum_motion_pose) is not bool:","    if type(box_center_preference) is not bool:raise ValueError('Invalid box center preference')\n    if box_center_preference:\n        if not (minimum_motion_pose and prefer_interior and scene.side=='right'):raise ValueError('Box center preference requires right-side minimum-motion interior plan')\n        from box_center_preference_plan import plan as centered_plan\n        parent=plan(scene,q,step=step,earlier_seed=earlier_seed,prefer_interior=prefer_interior,minimum_motion_pose=minimum_motion_pose)\n        return centered_plan(scene,q,step=step,parent_plan=parent)\n    if type(minimum_motion_pose) is not bool:")
 if p.suffix=='.py':ast.parse(s)
 (stage/p.name).write_text(s)
 if s!=original:changes[p.name]=dict(before_sha256=sha(original),after_sha256=sha(s))
s=(w/'offline_center_penalty_plan.py').read_text();s=s.replace('# OFFLINE ONLY. Soft center preference; all original endpoint/path gates retained.','# Default-off box-only center preference. No contact or success guarantee.').replace('offline_center_penalty=True','box_center_preference=True').replace('minimum_motion_pose','box_center_preference_pose');s=one(s,'    q=np.asarray(q,float);guard=scene.guard',"    if scene.side!='right':raise ValueError('Box center preference requires right hand')\n    q=np.asarray(q,float);guard=scene.guard");ast.parse(s);(stage/'box_center_preference_plan.py').write_text(s)
assert set(changes)=={'collect_paired_sorting.py','minimum_motion_lifecycle.py','recontact_plan.py'}
(stage/'CHANGE_MANIFEST.json').write_text(json.dumps(dict(changes=changes,new_module_sha256=sha(s),scope='Relative to closed uniform1.5mm trial: rear box keeps1.5mm and adds400/m2 unloaded support-center preference; rear bag restored to original3mm. Front/initial routes3mm. Original loaded controller, constraints, budget and guards unchanged. Pending independent audits/lifecycle/CLI/full-protocol validation; not started.',training_ready=False),indent=2));print('prepared unvalidated stage',stage)
