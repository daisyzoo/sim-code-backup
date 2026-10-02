"""Explicit SYNTHETIC_NOT_PHYSICS native-file/provenance fixtures.
Four actual starts seed previously checked synthetic responses; static padding
only exercises full1200-frame file readers. No timestamp remapping. Zero-force
history uses zero filtered load in the already-unloaded eligibility range.
No dynamics/contact claim, genuine RGB, task admission or training data.
"""
from pathlib import Path
import sys,json,hashlib,copy,tempfile,shutil
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_box_entry_pose_live import inspect,source_contract,loads,verify_files,FILES
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();stage=w/'staged_box_entry_lift';fixture=w/'BOX_ENTRY_LIFT_COMBINED_CHECK.json';raw_fixture=json.loads(fixture.read_text());assert raw_fixture['complete'] and raw_fixture['all_completed_within_budget'];data={'rows':[]}
guarded=json.loads((w/'BOX_ENTRY_LIFT_GUARDED_CHECK.json').read_text());assert guarded['complete'] and guarded['passed']
for report in [raw_fixture,guarded]:
 for path,digest in report['source_sha256'].items():assert sha(path)==digest,path
selection=[('box_center_groups_r1',522),('box_center_groups_r1',983),('rear_box_rate_groups_r1',706),('rear_box_rate_groups_r1',1151)]
for row in raw_fixture['rows']:
 if (row['run'],row['start_step']) not in selection:continue
 data['rows'].append(dict(episode='layout_840001_push_box_to_bin',step=row['start_step'],plants=[dict(trace=row['trace'])]))
