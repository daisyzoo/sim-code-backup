"""Reproduce measured corridor failure and check one prospective phase extension.
Each trajectory stops comparison at its first changed proposal: no old future
is treated as the response to a new command. Geometry only, no robot rollout.
"""
from pathlib import Path
import sys,json,hashlib,datetime,importlib.util,copy
import numpy as np
from scipy.optimize import linprog
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';C=W/'front_corridor_lateral_candidate_r1'
sys.path[:0]=[str(S),str(W),str(ROOT)]
import front_corridor_midpoint_runtime as original
from simfoundry.data.tabletop_route_candidates import footprint_radii
spec=importlib.util.spec_from_file_location('lateral_candidate',C/'selection.py');candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={str(Path(__file__)):sha(__file__),str(C/'selection.py'):sha(C/'selection.py'),str(S/'front_corridor_midpoint_runtime.py'):sha(S/'front_corridor_midpoint_runtime.py'),str(S/'front_diagonal_entry_geometry_probe.py'):sha(S/'front_diagonal_entry_geometry_probe.py'),str(ROOT/'simfoundry/data/tabletop_route_candidates.py'):sha(ROOT/'simfoundry/data/tabletop_route_candidates.py')}

def context(row,fr,t,o,tq,oq):
 i=row['step'];c=row['front_corridor_midpoint'];np.testing.assert_array_equal(t[i],row['observed_target'])
 return dict(original_goal_x=c['original_goal_x'],route_stage=c['route_stage'],target=t[i].tolist(),obstacle=o[i].tolist(),size=[.15,.145,.04],other_size=[.14,.09,.045],quat=tq[i].tolist(),other_quat=oq[i].tolist(),direction=fr['plan']['direction'],planning_margin=c['original_planning_margin_m'],initial_other=fr['plan']['obstacle_initial_xyz'],hand_obstacle_gap_m=row['hand_obstacle_gap_m'],parent_guard_reason='observed_guard' if c['other_guard_active'] else None,prior_stop_reason=c['prior_stop_reason'])

def independently_check_paths(c,record):
 tr=np.array(footprint_radii(c['size'],c['quat']));orr=np.array(footprint_radii(c['other_size'],c['other_quat']));ob=np.array(c['obstacle'][:2]);combined=tr+orr
 lo=.28+.005+tr[0];hi=ob[0]-combined[0]-c['planning_margin'];np.testing.assert_allclose([lo,hi],record['safe_interval_x'],atol=1e-12,rtol=0)
 assert lo<record['goal_x']<hi
 checks=[]
 for route in record['candidate_routes']['routes']:
  gaps=[];points=route['points']
  for a,b in zip(points,points[1:]):
   a=np.array(a);delta=np.array(b)-a;start=a-ob
   # Minimize g >= four signed AABB separation planes over 0<=t<=1.
   slopes=np.r_[delta,-delta];intercepts=np.r_[start-combined,-start-combined]
   lp=linprog([0.,1.],A_ub=np.column_stack([slopes,-np.ones(4)]),b_ub=-intercepts,bounds=[(0.,1.),(None,None)],method='highs')
   assert lp.success;gaps.append(float(lp.fun))
  tm=min(min(x-tr[0]-.28,.88-x-tr[0],y-tr[1]+.75,.75-y-tr[1]) for x,y in points)
  np.testing.assert_allclose(min(gaps),route['minimum_axis_gap_m'],atol=1e-10,rtol=0);np.testing.assert_allclose(tm,route['minimum_table_margin_m'],atol=1e-12,rtol=0)
  assert min(gaps)>=c['planning_margin']-1e-10 and tm>=.005-1e-10
  checks.append(dict(route=route['route'],lp_minimum_parcel_axis_gap_m=min(gaps),minimum_table_margin_m=tm))
 return checks

