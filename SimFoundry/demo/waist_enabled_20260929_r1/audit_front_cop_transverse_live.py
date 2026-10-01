"""Independent force-packet, geometric route and COP-waypoint reconstruction."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation

def reconstruct(rows, plan, tr, ori, packets, key):
 side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};direction=-1 if side=='right' else 1;rot={k:Rotation.from_quat(ori[k]).as_matrix() for k in sizes};g=plan['front_route_live_guards'];clear=g['clearance_before_lateral_m'];first=rows[0]['step'];radii={k:abs(rot[k])@sizes[k]/2 for k in sizes};initial_x=tr[other][first,0]-radii[other][first,0]-radii[key][first,0]-clear-.003;final_y=direction*max(.205,direction*tr[key][first,1]+.16)
 stage='front_x';hold=float(plan['initial_target_xyz'][1]);safe_count=0;anchor=None;last_anchor=None;previous=None;prior_step=None;errors=[];records=[]
 def near(t,name,a,b):
  error=float(np.max(abs(np.asarray(a)-np.asarray(b))))
  if not np.isfinite(error) or error>2e-6:errors.append([t,name,error])
 for row in rows:
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
  if row['mode']!='top_push':
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
  if not weights or sum(weights)<.3:
   if f.get('override') or f.get('reason')!='no_valid_current_loaded_cop':errors.append([t,'override_without_current_load'])
   anchor=last_anchor=None;previous=np.asarray(row['target_xyz'][:2]);continue
  if not f.get('override'):errors.append([t,'missing_declared_loaded_override']);previous=np.asarray(row['target_xyz'][:2]);continue
  cop=np.average(points,axis=0,weights=weights);local=r.T@(cop-obj)
  if anchor is None:anchor=local.copy()
  world=obj+r@anchor;feed=np.zeros(2) if last_anchor is None else world[:2]-last_anchor[:2];goal=np.array([goal_x,hold if stage=='front_x' else final_y]);error=goal-obj[:2];distance=np.linalg.norm(error);drive=error*min(.001,distance)/distance if distance else np.zeros(2);raw_correction=.05*(world[:2]-cop[:2]);axis=error/distance if distance else np.zeros(2);removed=(np.dot(raw_correction,error)/np.dot(error,error))*error if distance else np.zeros(2);correction=raw_correction-removed;base=np.asarray(row['observed_support_xyz'][:2]) if previous is None else previous;ref=np.asarray(row['observed_support_xyz'][:2]);desired=base+feed+drive+correction;bounded=np.clip(desired,ref-.030,ref+.030);command=base+np.clip(bounded-base,-.003,.003)
  compare={'command_xy':command,'previous_command_xy':base,'reference_xy':ref,'anchor_local':anchor,'measured_cop_local':local,'object_anchor_translation_xy':feed,'drive_xy':drive,'slip_correction_xy':correction,'raw_slip_correction_xy':raw_correction,'drive_direction_xy':axis,'removed_parallel_correction_xy':removed,'command_delta_xy':command-base,'command_reference_lead_xy':command-ref}
  for name,value in compare.items():
   if name not in f:errors.append([t,'missing_'+name])
   else:near(t,name,f[name],value)
  near(t,'actual_waypoint',row['target_xyz'][:2],command)
  for name,value in [('desired_lead_clipped',bool(np.any(abs(bounded-desired)>1e-12))),('retained_slew_lag_outside_lead',bool(np.any(abs(command-ref)>.030+1e-9)))]:
   # Near threshold float32 geometry can change a boolean; retain distance evidence.
   boundary=np.min(abs(abs(desired-ref)-.030)) if name=='desired_lead_clipped' else np.min(abs(abs(command-ref)-.030))
   if boundary>2e-6 and f.get(name)!=value:errors.append([t,name])
  records.append(dict(step=t,normal_load_n=sum(weights),independent_cop_local_m=local.tolist(),goal_xy=goal.tolist(),command_xy=command.tolist(),waypoint_error_m=float(np.max(abs(command-row['target_xyz'][:2])))))
  previous=np.asarray(row['target_xyz'][:2]);last_anchor=world
 return records,errors

if __name__=='__main__':
 p=Path(sys.argv[1]).resolve();log=json.loads((p/'frontal_bypass.json').read_text());args=json.loads((p.parent/'provenance.json').read_text())['args'];enabled=args.get('front_cop_slip_following',False) and log['plan'].get('front_route_selected',False);records=[];errors=[]
 if enabled:
  c=log['plan']['front_cop_slip_following'];assert c['enabled'] and c['feedback_projection']=='orthogonal_to_current_goal_direction' and c['drive_step_m']==.001 and c['feedback_gain']==.05 and c['max_step_m']==.003 and c['max_reference_lead_m']==.030
  with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
  with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
  packets={x['after_action_step']:x for x in json.loads((p/'solved_contact_forces.json').read_text())['rows']};records,errors=reconstruct(log['rows'],log['plan'],tr,ori,packets,'box' if 'push_box' in p.name else 'mailer')
 else:
  errors=[[r['step'],'unexpected_COP_trace'] for r in log['rows'] if r.get('cop_slip_following') is not None]
 sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();report=dict(passed=not errors,enabled=enabled,errors=errors,records=records,loaded_steps_checked=len(records),source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']},auditor_sha256=sha(__file__),scope='Independent previous-force COP, object pose, front clearance state/goal, local anchor, drive/correction and actual XY command reconstruction. Existing control/reference/quality audits required separately. No dynamics or success inference.',training_ready=False);(p/'FRONT_COP_LIVE_AUDIT.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in {'records','source_sha256'}});sys.exit(0 if report['passed'] else 1)
