"""Independent desired-lead/slew/lifecycle reconstruction, no control imports."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=Path(sys.argv[1]).resolve();config=json.loads((p.parent/'provenance.json').read_text())['args'];d=json.loads((p/'frontal_bypass.json').read_text());rows=d['rows'];lead=config.get('expert_top_object_relative_lead_m',0.);step=config['expert_frontal_top_drag_step_m'];errors=[];checks=[];previous=None;center_by={};side='right' if 'push_box' in p.name else 'left';key='box' if side=='right' else 'mailer'
if lead:
 assert .012<=lead<=.030 and config['expert_top_contact_center_calibration'] and not config['expert_front_object_relative_lead']
 if any(r['mode'].startswith('top_') for r in rows):assert d['plan']['bounded_top_object_lead']['desired_axis_lead_m']==lead
 if (p/'contact_center_calibration.json').exists():
  from audit_contact_center_live import audit
  verified=audit(p);center_by={r['step']:np.array(r['center_local']) for r in verified['centers']};commit=verified['commit_step']
 else:commit=None
 env={'__file__':str(ROOT/'audit_terminal_reach.py')};source=(ROOT/'audit_terminal_reach.py').read_text();exec(compile(source.split("p=root/'contact_x_ablation")[0],'<URDF audit setup>','exec'),env)
 vertices=np.array(json.loads((ROOT.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side])
 with np.load(p/'raw.npz') as z:qs=z['q'].copy()
 with np.load(p/'trace.npz') as z:position=z[key].copy()
 with np.load(p/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
 def point(t):
  m=np.eye(4);m[:3,3]=[.08,0,.793]
  for name,origin,axis in env['chains'][side]:
   m=m@origin
   if axis is not None:
    a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*(qs[t,12+env['names'].index(name)] if name in env['names'] else 0.)).as_matrix();m=m@a
  n=rot[t,:,2];w=vertices@m[:3,:3].T+m[:3,3];center=m[:3,:3]@center_by[t]+m[:3,3]
  return center+n*((w@n).min()-center@n)
for row in rows:
 t=row['step'];logged=row.get('bounded_top_object_lead')
 if not lead or row['mode']!='top_push':
  assert logged is None,(t,'Unexpected override');previous=None;continue
 assert commit is not None and t>commit and t in center_by,(t,'Uncalibrated push')
 assert logged is not None,(t,'Missing lead binding')
 reference=point(t);before=reference[:2] if previous is None else previous
 if 'route_stage' in row:
  progress=row.get('clearance_progress');goal_y=(progress['front_hold_y'] if progress is not None else d['plan']['initial_target_xyz'][1]) if row['route_stage']=='front_x' else d['plan']['front_route_candidates']['goal_y'];goal=np.array([row['route_goal_x'],goal_y])
 else:
  anchor=row.get('push_x_anchor_m');x=anchor if anchor is not None else row['parcel_top_xyz'][0]+row['approach_xy_bias_m'][0]
  # Parent state updates its original x command by2mm before this override.
  goal=np.array([before[0]+np.clip(x-before[0],-.002,.002),d['plan']['direction']*.34])
 desired=position[t,:2]+np.clip(goal-position[t,:2],-lead,lead);command=before+np.clip(desired-before,-step,step)
 compare={'goal_xy':goal,'desired_xy':desired,'previous_xy':before,'command_xy':command,'command_relative_object_xy_m':command-position[t,:2]}
 error=max(float(np.max(abs(np.asarray(logged[k])-v))) for k,v in compare.items());error=max(error,float(np.max(abs(np.asarray(row['target_xyz'][:2])-command))))
 assert logged['lead_m']==lead and logged['step_m']==step
 boundary=bool(np.min(abs(abs(desired-before)-step))<=2e-6)
 if not boundary:assert logged['slew_limited']==bool(np.any(abs(desired-before)>step))
 assert error<2e-6,(t,error)
 checks.append(dict(step=t,slew_classification_near_numeric_boundary=boundary,reconstruction_error_m=error,desired_axis_lead_m=float(np.max(abs(desired-position[t,:2]))),command_axis_lead_m=float(np.max(abs(command-position[t,:2]))),actual_reference_axis_offset_m=float(np.max(abs(reference[:2]-position[t,:2])))))
 previous=command
files=['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']
if (p/'contact_center_calibration.json').exists():files+=['contact_center_calibration.json','solved_contact_forces.json']
out=dict(passed=True,enabled=bool(lead),checked_override_frames=len(checks),max_reconstruction_error_m=max((r['reconstruction_error_m'] for r in checks),default=0.),max_actual_reference_axis_offset_m=max((r['actual_reference_axis_offset_m'] for r in checks),default=None),records=checks,source_sha256={str(p/f):sha(p/f) for f in files},auditor_sha256=sha(__file__),scope='Independent source-bound calibration, URDF reference and declared route goals, parent x slew, desired relative lead, command slew/reset and logging. Realized reference offset reported separately from desired bound. No full state/dynamics replay, force success, collision certification or training admission.',training_ready=False)
(p/'BOUNDED_TOP_LEAD_LIVE_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('records','source_sha256')},indent=2))
