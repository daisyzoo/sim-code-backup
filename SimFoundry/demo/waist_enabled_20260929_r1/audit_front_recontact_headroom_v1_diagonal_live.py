"""Independent force-packet, geometric route and COP-waypoint reconstruction."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog


def independent_corner(obj, other, radius, other_radius, direction, goal_x, clear):
 """Independent epigraph LP for minimum rectangle separation along each segment."""
 combined=radius[:2]+other_radius[:2]
 final=direction*max(.205,direction*obj[1]+.16)
 near=other[1]-direction*(combined[1]+clear+.003)
 corner=float(obj[1]+direction*max(0.,min(direction*(near-obj[1]),direction*(final-obj[1]))))
 points=np.array([obj[:2],[goal_x,corner],[goal_x,final]],dtype=float)
 minima=[]
 for a,b in zip(points,points[1:]):
  start=a-other[:2];delta=b-a
  intercept=np.r_[start-combined,-start-combined];slope=np.r_[delta,-delta]
  solved=linprog([0.,1.],A_ub=np.column_stack((slope,-np.ones(4))),b_ub=-intercept,bounds=[(0.,1.),(None,None)],method='highs')
  assert solved.success,'Independent segment LP failed'
  minima.append(float(solved.fun))
 table=float(min(np.min(points[:,0]-radius[0]-.28),np.min(.88-points[:,0]-radius[0]),np.min(points[:,1]-radius[1]+.75),np.min(.75-points[:,1]-radius[1])))
 return dict(goal_y=corner,points=points,minimum_axis_gap_m=min(minima),minimum_table_margin_m=table,length_m=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()),eligible=bool(table>=.005-1e-10 and min(minima)>=clear-1e-10))

def reconstruct(rows, plan, tr, ori, packets, key):
 drive_step=plan['front_cop_slip_following']['drive_step_m']
 edge_config=plan['front_cop_slip_following'].get('edge_speed',{});assert type(edge_config.get('enabled',False)) is bool
 assert type(drive_step) in (int,float) and np.isfinite(drive_step) and .001<=drive_step<=.003
 side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};direction=-1 if side=='right' else 1;rot={k:Rotation.from_quat(ori[k]).as_matrix() for k in sizes};g=plan['front_route_live_guards'];clear=g['clearance_before_lateral_m'];first=rows[0]['step'];radii={k:abs(rot[k])@sizes[k]/2 for k in sizes};initial_x=tr[other][first,0]-radii[other][first,0]-radii[key][first,0]-clear-.003;final_y=direction*max(.205,direction*tr[key][first,1]+.16)
 stage='front_x';hold=float(plan['initial_target_xyz'][1]);safe_count=0;anchor=None;last_anchor=None;previous=None;prior_step=None;previous_stage=None;errors=[];records=[]
 def near(t,name,a,b):
  error=float(np.max(abs(np.asarray(a)-np.asarray(b))))
  if not np.isfinite(error) or error>2e-6:errors.append([t,name,error])
 for row_index,row in enumerate(rows):
  t=row['step'];f=row.get('cop_slip_following');obj=tr[key][t];r=rot[key][t]
  if prior_step is not None and t!=prior_step+1:errors.append([t,'noncontiguous_observations'])
  prior_step=t
  if f is None:errors.append([t,'missing_feedback_trace']);previous=np.asarray(row['target_xyz'][:2]);continue
  gap=float(tr[other][t,0]-obj[0]-radii[other][t,0]-radii[key][t,0]);goal_x=min(initial_x,tr[other][t,0]-radii[other][t,0]-radii[key][t,0]-clear-.003)
  if row['mode']!='front_guard_lift':
   if stage=='front_x':
    safe_count=safe_count+1 if gap>=clear else 0
    if gap>=clear+g['recovery_resume_extra_m'] or safe_count>=g['nominal_clearance_confirmation_frames']:stage='lateral_y'
   elif gap<clear-g['recovery_hysteresis_m']:stage='front_x';hold=float(obj[1]);safe_count=0
   near(t,'geometric_goal_x',row['route_goal_x'],goal_x)
   if row['route_stage']!=stage:errors.append([t,'geometric_route_stage'])
  phase_reset=previous_stage is not None and stage!=previous_stage
  if f.get('route_anchor_reset') is not phase_reset:errors.append([t,'route_anchor_reset'])
  if f.get('previous_route_stage')!=previous_stage:errors.append([t,'previous_route_stage'])
  if phase_reset:anchor=last_anchor=None
  previous_stage=stage
  if not edge_config.get('enabled',False) and 'edge_speed' in f:errors.append([t,'unexpected_edge_speed'])
  if row['mode']!='top_push':
   if row.get('front_diagonal_entry') is not None:errors.append([t,'diagonal_outside_push'])
   if edge_config.get('enabled',False):
    e=f.get('edge_speed',{})
    if e.get('applied') is not False or e.get('reason')!='parent_non_push_mode' or e.get('drive_step_m')!=drive_step:errors.append([t,'edge_override_outside_push'])
   if f.get('override') or f.get('reason')!='original_non_push_mode':errors.append([t,'override_outside_push'])
   anchor=last_anchor=None;previous=np.asarray(row['target_xyz'][:2]);continue
  packet=packets.get(t-1);points=[];weights=[]
  if packet:
   near(t,'previous_packet_pose_alignment',packet['post_action_pose'][key],obj)
   for c in packet['parcel_contacts']:
    slots=[i for i,label in enumerate(c['shapes']) if '/'+actor+'/' in label]
    if len(slots)!=1 or not any(side+'_wrist' in label for label in c['shapes']):continue
    force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@r[:,2])
    if load>.05:points.append(c['position_world']);weights.append(load)
  diagonal=False;diagonal_goal_y=None
  vertical=sum(abs(float(c['force_world_N'][2])) for c in packet['parcel_contacts'] if any(side+'_wrist_roll' in label for label in c['shapes']) and any('/'+actor+'/' in label for label in c['shapes'])) if packet else 0.
  dlog=row.get('front_diagonal_entry')
  expected_diagonal=bool(plan.get('front_diagonal_entry',{}).get('enabled',False) and stage=='front_x' and vertical>=.3)
  if expected_diagonal:
   proposed=independent_corner(obj,tr[other][t],radii[key][t],radii[other][t],direction,goal_x,clear)
   diagonal=proposed['eligible'];diagonal_goal_y=proposed['goal_y']
   if dlog is None:errors.append([t,'missing_diagonal_proposal'])
   else:
    if dlog.get('selected') is not diagonal:errors.append([t,'diagonal_selection'])
    if dlog.get('reason')!=('current_observed_envelope_segment_clear' if diagonal else 'original_axis_fallback'):errors.append([t,'diagonal_reason'])
    proposal=dlog.get('proposal',{})
    if proposal.get('eligible') is not diagonal:errors.append([t,'diagonal_proposal_eligibility'])
    for name in ['points','minimum_axis_gap_m','minimum_table_margin_m','length_m']:
     if name not in proposal:errors.append([t,'missing_diagonal_'+name])
     else:near(t,'diagonal_'+name,proposal[name],proposed[name])
    if diagonal:
     if 'goal_y' not in dlog:errors.append([t,'missing_diagonal_goal'])
     else:near(t,'diagonal_goal',dlog['goal_y'],diagonal_goal_y)
  elif dlog is not None:errors.append([t,'unexpected_diagonal_proposal'])
  if not weights or sum(weights)<.3:
   if edge_config.get('enabled',False):
    e=f.get('edge_speed',{})
    if e.get('applied') is not False or e.get('reason')!='no_current_loaded_cop' or e.get('drive_step_m')!=drive_step:errors.append([t,'edge_override_without_load'])
   if f.get('override') or f.get('reason')!='no_valid_current_loaded_cop':errors.append([t,'override_without_current_load'])
   anchor=last_anchor=None;previous=np.asarray(row['target_xyz'][:2]);continue
  if not f.get('override'):errors.append([t,'missing_declared_loaded_override']);previous=np.asarray(row['target_xyz'][:2]);continue
  cop=np.average(points,axis=0,weights=weights);local=r.T@(cop-obj)
  effective_step=drive_step
  edge_cfg=plan['front_cop_slip_following'].get('edge_speed',{})
  if edge_cfg.get('enabled',False):
   assert edge_cfg['minimum_drive_step_m']==.001 and edge_cfg['warning_distance_m']==.010
   half=np.asarray(edge_cfg['actual_core_size_xyz'])[:2]/2
   drive_axis=0 if stage=='front_x' else 1;drive_sign=-1 if drive_axis==0 else direction
   ray=drive_sign*r[drive_axis,:];distances=[]
   if diagonal:
    world_direction=np.array([goal_x,diagonal_goal_y])-obj[:2];norm=np.linalg.norm(world_direction)
    if norm>1e-12:ray=r.T@np.r_[world_direction/norm,0.]
   if np.all(abs(local[:2])<=half):
    for j in range(2):
     if abs(ray[j])>1e-10:distances.append(((half[j] if ray[j]>0 else -half[j])-local[j])/ray[j])
   forward_distance=max(0.,min(distances)) if distances else 0.
   effective_step=.001+(drive_step-.001)*min(1.,forward_distance/.010)
   e=f.get('edge_speed')
   if e is None:errors.append([t,'missing_edge_speed'])
   else:
    for name,value in [('drive_step_m',effective_step),('forward_core_distance_m',forward_distance),('warning_distance_m',.010),('minimum_drive_step_m',.001),('nominal_step_m',drive_step)]:
     if name not in e:errors.append([t,'missing_edge_'+name])
     else:near(t,'edge_'+name,e[name],value)
    if e.get('applied') is not True or e.get('reason')!='current_drive_edge':errors.append([t,'edge_applied_state'])
  if anchor is None:anchor=local.copy()
  world=obj+r@anchor;feed=np.zeros(2) if last_anchor is None else world[:2]-last_anchor[:2];goal=np.array([goal_x,diagonal_goal_y if diagonal else (hold if stage=='front_x' else final_y)]);error=goal-obj[:2];distance=np.linalg.norm(error);drive=error*min(effective_step,distance)/distance if distance else np.zeros(2);raw_correction=.05*(world[:2]-cop[:2]);axis=error/distance if distance else np.zeros(2);removed=(np.dot(raw_correction,error)/np.dot(error,error))*error if distance else np.zeros(2);correction=raw_correction-removed;base=np.asarray(row['observed_support_xyz'][:2]) if previous is None else previous;ref=np.asarray(row['observed_support_xyz'][:2]);desired=base+feed+drive+correction;bounded=np.clip(desired,ref-.030,ref+.030);command=base+np.clip(bounded-base,-.003,.003)
  compare={'command_xy':command,'previous_command_xy':base,'reference_xy':ref,'anchor_local':anchor,'measured_cop_local':local,'object_anchor_translation_xy':feed,'drive_xy':drive,'slip_correction_xy':correction,'raw_slip_correction_xy':raw_correction,'drive_direction_xy':axis,'removed_parallel_correction_xy':removed,'command_delta_xy':command-base,'command_reference_lead_xy':command-ref}
  for name,value in compare.items():
   if name not in f:errors.append([t,'missing_'+name])
   else:near(t,name,f[name],value)
  # Parent FrontTopRouteState's cross-axis target, derived independently.
  # A recontact clears internal command; top_press does not store its emitted XY.
  parent_base=base if row_index and rows[row_index-1]['mode']=='top_push' else ref
  parent_desired=ref+np.clip(goal-obj[:2],-.012,.012)
  parent_xy=parent_base+np.clip(parent_desired-parent_base,-.003,.003)
  active_axis=0 if stage=='front_x' else 1;cross_axis=1-active_axis
  emitted=command.copy();emitted[cross_axis]=base[cross_axis]+np.clip(parent_xy[cross_axis]-base[cross_axis],-.003,.003)
  if diagonal:
   emitted=command.copy();mix=f.get('diagonal_entry_control')
   if 'route_axis_control' in f:errors.append([t,'axis_mix_in_diagonal'])
   if not mix or mix.get('both_xy_from_cop') is not True or mix.get('original_step_and_reference_bounds') is not True:errors.append([t,'missing_diagonal_control'])
   elif 'goal_xy' not in mix:errors.append([t,'missing_diagonal_control_goal'])
   else:near(t,'diagonal_control_goal',mix['goal_xy'],goal)
  else:
   if 'diagonal_entry_control' in f:errors.append([t,'diagonal_control_outside_selected'])
   mix=f.get('route_axis_control')
   if mix is None:errors.append([t,'missing_route_axis_control'])
   else:
    if mix.get('active_axis')!=active_axis:errors.append([t,'wrong_active_axis'])
    for name,value in [('parent_xy',parent_xy),('original_cop_xy',command),('emitted_xy',emitted)]:
     if name not in mix:errors.append([t,'missing_axis_'+name])
     else:near(t,'axis_'+name,mix[name],value)
  near(t,'actual_waypoint',row['target_xyz'][:2],emitted)
  for name,value in [('desired_lead_clipped',bool(np.any(abs(bounded-desired)>1e-12))),('retained_slew_lag_outside_lead',bool(np.any(abs(command-ref)>.030+1e-9)))]:
   # Near threshold float32 geometry can change a boolean; retain distance evidence.
   boundary=np.min(abs(abs(desired-ref)-.030)) if name=='desired_lead_clipped' else np.min(abs(abs(command-ref)-.030))
   if boundary>2e-6 and f.get(name)!=value:errors.append([t,name])
  records.append(dict(step=t,normal_load_n=sum(weights),independent_cop_local_m=local.tolist(),goal_xy=goal.tolist(),command_xy=emitted.tolist(),waypoint_error_m=float(np.max(abs(emitted-row['target_xyz'][:2])))))
  previous=np.asarray(row['target_xyz'][:2]);last_anchor=world
 return records,errors

if __name__=='__main__':
 p=Path(sys.argv[1]).resolve();log=json.loads((p/'frontal_bypass.json').read_text());args=json.loads((p.parent/'provenance.json').read_text())['args'];enabled=args.get('front_cop_route_axis',False) and args.get('front_cop_phase_anchor',False) and args.get('front_cop_slip_following',False) and log['plan'].get('front_route_selected',False);records=[];errors=[]
 if enabled:
  config=log['plan'].get('front_diagonal_entry',{})
  assert bool(config.get('enabled',False))==bool(args.get('front_diagonal_entry',False))
  if config.get('enabled',False):
   assert config['minimum_vertical_load_n']==.3 and config['planning_clearance_m']==args['expert_front_clearance_m'] and config['corner_reserve_m']==.003 and config['table_margin_m']==.005 and config['actual_direction_edge_ray'] and config['original_guard_priority'] and config['original_axis_fallback']
  c=log['plan']['front_cop_slip_following'];assert c['enabled'] and c['route_axis_only'] and c['reset_anchor_on_route_change'] and c['feedback_projection']=='orthogonal_to_current_goal_direction' and type(c['drive_step_m']) in (int,float) and .001<=c['drive_step_m']<=.003 and c['drive_step_m']==args.get('front_cop_drive_step_m',.001) and c['feedback_gain']==.05 and c['max_step_m']==.003 and c['max_reference_lead_m']==.030
  edge=c.get('edge_speed',{})
  assert bool(edge.get('enabled',False))==bool(args.get('front_cop_edge_speed',False))
  if edge.get('enabled',False):
   import ast
   provenance=json.loads((p.parent/'provenance.json').read_text())
   cfg=p.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py'
   assert hashlib.sha256(cfg.read_bytes()).hexdigest()==provenance['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py']
   node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets))
   is_box='push_box' in p.name;scale=ast.literal_eval(node.value.orelse if is_box else node.value.body)
   expected=np.array([.14,.09,.045] if is_box else [.15,.145,.04])*np.array(scale)
   assert np.max(abs(expected-np.asarray(edge['actual_core_size_xyz'])))<1e-7
  with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
  with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
  packets={x['after_action_step']:x for x in json.loads((p/'solved_contact_forces.json').read_text())['rows']};from front_recontact_headroom_v2_stage_source_binding import verify_observation_binding
  verify_observation_binding(p)
  assert not (p.parent/'SOURCE_CONTRACT_FIXTURE.json').exists()
  from audit_front_corridor_midpoint_cop import reconstruct as reconstruct_midpoint
  midpoint=reconstruct_midpoint(log['rows'],log['plan'],tr,ori,packets,'box' if 'push_box' in p.name else 'mailer',midpoint_enabled=True,expected_steps=range(1,len(tr['box'])))
  records,errors=midpoint['records'],midpoint['errors']
 else:
  errors=[[r['step'],'unexpected_COP_trace'] for r in log['rows'] if r.get('cop_slip_following') is not None]
 sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();report=dict(passed=not errors,enabled=enabled,errors=errors,records=records,loaded_steps_checked=len(records),source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']},auditor_sha256=sha(__file__),scope='Independent previous-force COP, object pose, front clearance state/goal, phase reset and local anchor, source-bound nominal drive and optional independent raw-COP/core-edge1..nominal governor/correction, independent epigraph LP for diagonal path selection, near-corner goal, actual direction core-edge ray, coupled XY command or unchanged parent axis fallback. Existing control/reference/quality audits required separately. No dynamics or success inference.',training_ready=False);(p/'FRONT_RECONTACT_HEADROOM_V1_DIAGONAL_LIVE_AUDIT.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in {'records','source_sha256'}});sys.exit(0 if report['passed'] else 1)