runs=[];newcontext=None
for run in ['front_box_recenter_physical_r2','inactive_transport_physical_r1','joint_transport_physical_r1','joint_transport_reserve_physical_r1']:
 ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text())
 for f in [ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'raw.npz',ep/'READY_FOR_AUDIT.json']:sources[str(f)]=sha(f)
 ready=json.loads((ep/'READY_FOR_AUDIT.json').read_text())
 for path,h in ready['source_sha256'].items():assert sha(path)==h
 with np.load(ep/'trace.npz') as z:t=z['mailer'].copy();o=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:tq=z['mailer'].copy();oq=z['box'].copy()
 prefix=0;changed=None;firststop=None
 for row in fr['rows']:
  if 'front_corridor_midpoint' not in row:continue
  c=context(row,fr,t,o,tq,oq);g,old=original.select(**c);disabled=candidate.select(**c)
  assert disabled==(g,old)
  saved=row['front_corridor_midpoint'];assert old['changed']==saved['changed'] and old['reason']==saved['reason'];np.testing.assert_allclose(g,saved['goal_x'],atol=1e-12,rtol=0)
  if firststop is None and row.get('route_stop_reason'):firststop=dict(step=row['step'],reason=row['route_stop_reason'],stage=c['route_stage'],safe_interval_x=old['safe_interval_x'])
  newgoal,new=candidate.select(**c,lateral_y_enabled=True)
  if newgoal!=g or new['changed']!=old['changed']:
   changed=dict(step=row['step'],original=old,candidate=new,independent_paths=independently_check_paths(c,new),remaining_control_intervals=1199-row['step'])
   if run=='joint_transport_reserve_physical_r1':newcontext=c
   break
  prefix+=1
 runs.append(dict(run=run,unchanged_goal_prefix_rows=prefix,first_stop=firststop,first_changed_proposal=changed,no_observations_after_changed_proposal_used=True))
assert newcontext is not None
assert runs[-1]['first_changed_proposal']['step']==594
# Earlier versions can diverge before their eventual empty corridor; preserve that evidence.
for run_result in runs:
 ep=W/run_result['run']/'case_840023/layout_840023_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());stop=next(x for x in fr['rows'] if x.get('route_stop_reason')=='front_corridor_no_table_margin')
 with np.load(ep/'trace.npz') as z:t=z['mailer'].copy();o=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:tq=z['mailer'].copy();oq=z['box'].copy()
 c=context(stop,fr,t,o,tq,oq);g,result=candidate.select(**c,lateral_y_enabled=True)
 if result['safe_interval_x'][0]>=result['safe_interval_x'][1]:assert not result['changed']
 run_result['independent_actual_stop_context']=dict(step=stop['step'],record=result,scope='Separate observed context only, never continuation after changed prefix')
negative=[]
mutations=[('latched_stop',{'prior_stop_reason':'front_corridor_no_table_margin'}),('parent_guard',{'parent_guard_reason':'independent_guard'}),('hand_gap',{'hand_obstacle_gap_m':.0049}),('other_motion',{'initial_other':[newcontext['obstacle'][0]+.011,*newcontext['obstacle'][1:]]}),('table_margin',{'target':[.284+footprint_radii(newcontext['size'],newcontext['quat'])[0],*newcontext['target'][1:]]}),('valid_original',{'original_goal_x':sum(runs[-1]['first_changed_proposal']['original']['safe_interval_x'])/2})]
for name,delta in mutations:
 c=copy.deepcopy(newcontext);c.update(delta);g,r=candidate.select(**c,lateral_y_enabled=True);assert not r['changed'];assert g==c['original_goal_x'];negative.append(dict(case=name,reason=r['reason']))
for bad in [0,1,None,'true']:
 try:candidate.select(**newcontext,lateral_y_enabled=bad)
 except ValueError:negative.append(dict(case='invalid_flag_'+repr(bad),rejected=True))
 else:raise AssertionError('invalid flag accepted')
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,runs=runs,guard_checks=negative,source_sha256=sources,physical_execution=False,training_ready=False,goal_complete=False,limitations=['Only current-observation fixed-orientation object paths checked; no fresh command, full-arm reach, contact force, physical tracking or policy result.','The positive corridor is less than1mm wide; future rotation or drift may correctly trigger the original guard.','Existing parent-fallback actual margin losses remain unresolved; do not count an optimized-branch pass as whole-episode safety.'],next='Reconstruct causal native controller through step593; compare first unissued command594 with all parent priorities retained, then isolated source/auditor integration.')
with (C/'GEOMETRY_REPRODUCTION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps([dict(run=r['run'],prefix=r['unchanged_goal_prefix_rows'],first_stop=r['first_stop'],changed_step=None if r['first_changed_proposal'] is None else r['first_changed_proposal']['step']) for r in runs],indent=2))
print('Guard checks',len(negative));print(json.dumps(runs[-1]['first_changed_proposal']['independent_paths'],indent=2))