assert len(data['rows'])==4
base=Path(tempfile.mkdtemp(prefix='box_entry_native_files_'));model=HandModel(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
results=[];first=None
for ci,case in enumerate(data['rows']):
 parent=base/str(ci);ep=parent/'SYNTHETIC_NOT_PHYSICS';ep.mkdir(parents=True);src={};snap=parent/'source_snapshot'
 paths=[stage/n for n in ['collect_paired_sorting.py','waist_coordination_clearance.py','recontact_tracking.py','recontact_lifecycle.py','recontact_plan.py','recontact_plan_original.py','recontact_plan_deeper.py','recontact_scene.py','recontact_adapter.py','elbow_torso_hulls.json','causal_response_parameters.json','minimum_motion_recontact.py','minimum_motion_lifecycle.py','task_ik.py','task_ik_precision.py','joint_edge_command.py','joint_edge_adapter.py','rear_cop_route.py','box_center_preference_plan.py','box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py']]+[repo/n for n in ['simfoundry/scene_bridge/isaac_cfg.py','simfoundry/robots/g1_assets.py','simfoundry/calibration/sorting_station.py','third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json']]
 for path in paths:
  name=str(path.relative_to(repo));dst=snap/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dst);src[name]=sha(path)
 args={k:True for k in ['rear_box_entry_lift','rear_box_center_preference','rear_slow_drag','minimum_motion_recontact','rear_joint_edge_parent_seed_retry','rear_joint_edge_analytic_retry','precise_clearance_task_ik','recontact_interior_preference','unloaded_recontact_pose','rear_short_recovery','self_clearance_task_ik','rear_joint_xy_progress','region_causal_response','region_separate_measured_bounds','expert_top_contact_normal_hold','waist_coordinated_expert','bounded_coupled_ik']};args.update(expert_frontal_top_drag_step_m=.003,role='diagnostic',motion_protocol='waist_yaw_enabled_v1',waist_limit_rad=1.,policy_port=0,waist_probe=False,idle=False,push_assist=False,push_force_n=0,wait_force_n=0)
 (parent/'provenance.json').write_text(json.dumps(dict(args=args,source_sha256=src,fixture_scope=__doc__)))
 trace=copy.deepcopy(case['plants'][0]['trace']);start=case['step'];shift=0
 for event in trace:
  assert event['context']['observed_load_n']==0 and 0<=event['context']['filtered_load_n']<=.05
  event['context']['filtered_load_n']=0.
  event['context']['step']+=shift
  if event['planning'] is not None:
   event['planning']['step']+=shift
   assert shift==0
   assert ('lift' in event['planning']) if event.get('entry_lift_phase') else ('box_center_preference_pose' in event['planning'])
 end=start+len(trace)-1;scene=trace[0]['context']['scene'];side=scene['side'];inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';task='push_box_to_bin' if side=='right' else 'nudge_mailer_to_bin';n=1200
 q=np.zeros((n,23));u=np.zeros((n,23));q[start-1,12:23]=trace[0]['context']['previous_q'];u[start-1,12:23]=trace[0]['context']['previous_command']
 for event in trace:
  t=event['context']['step'];q[t,12:23]=event['context']['current'];u[t,12:23]=event['command']
 q[end+1:]=q[end];u[end+1:]=u[end]
 np.savez(ep/'raw.npz',q=q,action=u,task_id=task,collect_meta=json.dumps(dict(rear_box_entry_lift=True,rear_box_center_preference=True,rear_slow_drag=True,minimum_motion_recontact=True,rear_joint_edge_parent_seed_retry=True,task_ik_optimizer_ftol=1e-13,self_clearance_task_ik=True,recontact_interior_preference=True,unloaded_recontact_pose=True,unloaded_recontact_failure=None,assist_frames=0)))
 np.savez(ep/'trace.npz',**{key:np.tile(scene['target_xyz'],(n,1)),other:np.tile(scene['other_xyz'],(n,1))})
 np.savez(ep/'parcel_orientation.npz',**{key:np.tile(scene['target_quat'],(n,1)),other:np.tile(scene['other_quat'],(n,1))})
 capture=trace[-1];anchor=capture['captured_inactive_anchor_world'];center=capture['captured_center_local'];surface=capture['selected_surface_local_xy'];reference=capture['reference'];normal_anchor=np.array(capture['captured_normal_local_up']);events={e['context']['step']:copy.deepcopy(e) for e in trace}
 rows=[];coords=[];experts=[dict(step=0,mode='initial',target_xyz=[0.,0.,0.])];regions=[];holds=[];final=[];eventlog=[]
 for t in range(n):
  final.append(dict(step=t,phase='final_command',accepted=True,current=q[t,12:23].tolist(),previous=u[max(0,t-1),12:23].tolist(),command=u[t,12:23].tolist()))
  if not t:continue
  event=events.get(t);mode='approach' if t<start else 'top_cross' if t<end else 'top_press';f=dict(step=t,mode=mode,target_xyz=[0.,0.,0.],recontacts=trace[0]['context']['recontacts']);expert=dict(step=t,mode=mode,target_xyz=[0.,0.,0.]);c=dict(step=t,contact_normal_tracking=None,inactive_anchor=anchor);region=dict(step=t,active=False,center_local=center,selected_surface_local_xy=surface,abort_reason=None,mode=mode)
  if t>=start:
   f['contact_load']=dict(observed_vertical_load_n=0.,filtered_vertical_load_n=0.,applied_z_bias_m=0.,stored_z_bias_m=0.)
   regions.append(region)
  if event:
   event['old_inactive_anchor']=anchor;event['old_normal_anchor']=normal_anchor.tolist();event['runtime_fk_check']={s:dict(position_max_error_m=0.,rotation_max_error=0.) for s in ['left','right']};events[t]=event;eventlog.append(dict(step=t,**event));f['recontact_pose_phase']='measured_handover' if t==end else 'tracking'
   c.update(recontact_pose_override=event,controller_kind='verified_unloaded_recontact_joint_path',upper_q=q[t,12:23].tolist(),active_side=side,bounded_solver=True,task_inputs=None,contact_bout_yaw_tracking=None,terminal_joint_hold=False,joint_edge_refinement=dict(override=False),active_support_reference=reference,control_point_positions={side:capture['observed_support_xyz']})
   if t==end:
    f.update(target_xyz=capture['observed_support_xyz'],observed_support_xyz=capture['observed_support_xyz'],control_offset_local=reference['reference_local'],projected_support_reference=reference,push_x_anchor_m=None,approach_xy_bias_m=[0.,0.]);expert['target_xyz']=f['target_xyz']
   holds.append(dict(step=t,held=False,output_upper_command=u[t,12:23].tolist(),previous_upper_command=u[t-1,12:23].tolist(),current_upper_q=q[t,12:23].tolist()))
  elif t>end:
   eventlog.append(dict(step=t,kind='unchanged',reason='not_new_eligible_recovery'))
   current=model.fk(q[t,12:23],side)[2,:3];J=np.zeros((3,11))
   if t%20==0:
    for j in range(11):
     delta=np.zeros(11);delta[j]=1e-6;J[:,j]=.15*(model.fk(q[t,12:23]+delta,side)[2,:3]-model.fk(q[t,12:23]-delta,side)[2,:3])/(2e-6)
   c['contact_normal_tracking']=dict(current_local_up=current.tolist(),target_local_up=normal_anchor.tolist(),error=(.15*np.clip(.72*(normal_anchor-current),-.1,.1)).tolist(),angle_error_rad=float(np.arccos(np.clip(current@normal_anchor,-1,1))),weight_m=.15,jacobian=J.tolist())
  rows.append(f);coords.append(c);experts.append(expert)
 plan=dict(unloaded_recontact_pose=dict(interior_preference=dict(enabled=True,preferred_inset_m=.020,original_inset_m=.012,original_fallback=True,interpolated_path_check=True,measured_handover_inset_m=.01,training_ready=False)),region_approach=dict(enabled=True),rear_joint_xy_progress=dict(enabled=True),region_causal_response=dict(actual_core=dict(collision_core_size_xyz=scene['core_size']),decay=trace[0]['proposal']['decay']))
 plan['unloaded_recontact_pose']['minimum_motion_pose']=dict(enabled=True,alignment_abs_min=.8,preferred_inset_m=.020,seed_policy=['original_endpoint','current_observed'],lift_heights_m=[.015,.030,.060],original_fallback=True,whole_sampled_path_check=True,maximum_ticks=240,training_ready=False)
 plan.update(direction=-1,rear_cop_centering=dict(enabled=True),top_recontact=dict(drag_step_m=.0015,continuous_drag=True))
 plan['unloaded_recontact_pose']['box_center_preference']=dict(enabled=True,center_weight_per_m2=400.,parent='same_observation_minimum_motion',side='right',original_fallback=True,original_constraints_unchanged=True)
 plan['unloaded_recontact_pose']['entry_lift']=dict(enabled=True,side='right',original_entry_height_m=.84,nominal_lift_height_m=.845,measured_ready_frames=3,maximum_lift_ticks=40,combined_maximum_ticks=240,measured_unloaded_required=True,phase_boundary_guards=True,training_ready=False)
 payload={'frontal_bypass.json':dict(plan=plan,rows=rows),'coordination.json':coords,'expert_control.json':experts,'region_approach.json':dict(rows=regions),'recontact_pose.json':dict(rows=eventlog),'solved_contact_forces.json':dict(rows=[dict(after_action_step=t,parcel_contacts=[]) for t in range(n)]),'self_clearance.json':dict(rows=final,failure=None,requested_frames=n,recorded_frames=n),'terminal_joint_hold.json':dict(rows=holds)}
 for name,value in payload.items():(ep/name).write_text(json.dumps(value))
 result=inspect(ep);assert result['command_events']==len(trace) and result['handovers']==1
 results.append(dict(episode=case['episode'],recorded_start=case['step'],synthetic_start=start,events=len(trace),fixture=str(ep),passed=True));print(results[-1],flush=True)
 if first is None:first=(ep,start,end)
