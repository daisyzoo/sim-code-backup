"""One-step replay of recorded IK: distinguish posture tradeoff from tracking dynamics."""
from pathlib import Path
import ast,json,sys
import numpy as np
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.bounded_ik import bounded_damped_step
values={}
for n in ast.parse((root.parents[1]/'simfoundry/robots/g1_assets.py').read_text()).body:
 if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id in ('U1_JOINT_LIMIT_LO','U1_JOINT_LIMIT_HI'):values[n.target.id]=ast.literal_eval(n.value)
lo=np.array(values['U1_JOINT_LIMIT_LO'][12:23]);hi=np.array(values['U1_JOINT_LIMIT_HI'][12:23]);lo[0]=-.98;hi[0]=.98;limits=np.r_[.015,np.full(10,.04)];damping=np.r_[.12,np.full(10,.045)];run=Path(sys.argv[1]).resolve();rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 control=json.loads((ep/'coordination.json').read_text());frontal={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};z=np.load(ep/'raw.npz');records=[]
 for c in control:
  if 'control_jacobian_world' not in c or c['waist_preference_rad'] is None:continue
  t=c['step'];f=frontal[t];J=np.array(c['control_jacobian_world']);q=np.array(c['upper_q']);active=c['active_side'];idx=slice(0,3) if active=='left' else slice(3,6);points=c['control_point_positions'];targets={active:f['target_xyz'],('right' if active=='left' else 'left'):c['inactive_anchor']};error=np.concatenate([np.clip(.72*(np.array(targets[s])-points[s]),-.035,.035) for s in ('left','right')]);prior=np.zeros(11);prior[0]=c['preferred_waist_step_rad'];weighted=bounded_damped_step(J,error,q,lo,hi,limits,damping,prior);zero=bounded_damped_step(J,error,q,lo,hi,limits,damping)
  action=np.clip(q+weighted,z['action'][t-1,12:23]-.055,z['action'][t-1,12:23]+.055)
  records.append(dict(step=t,mode=f['mode'],replay_action_error_rad=float(np.max(abs(action-z['action'][t,12:23]))),cartesian_residual_with_prior_m=float(np.linalg.norm((error-J@weighted)[idx])),cartesian_residual_without_prior_m=float(np.linalg.norm((error-J@zero)[idx])),posture_induced_active_step_difference_m=float(np.linalg.norm((J@(weighted-zero))[idx])),prior_waist_step_rad=float(prior[0]),current_waist_rad=float(q[0]),nominal_xy_error_m=float(np.max(abs(np.array(f['observed_support_xyz'][:2])-f['parcel_top_xyz'][:2]))) if 'parcel_top_xyz' in f else None))
 late=[r for r in records if r['step']>=600 and r['mode']=='top_descend'];row=dict(episode=ep.name,max_replay_action_error_rad=max(r['replay_action_error_rad'] for r in records),late_descend_samples=len(late),max_posture_induced_active_step_difference_m=max((r['posture_induced_active_step_difference_m'] for r in late),default=None),records=records);rows.append(row);print(ep.name,{k:v for k,v in row.items() if k!='records'},'late',late[-4:])
(run/'WAIST_PRIOR_TASK_TRADEOFF.json').write_text(json.dumps(dict(rows=rows,scope='Replay actual bounded position solver at recorded Jacobian samples, with vs without preferred waist step, including final0.055rad continuity clip for parity. One-step linearized comparison, not a closed-loop ablation or proof that removing posture preference helps visibility or task success.',training_ready=False),indent=2))
