"""Execute actual candidate pre-contact guard/goal prefix on fixed real snapshots.
Not a counterfactual trajectory: each snapshot retains its original prior latch.
Does not execute remaining contact state machine, IK or robot/parcel dynamics.
"""
from pathlib import Path
import ast,json,hashlib,sys,datetime,copy,types,math
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W/'staged_closed_peak_trial'),str(ROOT)]
from simfoundry.data.tabletop_route_candidates import footprint_radii
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((W/'FRONT_CORRIDOR_INTERVAL_CANDIDATE_PREPARATION.json').read_text());assert sha(prep['candidate'])==prep['candidate_sha256'] and sha(prep['parent'])==prep['parent_sha256']
def prefix(path):
 tree=ast.parse(Path(path).read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FrontTopRouteState');update=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='update'));stop=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_stop'));i=next(i for i,n in enumerate(update.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='previous_route_stage' for t in n.targets));update.body=update.body[:i]+ast.parse("return dict(prefix_continues=True,goal_x=goal_x,interval=locals().get('interval_record',{}))").body
 module=ast.fix_missing_locations(ast.Module(body=[stop,update],type_ignores=[]));space={'math':math,'footprint_radii':footprint_radii};exec(compile(module,str(path)+'#guard-prefix','exec'),space);return space['update'],space['_stop']
old,oldstop=prefix(prep['parent']);new,newstop=prefix(prep['candidate']);screen=json.loads((W/'FRONT_CORRIDOR_REPLANNING_SCREEN_R3.json').read_text());summaries=[];sources={prep['candidate']:sha(prep['candidate']),prep['parent']:sha(prep['parent'])};first_case=None
for summary in screen['episodes']:
 ep=next((W/'fresh_closed_peak_trials_r1').glob('case_*/'+summary['episode']));fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';size=(.14,.09,.045) if key=='box' else (.15,.145,.04);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy();otherxyz=z[other].copy()
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].copy();otherquat=z[other].copy()
 route=next(x for x in plan['front_route_candidates']['candidates'] if x['route']=='front');rx=route['waypoints_xy'][1][0]-.003;prior_reason=None;prior_tip=None;changed=[];stops=0
 for row in fr['rows']:
  t=row['step'];tip=tuple(row['observed_support_xyz']);kw=dict(tip=tip,quat=quat[t],obstacle_quat=otherquat[t],control_offset_local=row['control_offset_local'],load_n=0.,hand_obstacle_gap_m=row['hand_obstacle_gap_m']);args=(tip,xyz[t],otherxyz[t],0.,0.)
  def state(enabled,stop):
   value=types.SimpleNamespace(corridor_interval_replan=enabled,retain_micro_repair_contact=True,recontact_on_route_change=True,diagonal_entry=True,recovery_hysteresis_m=.0005,recover_clearance=True,route_clearance_m=.012,rear=types.SimpleNamespace(plan=plan),size=size,obstacle_size=osize,route_report={},route_x=rx,stop_reason=prior_reason,stop_tip=prior_tip,mode_step=0,load=types.SimpleNamespace(bias_m=0.),route_stage=row['route_stage']);value._stop=types.MethodType(stop,value);return value
  base=old(state(False,oldstop),*args,**kw);disabled=new(state(False,newstop),*args,**kw);assert base==disabled,('default-off differs',ep.name,t)
  actual_stopped=bool(row.get('route_stop_reason'));assert (not base.get('prefix_continues',False))==actual_stopped,(ep.name,t,'original guard replay')
  if actual_stopped:assert base['route_stop_reason']==row['route_stop_reason'];stops+=1
  elif 'route_goal_x' in row:assert abs(base['goal_x']-row['route_goal_x'])<2e-6
  enabled=new(state(True,newstop),*args,**kw);record=enabled.get('interval',{}).get('front_corridor_interval',enabled.get('front_corridor_interval'));assert record['enabled']
  if record['changed']:
   assert not record['protected'] and prior_reason is None and actual_stopped and enabled.get('prefix_continues') and row['route_stop_reason']=='front_corridor_no_table_margin';assert record['safe_interval_x'][0]<record['goal_x']<record['safe_interval_x'][1];changed.append(dict(step=t,**record))
   if first_case is None:first_case=(copy.deepcopy(state(True,newstop)),copy.deepcopy(args),copy.deepcopy(kw))
  else:
   normalized=copy.deepcopy(enabled);normalized.pop('front_corridor_interval',None)
   if 'interval' in normalized:normalized['interval']={}
   assert normalized==base,('unchanged branch differs',ep.name,t)
  if actual_stopped and prior_reason is None:prior_reason=row['route_stop_reason'];prior_tip=tip
 assert [x['step'] for x in changed]==[x['step'] for x in summary['proposed_changes']]
 summaries.append(dict(episode=ep.name,frames=len(fr['rows']),original_quality_passed=summary['original_quality_passed'],default_off_identical=True,original_guard_frames=stops,changes=changed));print(ep.name,len(changed),flush=True)
 for p in [ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz']:sources[str(p)]=sha(p)
assert first_case is not None
negatives=[]
for kind in ['latched_stop','hand_gap','non_target_motion','target_table','parcel_gap']:
 state,args,kw=copy.deepcopy(first_case);args=list(args)
 if kind=='latched_stop':state.stop_reason='prior_protection';state.stop_tip=kw['tip']
 elif kind=='hand_gap':kw['hand_obstacle_gap_m']=.004
 elif kind=='non_target_motion':state.rear.plan['obstacle_initial_xyz'][1]-=.02
 elif kind=='target_table':args[1][1]=.75
 elif kind=='parcel_gap':args[1][0]=args[2][0];args[1][1]=args[2][1]
 state._stop=types.MethodType(newstop,state);out=new(state,*args,**kw);assert not out.get('prefix_continues',False) and out['front_corridor_interval']['protected'] and not out['front_corridor_interval']['changed'];negatives.append(kind)
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,episodes=summaries,rows=sum(x['frames'] for x in summaries),default_off_rows_identical=sum(x['frames'] for x in summaries),changed_rows=sum(len(x['changes']) for x in summaries),live_protections_preserved=negatives,source_sha256=sources,checker_sha256=sha(__file__),runtime_installed=False,physics_verified=False,training_ready=False)
with (W/'FRONT_CORRIDOR_INTERVAL_CANDIDATE_CHECK.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ['episodes','source_sha256']},indent=2))