inactive_cases=[]
for original_ep in sorted((w/'rear_short_recovery_groups_r1').glob('case_*/layout_*')):
 if not (original_ep/'frontal_bypass.json').exists():continue
 plan=json.loads((original_ep/'frontal_bypass.json').read_text())['plan']
 if plan.get('region_approach',{}).get('enabled'):continue
 ep=base/('INACTIVE_'+original_ep.name);ep.mkdir()
 for name in FILES:
  if name=='recontact_pose.json':(ep/name).write_text(json.dumps(dict(rows=[])))
  elif (original_ep/name).exists():(ep/name).symlink_to((original_ep/name).resolve())
 result=verify_files(ep,stage);assert result['command_events']==0 and result['handovers']==0 and not result['selected']
 inactive_cases.append(dict(episode=original_ep.name,frames=result['frames'],source_sha256={n:sha(original_ep/n) for n in FILES if (original_ep/n).exists()}));print('inactive',original_ep.name,'passed',flush=True)
assert len(inactive_cases)==6
negative=[];ep,start,end=first
mutations=[
 ('frontal_bypass.json','missing_entry_metadata',lambda d:d['plan']['unloaded_recontact_pose'].pop('entry_lift')),
 ('frontal_bypass.json','extended_recovery_budget',lambda d:d['plan']['unloaded_recontact_pose']['entry_lift'].__setitem__('combined_maximum_ticks',280)),
 ('recontact_pose.json','missing_entry_phase',lambda d:d['rows'][0].pop('entry_lift_phase')),
 ('recontact_pose.json','early_lift_ready',lambda d:d['rows'][0].__setitem__('entry_lift_phase','lift_ready')),
 ('recontact_pose.json','unlogged_lift_normal_capture',lambda d:d['rows'][0].__setitem__('captured_normal_local_up',[0,0,1])),
 ('raw.npz','changed_final_action',None),
 ('frontal_bypass.json','changed_decay',lambda d:d['plan']['region_causal_response']['decay'].__setitem__(0,0.)),
 ('frontal_bypass.json','changed_collision_core',lambda d:d['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'].__setitem__(0,.2)),
 ('solved_contact_forces.json','wrong_load_alignment',lambda d:d['rows'][start-1]['parcel_contacts'].append(dict(shapes=['/robot/right_wrist_roll/mesh','/world/parcel_box/mesh'],force_world_N=[0.,0.,.01]))),
 ('frontal_bypass.json','false_filter',lambda d:d['rows'][start-1]['contact_load'].__setitem__('filtered_vertical_load_n',.001)),
 ('region_approach.json','missing_capture_center',lambda d:d['rows'][0].__setitem__('center_local',None)),
 ('recontact_pose.json','missing_event',lambda d:d['rows'].pop(0)),
 ('coordination.json','undeclared_path',lambda d:d[start-1].__setitem__('controller_kind','original')),
 ('self_clearance.json','short_episode',lambda d:d.__setitem__('recorded_frames',1199)),
 ('self_clearance.json','stopped_episode',lambda d:d.__setitem__('failure',dict(reason='stop'))),
 ('terminal_joint_hold.json','altered_action_chain',lambda d:d['rows'][0]['output_upper_command'].__setitem__(1,0.)),
 ('coordination.json','stale_post_capture_normal',lambda d:d[end]['contact_normal_tracking']['target_local_up'].__setitem__(0,.123)),
 ('region_approach.json','unlogged_center_change',lambda d:d['rows'][end-start+1]['center_local'].__setitem__(0,0.)),
]
for file,name,mutate in mutations:
 path=ep/file;original=path.read_bytes()
 try:
  if file=='raw.npz':
   with np.load(path) as z:values={k:z[k].copy() for k in z.files}
   values['action'][start,13]+=.001;np.savez(path,**values)
  else:
   value=json.loads(original);mutate(value);path.write_text(json.dumps(value))
  try:inspect(ep)
  except (AssertionError,ValueError):negative.append(name)
  else:raise AssertionError('Accepted native file corruption '+name)
 finally:path.write_bytes(original)
 print('rejected',name,flush=True)
