"""Independent verifier versus actual candidate guard prefix on recorded poses.
Enabled rows are synthetic guard/goal records on a fixed observed-state stream,
not a new physical trajectory, not a full contact/COP/IK execution or admission.
Candidate latch is propagated within this guard-only fixture. Original episodes
and their latched-stop records are never rewritten.
"""
from pathlib import Path
import ast,copy,json,hashlib,sys,types,math,datetime
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'staged_closed_peak_trial'),str(W.parents[1])]
from simfoundry.data.tabletop_route_candidates import footprint_radii
from audit_front_interval_goal_records import verify_interval_rows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((W/'FRONT_CORRIDOR_INTERVAL_CANDIDATE_PREPARATION.json').read_text());candidate=Path(prep['candidate']);assert sha(candidate)==prep['candidate_sha256']
tree=ast.parse(candidate.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FrontTopRouteState');update=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='update'));stop=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_stop'));end=next(i for i,n in enumerate(update.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='previous_route_stage' for t in n.targets));update.body=update.body[:end]+ast.parse("return dict(prefix_continues=True,goal_x=goal_x,interval=interval_record)").body
module=ast.fix_missing_locations(ast.Module(body=[stop,update],type_ignores=[]));space={'math':math,'footprint_radii':footprint_radii};exec(compile(module,str(candidate)+'#guard-only','exec'),space)
screen=json.loads((W/'FRONT_CORRIDOR_REPLANNING_SCREEN_R4.json').read_text());episodes=[next((W/'fresh_closed_peak_trials_r1').glob('case_*/'+x['episode'])) for x in screen['episodes']];episodes.append(W/'joint_edge_intersection_physical_r1/case_840015/layout_840015_nudge_mailer_to_bin');results=[];bindings={str(candidate):sha(candidate),str(W/'audit_front_interval_goal_records.py'):sha(W/'audit_front_interval_goal_records.py')};negatives=[]
for ep in episodes:
 fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':(.14,.09,.045),'mailer':(.15,.145,.04)}
 with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in z.files}
 disabled=verify_interval_rows(fr['rows'],plan,tr,ori,key,enabled=False)
 front=next(x for x in plan['front_route_candidates']['candidates'] if x['route']=='front');rx=front['waypoints_xy'][1][0]-.003;prior_reason=prior_tip=None;rows=[];probe=None
 for row in fr['rows']:
  t=row['step'];tip=tuple(row['observed_support_xyz']);state=types.SimpleNamespace(corridor_interval_replan=True,retain_micro_repair_contact=True,recontact_on_route_change=True,diagonal_entry=True,recovery_hysteresis_m=.0005,recover_clearance=True,route_clearance_m=.012,rear=types.SimpleNamespace(plan=plan),size=sizes[key],obstacle_size=sizes[other],route_report={},route_x=rx,stop_reason=prior_reason,stop_tip=prior_tip,mode_step=0,load=types.SimpleNamespace(bias_m=0.),route_stage=row['route_stage']);state._stop=types.MethodType(space['_stop'],state)
  out=space['update'](state,tip,tr[key][t],tr[other][t],0.,0.,tip=tip,quat=ori[key][t],obstacle_quat=ori[other][t],control_offset_local=row['control_offset_local'],load_n=0.,hand_obstacle_gap_m=row['hand_obstacle_gap_m'])
  record=out['interval']['front_corridor_interval'] if out.get('prefix_continues') else out['front_corridor_interval'];synthetic=dict(step=t,hand_obstacle_gap_m=row['hand_obstacle_gap_m'],front_corridor_interval=record,mode='prefix_continues' if out.get('prefix_continues') else 'front_guard_lift',route_stop_reason=state.stop_reason)
  if out.get('prefix_continues'):synthetic['route_goal_x']=out['goal_x']
  rows.append(synthetic);prior_reason=state.stop_reason;prior_tip=state.stop_tip
  if record['changed'] and probe is None:probe=(copy.deepcopy(state),t,tip)
 p=copy.deepcopy(plan);p['front_corridor_interval']=dict(enabled=True,table_margin_m=.005,parcel_planning_clearance_m=.012,original_extra_reserve_m=.003,proposal='midpoint_only_when_original_infeasible',original_live_guards=True,latched_stop_preserved=True,training_ready=False)
 verified=verify_interval_rows(rows,p,tr,ori,key,enabled=True)
 changed=[x['step'] for x in verified['records'] if x['changed']];guards=[x['step'] for x in rows if x['mode']=='front_guard_lift']
 results.append(dict(episode=str(ep.relative_to(W)),rows=len(rows),disabled_actual_verified=disabled['passed'],enabled_guard_fixture_verified=verified['passed'],changed_rows=len(changed),first_changed_step=changed[0] if changed else None,first_fixture_stop=guards[0] if guards else None,actual_quality_passed=json.loads((ep/'quality.json').read_text())['passed']))
 if changed and not negatives:
  for kind in ['modified_goal','modified_interval','false_change_flag','missing_record','unprotected_old_goal']:
   bad=copy.deepcopy(rows);r=bad[changed[0]-1];rec=r['front_corridor_interval']
   if kind=='modified_goal':rec['goal_x']+=.001;r['route_goal_x']+=.001
   elif kind=='modified_interval':rec['safe_interval_x'][1]+=.001
   elif kind=='false_change_flag':rec['changed']=False
   elif kind=='missing_record':r.pop('front_corridor_interval')
   else:rec['goal_x']=rec['original_goal_x'];r['route_goal_x']=rec['original_goal_x'];rec['changed']=False
   try:verify_interval_rows(bad,p,tr,ori,key,enabled=True)
   except (AssertionError,KeyError):negatives.append(kind)
   else:raise AssertionError(('mutation accepted',kind))
 if probe and 'guard_bypass' not in negatives:
  state,t,tip=probe;state._stop=types.MethodType(space['_stop'],state)
  blocked=space['update'](state,tip,tr[key][t],tr[other][t],0.,0.,tip=tip,quat=ori[key][t],obstacle_quat=ori[other][t],control_offset_local=fr['rows'][t-1]['control_offset_local'],load_n=0.,hand_obstacle_gap_m=.004)
  assert blocked['mode']=='front_guard_lift' and blocked['front_corridor_interval']['protected'] and not blocked['front_corridor_interval']['changed']
  fixture=copy.deepcopy(rows[:t]);fixture[-1]=dict(step=t,hand_obstacle_gap_m=.004,front_corridor_interval=blocked['front_corridor_interval'],mode=blocked['mode'],route_stop_reason=blocked['route_stop_reason'])
  assert verify_interval_rows(fixture,p,tr,ori,key,enabled=True)['passed']
  bad=copy.deepcopy(fixture);bad[-1]['mode']='prefix_continues';bad[-1]['route_stop_reason']=None
  try:verify_interval_rows(bad,p,tr,ori,key,enabled=True)
  except (AssertionError,KeyError):negatives.append('guard_bypass')
  else:raise AssertionError('injected guard bypass accepted')
 if guards and 'guard_bypass' not in negatives:
  bad=copy.deepcopy(rows);bad[guards[0]-1]['mode']='prefix_continues';bad[guards[0]-1]['route_stop_reason']=None
  try:verify_interval_rows(bad,p,tr,ori,key,enabled=True)
  except (AssertionError,KeyError):negatives.append('guard_bypass')
  else:raise AssertionError('guard bypass accepted')
 for name in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','quality.json']:bindings[str(ep/name)]=sha(ep/name)
 print(json.dumps(results[-1]),flush=True)
assert len(results)==9 and len(negatives)==6
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,episodes=results,rows=sum(x['rows'] for x in results),mutation_rejections=negatives,source_sha256=bindings,checker_sha256=sha(__file__),full_contact_cop_ik_verified=False,physics_verified=False,training_ready=False)
with (W/'FRONT_INTERVAL_INDEPENDENT_ENABLED_CHECK.json').open('x') as f:json.dump(result,f,indent=2)
print('PASS',result['rows'],negatives)
