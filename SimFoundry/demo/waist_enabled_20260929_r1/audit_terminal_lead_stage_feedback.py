"""Independent complete-record direct feedback reconstruction, no candidate imports.
Historical measurement entry is explicitly separate from new-source admission.
Original raw task/pose, force, all guards and actual visual reviews remain required.
"""
from pathlib import Path
import json,hashlib,sys,math
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_measurements(ep,*,enabled):
 assert type(enabled) is bool;ep=Path(ep)
 with np.load(ep/'raw.npz') as z:task=str(z['task_id']);frames=len(z['q'])
 assert frames==(70 if task=='wait_no_package' else 1200)
 if task=='wait_no_package':
  assert not (ep/'frontal_bypass.json').exists() or not json.loads((ep/'frontal_bypass.json').read_text())['rows']
  return dict(passed=True,wait=True,checked_feedback_rows=0,changed_rows=0,errors=[])
 d=json.loads((ep/'frontal_bypass.json').read_text());plan=d['plan'];rows=d['rows'];assert [r['step'] for r in rows]==list(range(1,frames));controls=json.loads((ep/'expert_control.json').read_text());assert [r['step'] for r in controls]==list(range(frames));key='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1;assert plan['direction']==direction
 sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
 with np.load(ep/'trace.npz') as z:target=z[key].astype(float);obstacle=z[other].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix();orot=Rotation.from_quat(z[other]).as_matrix()
 stage='lateral_y';hold=None;checks=[];errors=[];count=0
 def near(a,b,t,label):
  aa,bb=np.asarray(a,float),np.asarray(b,float)
  if aa.shape!=bb.shape or not np.isfinite(aa).all() or not np.isfinite(bb).all() or np.max(abs(aa-bb))>2e-6:errors.append(dict(step=t,kind=label))
 for row in rows:
  t=row['step'];f=row.get('clearance_feedback');annotation=(f or {}).get('terminal_directional_lead_floor')
  if not f or not f.get('eligible'):
   if annotation is not None:errors.append(dict(step=t,kind='floor_outside_eligible_feedback'))
   continue
  assert plan.get('initial_top_selected') and row['mode']=='top_push'
  near(row['observed_target'],target[t],t,'target_trace_binding');near(plan['initial_target_xyz'],target[0],t,'initial_trace_binding')
  tr=abs(rot[t])@(sizes[key]/2);orr=abs(orot[t])@(sizes[other]/2);gap=abs(target[t,:2]-obstacle[t,:2])-tr[:2]-orr[:2];away=-1 if target[0,0]<obstacle[0,0] else 1;goal_y=direction*max(.205,direction*target[0,1]+.16);low,high=sorted([target[t,1],goal_y]);remaining=max(low-obstacle[t,1],obstacle[t,1]-high,0.)-tr[1]-orr[1];need=remaining<.024;boundary=obstacle[t,0]+away*(tr[0]+orr[0]+.024);separated=min(target[0,0],boundary) if away<0 else max(target[0,0],boundary);goal_x=separated if need else target[0,0];margin=min(goal_x-tr[0]-.28,.88-goal_x-tr[0])
  if max(gap)<.01-1e-7 or margin<.005-1e-7:errors.append(dict(step=t,kind='original_geometry_guard'))
  xgap=away*(target[t,0]-obstacle[t,0])-tr[0]-orr[0]
  if gap[1]<.022 and xgap<.018 and stage!='clearance_x':stage='clearance_x';hold=target[t,1]
  elif stage=='clearance_x' and (xgap>=.021 or gap[1]>=.022):stage='lateral_y';hold=None
  ygoal=hold if stage=='clearance_x' else goal_y
  if f['stage']!=stage or f['needs_x_corridor'] is not bool(need):errors.append(dict(step=t,kind='phase_or_y_path'))
  near(f['axis_gaps_m'],gap,t,'axis_gaps');near(f['object_goal_xy'],[goal_x,ygoal],t,'object_goal');near(f['remaining_y_gap_m'],remaining,t,'remaining_y_gap');near(f['planned_table_margin_m'],margin,t,'table_margin')
  tip=np.asarray(row['observed_support_xyz'][:2]);prev=np.asarray(controls[t-1]['target_xyz'][:2]) if controls[t-1]['mode']=='top_push' else tip;step=min(.003,plan['top_recontact']['drag_step_m']);desired=tip+np.clip(np.array([goal_x,ygoal])-target[t,:2],-.012,.012);old_command=prev+np.clip(desired-prev,-step,step);distance=direction*(ygoal-target[t,1]);eligible=bool(enabled and stage=='lateral_y' and 0<distance<step)
  if eligible:
   expected=dict(enabled=True,original_step_m=step,signed_remaining_y_m=float(distance),original_desired_y=float(desired[1]),original_command_y=float(old_command[1]),goal_unchanged=True,quality_unchanged=True,physical_benefit_proven=False)
   if not isinstance(annotation,dict) or set(annotation)!=set(expected):errors.append(dict(step=t,kind='missing_or_changed_floor_metadata'))
   else:
    for k,v in expected.items():
     if isinstance(v,bool):
      if annotation[k] is not v:errors.append(dict(step=t,kind='floor_metadata_'+k))
     else:near(annotation[k],v,t,'floor_metadata_'+k)
   desired[1]=tip[1]+direction*step;count+=1
  elif annotation is not None:errors.append(dict(step=t,kind='unexpected_floor'))
  command=prev+np.clip(desired-prev,-step,step);near(f['desired_support_xy'],desired,t,'desired_support');near(f['command_xy'],command,t,'emitted_command');near(row['target_xyz'][:2],command,t,'waypoint_mapping');near(controls[t]['target_xyz'],row['target_xyz'],t,'actual_expert_mapping');checks.append(dict(step=t,phase=stage,new_floor_expected=eligible,previous_xy=prev.tolist(),expected_xy=command.tolist()))
 if plan.get('initial_top_selected') and any(r['mode']=='top_push' for r in rows):assert checks
 return dict(passed=not errors,wait=False,checked_feedback_rows=len(checks),changed_rows=count,errors=errors,rows=checks)
def audit(ep):
 from terminal_lead_stage_source_binding import verify_observation_binding
 ep=Path(ep).resolve();binding=verify_observation_binding(ep);result=verify_measurements(ep,enabled=True);files=[ep/'raw.npz',Path(__file__)]
 if not result['wait']:files.extend(ep/n for n in ['frontal_bypass.json','expert_control.json','trace.npz','parcel_orientation.npz'])
 result.update(source_binding=binding,source_sha256={str(p):sha(p) for p in files},scope=__doc__,training_ready=False);return result
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=audit(ep);(ep/'TERMINAL_LEAD_STAGE_FEEDBACK_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('rows','source_binding','source_sha256','scope')}));sys.exit(0 if out['passed'] else 1)