provenance=ep.parent/'provenance.json';original=provenance.read_bytes();d=json.loads(original);d['args']['unloaded_recontact_pose']=False;provenance.write_text(json.dumps(d))
try:
 try:source_contract(ep)
 except AssertionError:negative.append('disabled_flag')
 else:raise AssertionError('Accepted disabled candidate')
finally:provenance.write_bytes(original)
d=json.loads(original);name=next(n for n in d['source_sha256'] if n.endswith('/recontact_plan.py'));path=ep.parent/'source_snapshot'/name;original_source=path.read_bytes();path.write_bytes(original_source+b'\n# tampered\n')
try:
 try:source_contract(ep)
 except AssertionError:negative.append('changed_archived_source')
 else:raise AssertionError('Accepted source corruption')
finally:path.write_bytes(original_source)
# Native wait episodes legitimately have no frontal plan; missing push plan rejects.
wait_case=base/'WAIT_SOURCE_CONTRACT';wait_case.mkdir();(wait_case/'source_snapshot').symlink_to((first[0].parent/'source_snapshot').resolve(),target_is_directory=True);(wait_case/'provenance.json').write_bytes((first[0].parent/'provenance.json').read_bytes());wait_ep=wait_case/'wait';wait_ep.mkdir();np.savez(wait_ep/'raw.npz',task_id='wait_no_package',collect_meta=json.dumps(dict(rear_box_entry_lift=True,rear_box_center_preference=True,rear_slow_drag=True,minimum_motion_recontact=True,rear_joint_edge_parent_seed_retry=True,task_ik_optimizer_ftol=1e-13,self_clearance_task_ik=True,recontact_interior_preference=True,unloaded_recontact_pose=True)));assert source_contract(wait_ep)==stage
np.savez(wait_ep/'raw.npz',task_id='push_box_to_bin',collect_meta=json.dumps(dict(rear_box_entry_lift=True,rear_box_center_preference=True,rear_slow_drag=True,minimum_motion_recontact=True,rear_joint_edge_parent_seed_retry=True,task_ik_optimizer_ftol=1e-13,self_clearance_task_ik=True,recontact_interior_preference=True,unloaded_recontact_pose=True)))
try:source_contract(wait_ep)
except AssertionError:negative.append('missing_push_plan')
else:raise AssertionError('Accepted push without plan')
# Explicit nonzero filtering/sign and previous-step alignment on native packets.
packets=[dict(after_action_step=0,parcel_contacts=[dict(shapes=['right_wrist_roll','/parcel_box/mesh'],force_world_N=[0,0,-4.])]),dict(after_action_step=1,parcel_contacts=[])]
fr=[dict(step=1,contact_load=dict(observed_vertical_load_n=4.,filtered_vertical_load_n=1.)),dict(step=2,contact_load=dict(observed_vertical_load_n=0.,filtered_vertical_load_n=.75))];assert loads(fr,packets,'right','parcel_box')=={1:(4.,1.),2:(0.,.75)}
out=dict(passed=True,scope=__doc__,fixtures=results,inactive_cases=inactive_cases,total_events=sum(r['events'] for r in results),rejected_corruptions=negative,nonzero_previous_contact_filter_checked=True,wait_source_contract_checked=True,fixture_root=str(base),fixture_sha256=sha(fixture),source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_box_entry_pose_live.py',w/'audit_box_entry_source_contract.py',w/'audit_box_entry_events.py',w/'audit_box_entry_plan.py',w/'audit_box_entry_lift_events.py',w/'audit_box_center_events.py',w/'audit_box_center_plan.py',w/'BOX_ENTRY_LIFT_GUARDED_CHECK.json',w/'audit_box_center_preference_plan.py',w/'audit_slow_drag_plan.py',w/'box_entry_step_contract.py',w/'audit_recontact_interior_events.py',w/'audit_recontact_pose_normal.py']},physical_validation=False,training_ready=False)
(stage/'NATIVE_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',out['total_events'],len(negative),flush=True)
