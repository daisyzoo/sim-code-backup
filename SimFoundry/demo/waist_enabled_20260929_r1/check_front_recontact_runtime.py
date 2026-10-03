"""Runtime ownership/capture tests using audited affine fixtures and parent class.
These are explicit sampled-prefix/affine fixtures, not a new physical history.
No caller is allowed to pass a fabricated zero counter to the recovery path.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys,json,datetime,hashlib,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_waypoint_reconciliation';D=W/'front_bag_recontact_center_draft_r4';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from front_recontact_center_runtime import FrontRecontactCenterRuntime
from front_initial_center_cop_route import FrontCopRouteState
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);base=json.loads((D/'LIFECYCLE_CHECK.json').read_text());sources=dict(base['source_sha256']);records=[];negative=[];active_fixture=None
for n,h in sources.items():assert sha(n)==h,n
for p in [Path(__file__),D/'front_recontact_center_runtime.py',D/'LIFECYCLE_CHECK.json',D/'ADAPTER_CHECK.json',D/'ACTUAL_PREFIX_LOAD_CHECK.json']:sources[str(p)]=sha(p)
for fixture in base['records']:
 event0=fixture['events'][0];c=event0['context'];s=c['scene'];size=s['core_size'];other_size=s['other_size'];ep=W/fixture['run']/'case_840023/layout_840023_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());original=next(r for r in fr['rows'] if r['step']==fixture['step'])
 state=FrontCopRouteState(SimpleNamespace(plan=copy.deepcopy(fr['plan'])),'left',tuple(size),obstacle_size=tuple(other_size),guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=.9,tilt_recontact_rad=.03,recontact_on_route_change=True,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005,route_clearance_m=.012,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=.002,edge_speed_enabled=True,edge_core_size=size)
 runtime=FrontRecontactCenterRuntime(guard,'left',size,other_size,c['decay'],enabled=True);ref={k:np.asarray(v) for k,v in fixture['events'][-1]['reference'].items()};anchors=dict(normal_anchor=[0.,0.,1.],inactive_anchor=[.2,-.3,.89])
 def inputs(ev):
  cc=ev['context'];ss=cc['scene'];return dict(selected=True,step=cc['step'],current=cc['current'],previous_q=cc['previous_q'],previous_command=cc['previous_command'],target_xyz=ss['target_xyz'],target_quat=ss['target_quat'],other_xyz=ss['other_xyz'],other_quat=ss['other_quat'],observed_load_n=cc['observed_load_n'],observed_hand_pose=cc['observed_hand_pose'],observed_inactive_hand_pose=cc['observed_inactive_hand_pose'],**anchors)
 # Counter-ownership fixture: use original first lift record for each preceding
 # real recovery, without asserting omitted intervening candidate behavior.
 for counter in range(fixture['recontacts']):
  parent=next(r for r in fr['rows'] if r.get('recontacts')==counter and r['mode']=='top_lift');state.recontacts=counter;row=copy.deepcopy(parent);inp=inputs(event0);inp['step']=parent['step'];before=repr(vars(state));rr,rf,e=runtime.update(row,state,ref,**inp);assert e['kind']=='unchanged' and rr is row and rf is ref and repr(vars(state))==before
 checks=[]
 for expected in fixture['events']:
  row=copy.deepcopy(original);row['mode']=expected['context']['parent_mode'];row['recontacts']=fixture['recontacts'];row['step']=expected['context']['step'];row['contact_load']['filtered_vertical_load_n']=expected['context']['filtered_load_n'];state.recontacts=fixture['recontacts'];state.mode=state.top_mode=row['mode'];inp=inputs(expected)
  with patch('front_recontact_center_lifecycle.plan',return_value=copy.deepcopy(fixture['selected_plan'])):rr,rf,e=runtime.update(row,state,ref,**inp)
  assert e['kind']==expected['kind'] and e['command']==expected['command'] and e['measured_ready_count']==expected['measured_ready_count'];assert state.recontacts==fixture['recontacts'] and e['real_recontact_index']==fixture['recontacts']
  if e['kind']=='handover':
   np.testing.assert_array_equal(runtime.center_local,e['captured_center_local']);assert state.top_mode=='top_press';assert max(abs(np.asarray(rr['target_xyz'])-e['observed_support_xyz']))<1e-12;ref=rf
  elif active_fixture is None:
   # Next actual test input is an explicit affine-fixture observation.
   next_ev=fixture['events'][1];next_row=copy.deepcopy(row);next_row['step']=next_ev['context']['step'];active_fixture=(copy.deepcopy(runtime),copy.deepcopy(state),copy.deepcopy(ref),next_row,inputs(next_ev))
  checks.append(dict(step=inp['step'],kind=e['kind'],counter=e['real_recontact_index']))
 assert runtime.lifecycle.finished and runtime.failure is None
 records.append(dict(run=fixture['run'],real_counter=fixture['recontacts'],fixture_events=checks,captured_reference_matches=True))
 # Off/nonselected/right/first-contact contexts must preserve caller objects.
 for label,enabled,side,selected,counter in [('disabled',False,'left',True,1),('not_selected',True,'left',False,1),('right_box',True,'right',True,1),('first_contact',True,'left',True,0)]:
  rt=FrontRecontactCenterRuntime(guard,side,size,other_size,c['decay'],enabled=enabled);st=copy.deepcopy(state);st.recontacts=counter;row=copy.deepcopy(original);row['recontacts']=counter;inp=inputs(event0);inp['selected']=selected;before=repr(vars(st));rr,rf,e=rt.update(row,st,ref,**inp);assert e['kind']=='unchanged' and rr is row and rf is ref and repr(vars(st))==before;negative.append(label)
for label in ['counter_jump','counter_rollback','counter_changed_active','row_counter_disagrees','missing_load_active','selection_lost','parent_guard']:
 rt,st,ref,row,inp=copy.deepcopy(active_fixture)
 if label=='counter_jump':st.recontacts=3;row['recontacts']=3
 if label=='counter_rollback':st.recontacts=0;row['recontacts']=0
 if label=='counter_changed_active':st.recontacts=2;row['recontacts']=2
 if label=='row_counter_disagrees':row['recontacts']=9
 if label=='missing_load_active':row.pop('contact_load')
 if label=='selection_lost':inp['selected']=False
 if label=='parent_guard':row['route_stop_reason']='fixture_parent_guard'
 before=repr(vars(st));rr,rf,e=rt.update(row,st,ref,**inp);assert e['kind']=='stop' and e['requires_stop'] and repr(vars(st))==before and rr is row and rf is ref
 again=rt.update(row,st,ref,**inp)[2];assert again['kind']=='stop' and again['reason']==e['reason'];negative.append(label)
assert len(records)==6 and len(negative)==31
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,negative_cases=negative,fixture_events=sum(len(x['fixture_events']) for x in records),source_sha256=sources,collector_integrated=False,simulation_started=False,training_ready=False)
with (D/'RUNTIME_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,events=out['fixture_events'],negative_cases=len(negative))))
