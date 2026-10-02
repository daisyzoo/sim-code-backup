"""Actual parent/candidate state classes, off parity and captured-point continuity.
Constructed contact/guard fixtures, not physical rollout or collector wiring.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,copy,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(W),str(S),str(ROOT)]
from front_cop_route_micro import FrontCopRouteState as Parent
from front_initial_center_cop_route import FrontCopRouteState as Candidate
from front_initial_center_adapter import apply
from front_initial_center_reference_ledger import verified_reference_lifetimes
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from simfoundry.data.projected_support_reference import projected_support_reference
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((W/'FRONT_INITIAL_CENTER_STATE_PREPARATION.json').read_text())
for row in prep['changes']:
 source=Path(row['source']);target=Path(row['target']);assert sha(source)==row['source_sha256'] and sha(target)==row['target_sha256']
 restored=target.read_text()
 for pair in reversed(row['replacements']):
  assert restored.count(pair['new'])==1;restored=restored.replace(pair['new'],pair['old'])
 assert restored==source.read_text()
guard=ClearanceGuard(ROOT,S);probe=json.loads((W/'FRONT_INITIAL_CENTER_LANDING_PROBE.json').read_text());records=[]
for original in probe['records']:
 z=original['scene'];side=z['side'];target=z['target_xyz'];other=z['other_xyz'];quat=z['target_quat'];other_quat=z['other_quat'];size=z['core_size'];other_size=z['other_size'];direction=1 if side=='left' else -1
 scene=RecontactScene(guard,side,target,quat,size,other,other_quat,other_size)
 ep=next((W/'fresh_closed_peak_trials_r1').glob('case_*/'+original['episode']));fr=json.loads((ep/'frontal_bypass.json').read_text());parent_plan=fr['plan'];first=next(r for r in fr['rows'] if r['step']==original['step'])
 def new(cls):
  return cls(SimpleNamespace(plan=copy.deepcopy(parent_plan)),side,tuple(size),obstacle_size=tuple(other_size),guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=.9,tilt_recontact_rad=.03,recontact_on_route_change=True,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005,route_clearance_m=.012,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=.002,edge_speed_enabled=True,edge_core_size=size)
 args=(target,target,other,size[0]/2,other_size[0]/2)
 kwargs=dict(tip=first['observed_support_xyz'],quat=quat,obstacle_quat=other_quat,control_offset_local=first['control_offset_local'],load_n=0.,hand_obstacle_gap_m=first['hand_obstacle_gap_m'])
 a,b=new(Parent),new(Candidate);assert a.update(*args,**kwargs)==b.update(*args,**kwargs)
 tests=[]
 for phase,load,gap,moved in [('top_cross',0.,.1,False),('top_descend',0.,.1,False),('top_press',5.,.1,False),('top_push',5.,.1,False),('top_push',0.,.1,False),('top_push',5.,.001,False),('top_push',5.,.1,True)]:
  aa,bb=copy.deepcopy(a),copy.deepcopy(b)
  for state in [aa,bb]:
   state.top_mode=phase;state.settled=2;state.load.filtered_n=5.;state.command=tuple(kwargs['tip']);state.lost_contact_steps=2;state.descent_z=kwargs['tip'][2]
  obs=list(other);obs[1]+=.02 if moved else 0.
  inp=dict(kwargs,load_n=load,hand_obstacle_gap_m=gap)
  ra=aa.update(target,target,obs,size[0]/2,other_size[0]/2,**inp);rb=bb.update(target,target,obs,size[0]/2,other_size[0]/2,**inp)
  assert ra==rb,(original['episode'],phase)
  tests.append(dict(mode=phase,load=load,gap=gap,moved=moved,output_mode=rb['mode'],off_exact_parity=True))
 chosen=min([x for x in original['attempts'] if x['accepted_endpoint'] and x['nominal_path']['independently_accepted']],key=lambda v:v['objective'])
 q=np.array(chosen['candidate_q']);detail=scene.details(q);pose=detail['hand_pose'];center=detail['vertex_local'];reference=projected_support_reference(guard.model.vertices[side],pose[:3,:3],scene.rotation[:,2],center_local=center)
 tip=pose[:3,3]+pose[:3,:3]@reference['reference_local'];local=scene.rotation.T@(tip-scene.target)
 event=dict(kind='handover',captured_center_local=center.tolist(),context=dict(recontacts=0),measured_ready_count=3,reference={k:reference[k].tolist() for k in ['reference_local','center_local','lowest_vertex_local','world_normal']},observed_support_xyz=tip.tolist(),selected_surface_local_xy=local[:2].tolist())
 b=new(Candidate);row=b.update(*args,**kwargs);before=copy.deepcopy(b)
 for bad in [dict(event,kind='stop'),dict(event,measured_ready_count=2),dict(event,context=dict(recontacts=1))]:
  state=copy.deepcopy(before);saved=copy.deepcopy(vars(state))
  try:apply(row,state,reference,bad,object_xyz=target,object_rotation=scene.rotation);raise AssertionError('Invalid transition accepted')
  except ValueError:pass
  assert repr(vars(state))==repr(saved)
 updated,ref=apply(row,b,reference,event,object_xyz=target,object_rotation=scene.rotation)
 assert np.max(abs(np.array(updated['target_xyz'])-tip))<1e-12 and b.recontacts==0
 next_kwargs=dict(kwargs,tip=tip.tolist(),control_offset_local=ref['reference_local'].tolist(),load_n=0.,hand_obstacle_gap_m=.1)
 nextrow=b.update(target,target,other,size[0]/2,other_size[0]/2,**next_kwargs)
 expected=scene.target+scene.rotation@np.r_[local[:2],scene.core[2]/2]
 assert np.max(abs(np.array(nextrow['parcel_top_xyz'])-expected))<1e-12
 assert np.max(abs(np.array(nextrow['target_xyz'])[:2]-expected[:2]))<1e-12
 assert np.max(abs((expected-tip)[:2]+scene.rotation[:2,2]*(local[2]-scene.core[2]/2)))<1e-12
 # All route guards remain in front of captured surface/loading logic.
 stopped=copy.deepcopy(b).update(target,target,other,size[0]/2,other_size[0]/2,**dict(next_kwargs,hand_obstacle_gap_m=.001))
 assert stopped['mode']=='front_guard_lift'
 # Real state class: inner loss-of-load resets after surface computation.
 internal=copy.deepcopy(b);internal.top_mode='top_push';internal.lost_contact_steps=2;internal.load.filtered_n=0.
 inside=internal.update(target,target,other,size[0]/2,other_size[0]/2,**next_kwargs)
 assert inside['recontacts']==1 and inside['last_recontact_reason']=='lost_contact'
 assert internal.selected_surface_local_xy is None
 after=internal.update(target,target,other,size[0]/2,other_size[0]/2,**next_kwargs)
 def ledger(rows):
  return verified_reference_lifetimes([dict(r,step=i+1,front_initial_captured_center_local=center.tolist()) for i,r in enumerate(rows)],{1:event})
 inside_ledger=ledger([updated,nextrow,inside,after])
 assert set(inside_ledger['centers'])=={1,2,3,4} and set(inside_ledger['surface_local_by_step'])=={1,2,3}
 assert np.max(abs(np.array(inside['parcel_top_xyz'])-expected))<1e-12
 assert np.max(abs(np.array(after['parcel_top_xyz'])-expected))>.001
 # Real outer route transition resets before calling the base surface method.
 external=copy.deepcopy(b);external.top_mode='top_push';external.load.filtered_n=5.
 external.route_stage='lateral_y' if b.route_stage=='front_x' else 'front_x'
 outside=external.update(target,target,other,size[0]/2,other_size[0]/2,**dict(next_kwargs,load_n=5.))
 assert outside['direction_change_recontact']['restarted'] is True
 assert outside['recontacts']==1 and outside['last_recontact_reason']=='front_route_direction_change'
 outside_ledger=ledger([updated,nextrow,outside])
 assert set(outside_ledger['centers'])=={1,2,3} and set(outside_ledger['surface_local_by_step'])=={1,2}
 assert np.max(abs(np.array(outside['parcel_top_xyz'])-expected))>.001
 b._start_recontact(tip,'test_actual_parent_reset');assert b.selected_surface_local_xy is None and b.recontacts==1
 records.append(dict(episode=original['episode'],off_cases=tests,measured_reference_fixture_continuity=True,invalid_transitions_rejected_without_mutation=True,front_guard_precedence=True,recovery_clears_selected_surface=True,inner_reset_ledger=inside_ledger,outer_reset_ledger=outside_ledger,fixture_scope='Manufactured measured endpoint; does not prove the lifecycle reaches it.'))
 print(original['episode'],'off',len(tests),'handover continuity passed',flush=True)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_inverse_diff_verified=True,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_initial_center_adapter.py',W/'front_initial_center_reference_ledger.py',W/'FRONT_INITIAL_CENTER_STATE_PREPARATION.json']},collector_integrated=True,simulation_started=False,training_ready=False)
with (W/'FRONT_INITIAL_CENTER_REFERENCE_LIFETIME_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
