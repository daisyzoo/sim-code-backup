"""Offline nonlinear frozen-offset virtual-reference direction screen under original command bounds.
No controller change, state rollout, COP dynamics or collision certificate.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from scipy.optimize import linprog,minimize,Bounds,LinearConstraint
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_rear_coupled_execution_live import inspect
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=inspect(ep);assert base['passed'] and base['complete_push_coverage'] and base['selected']
audit=json.loads((ep/'REAR_JOINT_XY_LIVE_AUDIT.json').read_text());assert audit['passed'] and audit['enabled']
for n,h in audit['source_sha256'].items():assert sha(ep/n)==h
prov=json.loads((ep.parent/'provenance.json').read_text());snap=ep.parent/'source_snapshot'
gname=next(n for n in prov['source_sha256'] if n.endswith('/articulated_hand_geometry.py'));gp=snap/gname;assert sha(gp)==prov['source_sha256'][gname]
sp=importlib.util.spec_from_file_location('edge_screen_fk',gp);gm=importlib.util.module_from_spec(sp);sp.loader.exec_module(gm)
assets=['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py']
for a in assets:assert sha(repo/a)==prov['source_sha256'][a]
model=gm.ArticulatedHandGeometry(repo/assets[0],repo/assets[1])
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(np.float32);u=z['action'][:,12:23].astype(np.float32)
key='box' if 'push_box' in ep.name else 'mailer';side='right' if key=='box' else 'left';direction=-1 if side=='right' else 1;ai=list(range(3,6)) if side=='right' else list(range(3));ii=list(range(3)) if side=='right' else list(range(3,6))
with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fr=json.loads((ep/'frontal_bypass.json').read_text());core=np.asarray(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;damping=np.full(11,.045);damping[0]=.12;rows=[]
for f in fr['rows']:
 if f['mode']!='top_push' or not f.get('rear_joint_xy_progress',{}).get('override'):continue
 t=f['step'];c=cs[t];J=np.vstack([np.asarray(c['control_jacobian_world'],dtype=np.float32),np.asarray(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]).astype(float);err=[]
 for hand in ['left','right']:
  target=f['target_xyz'] if hand==side else c['inactive_anchor'];point=np.asarray(c['control_point_positions'][hand],dtype=np.float32);err.extend(np.clip(np.float32(.72)*(np.asarray(target,dtype=np.float32)-point),np.float32(-.035),np.float32(.035)).tolist())
 error=np.r_[err,c['contact_normal_tracking']['error']];lower=np.maximum.reduce([lo-q[t],-limits,u[t-1].astype(float)-.055-q[t]]);upper=np.minimum.reduce([hi-q[t],limits,u[t-1].astype(float)+.055-q[t]])
 local=rot[t].T@(np.asarray(f['rear_cop_centering']['cop_world'])-xyz[t]);axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01000001];assert axes
 normals=np.asarray([-np.sign(local[k])*rot[t,:,k] for k in axes]);A=normals@J[ai];forward=direction*J[ai][1];A=np.vstack([A,forward])
 row=dict(step=t,threatened_axes=axes,loaded=f['contact_load']['observed_vertical_load_n']>=.2)
 if (lower>upper).any():row['status']='empty_original_bound_intersection';rows.append(row);continue
 lp=linprog(-forward,A_ub=-A,b_ub=np.zeros(len(A)),bounds=list(zip(lower,upper)),method='highs')
 if not lp.success:
  assert lp.status==2,lp.message
  row['status']='direction_constraints_infeasible';rows.append(row);continue
 # Keep the same position/normal/damping objective; only add direction and final slew constraints.
 design=np.vstack([J,np.diag(damping)]);rhs=np.r_[error,np.zeros(11)];H=design.T@design;g=design.T@rhs
 fun=lambda x:5000*float(x@H@x-2*g@x)
 jac=lambda x:10000*(H@x-g)
 sol=minimize(fun,lp.x,jac=jac,bounds=Bounds(lower,upper),constraints=[LinearConstraint(A,np.zeros(len(A)),np.full(len(A),np.inf))],method='SLSQP',options={'ftol':1e-11,'maxiter':300})
 assert sol.success,(t,sol.message);assert np.min(A@sol.x)>=-1e-8 and np.min(sol.x-lower)>=-1e-8 and np.min(upper-sol.x)>=-1e-8
 current=q[t].astype(float);offset=np.asarray(f['control_offset_local'])
 def point(cmd):
  T,_,_=model.fk(side,cmd);return T[:3,3]+T[:3,:3]@offset
 p0=point(current);assert np.max(abs(p0-np.asarray(f['observed_support_xyz'])))<2e-6
 def nonlinear_direction(dq):
  motion=point(current+dq)-p0
  return np.r_[normals@motion,direction*motion[1]]
 nonlinear_sol=minimize(fun,sol.x,jac=jac,bounds=Bounds(lower,upper),constraints=[{'type':'ineq','fun':nonlinear_direction}],method='SLSQP',options={'ftol':1e-11,'maxiter':300})
 assert nonlinear_sol.success,(t,nonlinear_sol.message)
 assert np.min(nonlinear_direction(nonlinear_sol.x))>=-1e-8
 assert np.min(nonlinear_sol.x-lower)>=-1e-8 and np.min(upper-nonlinear_sol.x)>=-1e-8
 sol=nonlinear_sol
 variants=[]
 for name,cmd in [('actual_baseline',u[t].astype(float)),('nonlinear_joint_direction_screen',(current+sol.x).astype(np.float32).astype(float))]:
  dq=cmd-current;motion=point(cmd)-p0;res=J@dq-error
  variants.append(dict(name=name,linear_min_edge_inward_mm=float(np.min(normals@J[ai]@dq)*1000),nonlinear_min_edge_inward_mm=float(np.min(normals@motion)*1000),nonlinear_forward_mm=float(direction*motion[1]*1000),active_residual_norm_mm=float(np.linalg.norm(res[ai])*1000),inactive_residual_mm=float(np.linalg.norm(res[ii])*1000),normal_residual_norm=float(np.linalg.norm(res[6:])),command=cmd.tolist()))
 row.update(status='feasible',lp_max_linear_forward_mm=float(-lp.fun*1000),variants=variants);rows.append(row)
feasible=[r for r in rows if r['status']=='feasible'];assert feasible
summary=dict(selected_override_frames=len(rows),baseline_full_push_replay_frames=base['checked_push_frames'],feasible_frames=len(feasible),infeasible_frames=len(rows)-len(feasible),median_max_linear_forward_mm=float(np.median([r['lp_max_linear_forward_mm'] for r in feasible])),variants=[])
for i in [0,1]:
 vals=[r['variants'][i] for r in feasible];bas=[r['variants'][0] for r in feasible]
 summary['variants'].append(dict(name=vals[0]['name'],nonlinear_outward_over_0_05mm=sum(v['nonlinear_min_edge_inward_mm']<-.05 for v in vals),median_nonlinear_min_edge_inward_mm=float(np.median([v['nonlinear_min_edge_inward_mm'] for v in vals])),median_nonlinear_forward_mm=float(np.median([v['nonlinear_forward_mm'] for v in vals])),median_active_residual_mm=float(np.median([v['active_residual_norm_mm'] for v in vals])),normal_residual_worse_over_1e_4=sum(v['normal_residual_norm']>b['normal_residual_norm']+1e-4 for v,b in zip(vals,bas)),inactive_residual_worse_over_0_1mm=sum(v['inactive_residual_mm']>b['inactive_residual_mm']+.1 for v,b in zip(vals,bas))))
out=dict(episode=ep.name,summary=summary,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json','trace.npz','parcel_orientation.npz','REAR_JOINT_XY_LIVE_AUDIT.json']},archived_geometry_sha256=sha(gp),assets_sha256={n:sha(repo/n) for n in assets},checker_sha256=sha(Path(__file__)),training_ready=False,scope=__doc__+' Fixed current-offset virtual reference FK (not a mesh material/contact point), near-core-edge<=10mm constraints applied to nonlinear FK hand displacement in frozen current object orientation, plus nonnegative nonlinear forward displacement. Feasible linear direction LP and QP initialize SLSQP, which optimizes the unchanged quadratic position/normal/damping objective with nonlinear direction constraints. Linear LP maximum-forward is only the initialization geometry, not a nonlinear maximum. Object translation/rotation and actual actuator dynamics are NOT predicted. Full original baseline executed actions replayed; no physical evidence for alternative commands.')
(ep/'JOINT_EDGE_NONLINEAR_IK_SCREEN.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(episode=ep.name,summary=summary),indent=2))
