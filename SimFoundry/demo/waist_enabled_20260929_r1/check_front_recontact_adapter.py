"""Actual parent state class with explicit synthetic audited handover fixtures.
Check atomic rejection, real recovery counter, captured surface/next press,
original front guard and next recovery reset. Not a physical rollout.
"""
from pathlib import Path
from types import SimpleNamespace
import copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_waypoint_reconciliation';D=W/'front_bag_recontact_center_draft_r4';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from front_initial_center_cop_route import FrontCopRouteState
from front_recontact_center_adapter import apply
from simfoundry.data.top_contact_bypass import rotation_xyzw
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();report=json.loads((D/'LIFECYCLE_CHECK.json').read_text());assert report['passed'];sources=dict(report['source_sha256'])
for name,h in sources.items():assert sha(name)==h,name
for p in [Path(__file__),D/'LIFECYCLE_CHECK.json']:sources[str(p)]=sha(p)
rows=[]
for r in report['records']:
 ep=W/r['run']/'case_840023/layout_840023_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());row=next(x for x in fr['rows'] if x['step']==r['step']);p=r['selected_plan'];s=p['scene'];size=s['core_size'];other_size=s['other_size'];state=FrontCopRouteState(SimpleNamespace(plan=copy.deepcopy(fr['plan'])),'left',tuple(size),obstacle_size=tuple(other_size),guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=.9,tilt_recontact_rad=.03,recontact_on_route_change=True,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005,route_clearance_m=.012,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=.002,edge_speed_enabled=True,edge_core_size=size)
 state.recontacts=r['recontacts'];state.mode=state.top_mode=row['mode'];event=copy.deepcopy(r['events'][-1]);ref={k:np.array(v) for k,v in event['reference'].items()};xyz=np.asarray(s['target_xyz']);rot=np.asarray(rotation_xyzw(s['target_quat']));saved=repr(vars(state));unchanged=apply(row,state,ref,dict(kind='unchanged'),object_xyz=xyz,object_rotation=rot);assert unchanged[0] is row and unchanged[1] is ref and repr(vars(state))==saved
 invalid=[]
 for kind in ['stop','early','wrong_counter','zero_counter','noncenter','parent_guard']:
  st=copy.deepcopy(state);e=copy.deepcopy(event);rr=copy.deepcopy(row);before=repr(vars(st))
  if kind=='stop':e['kind']='stop'
  if kind=='early':e['measured_ready_count']=2
  if kind=='wrong_counter':e['context']['recontacts']+=1
  if kind=='zero_counter':e['context']['recontacts']=0
  if kind=='noncenter':e['selected_surface_local_xy'][0]=.02
  if kind=='parent_guard':rr['route_stop_reason']='fixture_guard'
  try:apply(rr,st,ref,e,object_xyz=xyz,object_rotation=rot)
  except ValueError:pass
  else:raise AssertionError('invalid transition accepted '+kind)
  assert repr(vars(st))==before;invalid.append(kind)
 rr,newref=apply(row,state,ref,event,object_xyz=xyz,object_rotation=rot);assert state.recontacts==r['recontacts'] and state.top_mode=='top_press' and state.mode_step==1;tip=np.asarray(event['observed_support_xyz']);xy=np.asarray(event['selected_surface_local_xy']);surface=xyz+rot@np.r_[xy,size[2]/2];np.testing.assert_allclose(rr['parcel_top_xyz'],surface,atol=1e-12,rtol=0);np.testing.assert_allclose(rr['target_xyz'],tip,atol=1e-12,rtol=0);assert state.selected_surface_local_xy==tuple(xy)
 # Original guard remains before the captured-surface branch of parent update.
 inp=dict(tip=tip,quat=s['target_quat'],obstacle_quat=s['other_quat'],control_offset_local=newref['reference_local'],load_n=0.,hand_obstacle_gap_m=.001)
 stopped=copy.deepcopy(state).update(xyz,xyz,s['other_xyz'],size[0]/2,other_size[0]/2,**inp);assert stopped['mode']=='front_guard_lift'
 state._start_recontact(tip,'fixture_next_real_recovery');assert state.recontacts==r['recontacts']+1 and state.selected_surface_local_xy is None
 rows.append(dict(run=r['run'],recontacts=r['recontacts'],atomic_invalid_rejections=invalid,unchanged_path_exact=True,counter_preserved=True,captured_surface_equal=True,original_guard_precedence=True,next_recovery_clears_surface=True))
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=rows,source_sha256=sources,simulation_started=False,collector_integrated=False,training_ready=False)
with (D/'ADAPTER_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,fixtures=len(rows),atomic_negative_cases=sum(len(r['atomic_invalid_rejections']) for r in rows))))
