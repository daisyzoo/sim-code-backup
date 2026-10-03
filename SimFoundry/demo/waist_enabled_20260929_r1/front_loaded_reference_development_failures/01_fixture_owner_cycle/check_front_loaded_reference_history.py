"""Real parent controller plus cap adapter on explicitly synthetic loaded histories.
Recorded measured handovers initialize two actual collision-core scenes. The
following observations are manufactured, not predictions or physical outcomes.
Independent checks cover command memory, unchanged normal/safety bookkeeping,
limited advance for a stationary object, and explicit rejection before action.
"""
from pathlib import Path
from types import SimpleNamespace
import copy, datetime, hashlib, json, sys
import numpy as np
W=Path(__file__).resolve().parent; ROOT=W.parents[1]; S=W/'staged_front_initial_center'
sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_initial_center_cop_route import FrontCopRouteState
from front_initial_center_adapter import apply
from front_loaded_reference_adapter import admit
from peak_load_update_trace import TracedPeakLoadControl
from simfoundry.data.top_contact_bypass import rotation_xyzw
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=W/'FRONT_LOADED_REFERENCE_HISTORY_CHECK.json';assert not out.exists()
report=dict(status='running',scope=__doc__,records=[],negative=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_loaded_reference_adapter.py',W/'front_initial_loaded_reference_cap.py']})
def save():
 report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();out.write_text(json.dumps(report,indent=2))
def neutral(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,dict):return {k:neutral(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [neutral(v) for v in x]
 if hasattr(x,'__dict__'):return {k:neutral(v) for k,v in vars(x).items() if k not in ('owner',)}
 return x
try:
 save()
 for seed,task in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
  ep=W/'front_initial_physical_r1'/f'case_{seed}'/f'layout_{seed}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());events=json.loads((ep/'front_initial_center.json').read_text());event=next(r for r in events['rows'] if r['kind']=='handover');z=event['context']['scene'];size=z['core_size'];side=z['side'];other=z['other_xyz'];rot=np.asarray(rotation_xyzw(z['target_quat']));reference={k:np.array(v) for k,v in event['reference'].items()};plan=fr['plan']
  assert np.allclose(size,plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'],atol=1e-10,rtol=0)
  for p in [ep/'front_initial_center.json',ep/'frontal_bypass.json',S/'PREPARATION.json']:report['source_sha256'][str(p)]=sha(p)
  for moving in [False,True]:
   state=FrontCopRouteState(SimpleNamespace(plan=copy.deepcopy(plan)),side,tuple(size),obstacle_size=tuple(z['other_size']),guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=.9,tilt_recontact_rad=.03,recontact_on_route_change=True,diagonal_entry=True,retain_micro_repair_contact=True,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005,route_clearance_m=.012,recontact_travel_z=.86,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=.002,edge_speed_enabled=True,edge_core_size=size)
   state.load=TracedPeakLoadControl(5.,min_bias_m=-.006);state.load.bind_owner(state)
   seed_row=copy.deepcopy(next(r for r in fr['rows'] if r['step']==event['step']));seed_row,_=apply(seed_row,state,reference,event,object_xyz=z['target_xyz'],object_rotation=rot)
   runtime=SimpleNamespace(center_local=np.array(event['captured_center_local']),rows=[copy.deepcopy(event)])
   tip=np.array(event['observed_support_xyz']);tip[2]=seed_row['parcel_top_xyz'][2]
   changed=loaded=holds=0;maxoffset=0.;history=[];previous_delta=np.zeros(2)
   for i in range(1,81):
    t=event['step']+i;target=np.array(z['target_xyz']);target[:2]+=previous_delta
    before_xy=copy.deepcopy(state.last_emitted_xy)
    state.load.observe(action_step=t,after_action_step=t-1,vertical_load_n=[5.]*24)
    row=state.update(target,target,other,size[0]/2,z['other_size'][0]/2,tip=tip,quat=z['target_quat'],obstacle_quat=z['other_quat'],control_offset_local=reference['reference_local'],load_n=5.,hand_obstacle_gap_m=.1,slip_contact=dict(valid=True,normal_load_n=5.,weighted_contact_local=[*event['selected_surface_local_xy'],size[2]/2]))
    before=neutral(state);off=copy.deepcopy(state);off_result,off_stop=admit(enabled=False,row=row,state=off,runtime=runtime,previous_xy=before_xy,normal_load_n=5.,step=t);assert off_result is row and off_stop is None and neutral(off)==before
    result,stop=admit(enabled=True,row=row,state=state,runtime=runtime,previous_xy=before_xy,normal_load_n=5.,step=t)
    assert stop is None,(seed,moving,i,stop)
    after=neutral(state)
    assert {k:v for k,v in before.items() if k not in ('command','last_emitted_xy')}=={k:v for k,v in after.items() if k not in ('command','last_emitted_xy')}
    assert result['target_xyz'][2]==row['target_xyz'][2] and result['contact_load']==row['contact_load']
    advice=result['loaded_reference_cap']
    if advice['applied']:
     loaded+=1;changed+=int(advice['changed']);p=np.array(row['target_xyz'][:2]);prev=np.array(before_xy);cmd=np.array(result['target_xyz'][:2]);surface=np.array(row['parcel_top_xyz'][:2]);actual=np.array(row['observed_support_xyz'][:2]);
     assert np.all(abs(cmd-prev)<=.003+1e-10) and np.all(abs(cmd-actual)<=.030+1e-10) and np.all(abs(cmd-surface)<=.010+1e-10)
     assert np.all(cmd>=np.minimum(prev,p)-1e-10) and np.all(cmd<=np.maximum(prev,p)+1e-10)
     assert tuple(state.command)==tuple(result['target_xyz']) and tuple(state.last_emitted_xy)==tuple(cmd)
     assert np.allclose(row['cop_slip_following']['previous_command_xy'],prev,atol=1e-12,rtol=0)
     maxoffset=max(maxoffset,float(max(abs(cmd-surface))));holds+=int(max(abs(cmd-prev))<1e-10)
     # Only a declared synthetic following observation, not a physical model.
     if moving:previous_delta+=np.clip(cmd-surface,-.00025,.00025)
     tip[:2]=cmd
    history.append(dict(step=t,mode=result['mode'],command=list(result['target_xyz']),changed=advice['changed']))
   assert loaded>=60 and changed>=20
   if not moving:assert holds>=30
   report['records'].append(dict(episode=ep.name,synthetic_object_translation=moving,frames=80,loaded_frames=loaded,changed_frames=changed,held_frames=holds,max_world_axis_material_offset_m=maxoffset,synthetic_object_delta_xy=previous_delta.tolist(),history=history));save()
   if not moving:
    # An impossible material window must issue no command and leave state intact.
    bad=copy.deepcopy(row);bad['parcel_top_xyz']=list(bad['parcel_top_xyz']);bad['parcel_top_xyz'][0]+=1.;frozen=neutral(state);result,stop=admit(enabled=True,row=bad,state=state,runtime=runtime,previous_xy=state.last_emitted_xy,normal_load_n=5.,step=t)
    assert stop and stop['kind']=='stop' and result['loaded_reference_cap']['command_xy'] is None and neutral(state)==frozen
    report['negative'].append(dict(case=ep.name+'_empty_feasible_set',rejected_before_action=True))
    for guard_key in ['route_stop_reason','release_reason']:
     guarded=copy.deepcopy(bad);guarded[guard_key]='parent_guard_fixture';result,stop=admit(enabled=True,row=guarded,state=state,runtime=runtime,previous_xy=None,normal_load_n=5.,step=t);assert stop is None and result['target_xyz']==guarded['target_xyz'] and neutral(state)==frozen
     report['negative'].append(dict(case=ep.name+'_'+guard_key,parent_precedence=True))
    for label in ['future_capture','unbound_center','two_ready_only','missing_event','second_handover']:
     wrong=copy.deepcopy(runtime)
     if label=='future_capture':wrong.rows[0]['step']=t+1
     if label=='unbound_center':wrong.center_local[0]+=.001
     if label=='two_ready_only':wrong.rows[0]['measured_ready_count']=2
     if label=='missing_event':wrong.rows=[]
     if label=='second_handover':wrong.rows.append(copy.deepcopy(wrong.rows[0]))
     rejected=False
     try:admit(enabled=True,row=row,state=state,runtime=wrong,previous_xy=state.last_emitted_xy,normal_load_n=5.,step=t)
     except ValueError:rejected=True
     assert rejected and neutral(state)==frozen
     report['negative'].append(dict(case=ep.name+'_'+label,rejected=True))
 report.update(status='complete',passed=True);save();print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','records']},indent=2));print('history records',[(x['episode'],x['synthetic_object_translation'],x['loaded_frames'],x['held_frames']) for x in report['records']])
except Exception as e:report.update(status='failed',error=repr(e));save();raise
