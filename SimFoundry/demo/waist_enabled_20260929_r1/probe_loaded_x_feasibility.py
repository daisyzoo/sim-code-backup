"""Local LP allocation with no worsening other recorded linear task residuals."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from scipy.optimize import linprog
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();parent=w/'loaded_coupled_allocation_probe_r1/RESULT.json';prior=json.loads(parent.read_text());assert prior['passed'] and prior['max_actual_command_replay_error_rad']==0;reports=[]
for case in prior['episodes']:
 ep=w/case['run']/('case_'+case['episode'].split('_')[1])/case['episode'];src=json.loads((ep.parent/'provenance.json').read_text())['source_sha256'];rel=next(x for x in src if x.endswith('/articulated_hand_geometry.py'));path=ep.parent/'source_snapshot'/rel;assert sha(path)==case['archived_geometry_sha256'];spec=importlib.util.spec_from_file_location('lp_geometry',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 for name,h in case['asset_sha256'].items():assert sha(repo/name)==h
 for name,h in case['source_sha256'].items():assert sha(ep/name)==h
 model=m.ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right';ix=3 if side=='right' else 0
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};rows=[]
 lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015
 for sample in case['rows']:
  if not sample['loaded']:continue
  t=sample['step'];c=coords[t];f=fr[t];normal=c['contact_normal_tracking'];pos=np.array(c['control_jacobian_world']);jac=np.vstack([pos,np.array(normal['jacobian'],dtype=np.float32)]);err=[]
  for hand in ['left','right']:
   goal=f['target_xyz'] if hand==side else c['inactive_anchor'];err.extend(np.clip(np.float32(.72)*(np.array(goal,dtype=np.float32)-np.array(c['control_point_positions'][hand],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
  err=np.r_[err,np.array(normal['error'],dtype=np.float32)];base=np.array(sample['probes'][0]['command'])-q[t];res=jac@base-err;keep=[k for k in range(len(err)) if k!=ix];tol=np.abs(res[keep])+1e-7
  A=np.vstack([np.c_[jac[keep],np.zeros(len(keep))],np.c_[-jac[keep],np.zeros(len(keep))],np.r_[jac[ix],-1.][None],np.r_[-jac[ix],-1.][None]]);b=np.r_[err[keep]+tol,-err[keep]+tol,err[ix],-err[ix]]
  lower=np.maximum.reduce([lo-q[t],-limits,u[t-1]-.055-q[t]]);upper=np.minimum.reduce([hi-q[t],limits,u[t-1]+.055-q[t]]);objective=np.r_[np.zeros(11),1.];fit=linprog(objective,A_ub=A,b_ub=b,bounds=[*zip(lower,upper),(0,None)],method='highs')
  result=dict(step=t,success=bool(fit.success),message=fit.message,baseline_linear_x_residual_mm=float(abs(res[ix])*1000))
  if fit.success:
   delta=fit.x[:11];command=q[t]+delta;assert np.max(A@fit.x-b)<1e-6 and np.all(delta>=lower-1e-7) and np.all(delta<=upper+1e-7)
   values=[]
   for kind,cmd in [('baseline',q[t]+base),('candidate',command)]:
    T,_,_=model.fk(side,cmd);Ti,_,_=model.fk(inactive,cmd);point=T[:3,3]+T[:3,:3]@np.array(f['control_offset_local']);ip=Ti[:3,3]+Ti[:3,:3]@np.array([.2,0,.007]);normal_angle=np.arccos(np.clip((T[:3,:3].T@np.array([0.,0.,1.]))@normal['target_local_up'],-1,1));values.append(dict(kind=kind,goal_minus_nominal_fk_xyz_mm=((np.array(f['target_xyz'])-point)*1000).tolist(),inactive_anchor_error_mm=float(np.linalg.norm(ip-c['inactive_anchor'])*1000),nominal_normal_angle_error_rad=float(normal_angle)))
   result.update(candidate_linear_x_residual_mm=float(abs(jac[ix]@delta-err[ix])*1000),candidate_waist_command_rad=float(command[0]),candidate_command=command.tolist(),other_linear_residuals_no_worse=True,original_step_and_command_and_slew_bounds_passed=True,nonlinear_fk=values)
  rows.append(result)
 reports.append(dict(run=case['run'],episode=case['episode'],rows=rows))
out=dict(episodes=reports,source_replay_sha256=sha(parent),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Local first-order feasibility/absolute-X minimization under original joint/step/slew bounds. Every other recorded linear task residual component, including activeY/Z,inactiveXYZ,normal, may worsen only numerical1e-7m tolerance. Damping objective is omitted to ask existence, not propose a runtime controller. True FK reported separately; no contact/dynamics forecast or global infeasibility/success claim.')
p=w/'loaded_coupled_allocation_probe_r1/X_FEASIBILITY.json';assert not p.exists();p.write_text(json.dumps(out,indent=2))
for c in reports:print(c['run'],c['episode'],[(r['step'],r['success'],round(r['baseline_linear_x_residual_mm'],3),round(r.get('candidate_linear_x_residual_mm',-1),3)) for r in c['rows']])
