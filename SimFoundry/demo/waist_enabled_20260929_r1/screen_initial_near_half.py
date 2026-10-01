"""Near-box/bag approach from actual first cross states, candidate fractions only."""
from pathlib import Path
import sys,ast,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;repo=root.parents[1];sys.path.insert(0,str(repo))
s=(root/'audit_terminal_reach.py').read_text();exec(compile(s.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
tree=ast.parse((root/'audit_front_short_recovery_kinematics.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fk'],type_ignores=[]),'<fk>','exec'))
from simfoundry.data.projected_support_reference import projected_support_reference,projected_support_jacobian,skew
from simfoundry.data.initial_top_route import InitialTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.bounded_ik import bounded_damped_step
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
for node in ast.parse((repo/'simfoundry/robots/g1_assets.py').read_text()).body:
 if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in ['U1_JOINT_LIMIT_LO','U1_JOINT_LIMIT_HI']:globals()[node.target.id]=np.array(ast.literal_eval(node.value))[12:]
lo=U1_JOINT_LIMIT_LO.copy();hi=U1_JOINT_LIMIT_HI.copy();lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;damping=np.full(11,.045);damping[0]=.12
run=root/'initial_near_contact_depth_r1';results=[]
for identifier,task in [(890002,'push_box_to_bin'),(890003,'nudge_mailer_to_bin')]:
 ep=run/f'case_{identifier}'/f'layout_{identifier}_{task}';side='right' if 'push_box' in task else 'left';other_side='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=(.14,.09,.045) if key=='box' else (.15,.145,.04);other_size=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 log=json.loads((ep/'frontal_bypass.json').read_text());first=next(x for x in log['rows'] if x['mode']=='top_cross');t=first['step'];coord=next(x for x in json.loads((ep/'coordination.json').read_text()) if x['step']==t);assert coord['contact_normal_tracking'] is None
 with np.load(ep/'raw.npz') as z:q0=z['q'][t,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 target=tr[key][t].astype(float);obstacle=tr[other][t].astype(float);quat=ori[key][t];other_quat=ori[other][t];normal=Rotation.from_quat(quat).as_matrix()[:,2];anchor=np.asarray(coord['inactive_anchor']);vertices=np.array(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);m,_,_=fk(side,q0);fk_error=float(np.linalg.norm(m[:3,3]+m[:3,:3]@np.array([.20,0,.007])-tr['palm_'+side][t]));assert fk_error<.0001
 for fraction in [.7,.5]:
  q=q0.copy();state=InitialTopRouteState(FrontalBypassState(log['plan']),side,size,obstacle_size=other_size,guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.010,front_inset_fraction=fraction,tilt_recontact_rad=.03,confirm_terminal_release=True);state.proposal=log['plan']['initial_top_proposal'];state.top_mode='top_cross';state.start=tuple(first['observed_support_xyz']);history=[]
  for k in range(400):
   m,jl,jw=fk(side,q);r=m[:3,:3];ref=projected_support_reference(vertices,r,normal);offset=ref['reference_local'];point=m[:3,3]+r@offset;ja=projected_support_jacobian(jl,jw,r,ref);mi,jli,jwi=fk(other_side,q);po=np.array([.20,0,.007]);pi=mi[:3,3]+mi[:3,:3]@po;ji=jli-skew(mi[:3,:3]@po)@jwi
   gap=hand_face_separation(side).gap(m[:3,3],Rotation.from_matrix(r).as_quat(),obstacle,other_quat,other_size)
   row=state.update(point,target,obstacle,.075,.075,tip=point,quat=quat,obstacle_quat=other_quat,control_offset_local=offset,load_n=0.,hand_obstacle_gap_m=gap)
   low=m[:3,3]+r@ref['lowest_vertex_local'];history.append(dict(step=k,mode=row['mode'],hand_other_gap_m=gap,hand_min_z_m=float((vertices@r.T+m[:3,3])[:,2].min()),physical_low_vertex_minus_target_xy_m=(low-target)[:2].tolist(),reference_minus_target_xy_m=(point-target)[:2].tolist(),q=q.tolist()))
   if row['mode'] in ['top_press','initial_top_guard_lift']:break
   jac=np.vstack([ja,ji]);error=np.r_[np.clip(.72*(np.asarray(row['target_xyz'])-point),-.035,.035),np.clip(.72*(anchor-pi),-.035,.035)];q+=bounded_damped_step(jac,error,q,lo,hi,limits,damping)
  result=dict(episode=ep.name,actual_start_frame=t,fraction=fraction,reached_press=history[-1]['mode']=='top_press',kinematic_steps=len(history),min_hand_other_gap_m=min(x['hand_other_gap_m'] for x in history),min_hand_z_m=min(x['hand_min_z_m'] for x in history),last=history[-1],recorded_fk_error_m=fk_error,history=history,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest());results.append(result);print(json.dumps({k:v for k,v in result.items() if k not in ['history','raw_sha256']}),flush=True)
(root/'staged_initial_near_half/APPROACH_SCREEN.json').write_text(json.dumps(dict(rows=results,scope='Actual unloaded first-cross q/geometry/anchor, runtime arm/waist bounds and projected-support Jacobian; normal not yet anchored, matching real prepress phase. Instantaneous tracking/fixed parcels, sampled hand-other geometry only. No real contact patch/forces, full-arm swept clearance, camera or task success proof. Do not execute solved q.',training_ready=False),indent=2))
