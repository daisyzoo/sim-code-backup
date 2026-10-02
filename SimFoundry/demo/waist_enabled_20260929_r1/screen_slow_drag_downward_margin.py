"""Offline causal loaded-command screen, no runtime changes or physical admission.
Same recorded task/normal objective, bounds and slew; add at most0.25mm downward nominal
reference motion when the loaded reference goal is lower. Preserve forward and
near-edge inward nominal directions. Nonlinear FK constraints, independent
elbow/other-parcel/table geometry checks. This is not future COP/force prediction.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.optimize import minimize,Bounds,linprog
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_rear_slow_drag';sys.path[:0]=[str(stage),str(w),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry,skew
from audit_unloaded_wrist_task_optimality import IndependentElbows
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
r=w/'rear_slow_drag_groups_r1';ep=r/'case_840001/layout_840001_push_box_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
g=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');elbow=IndependentElbows(stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};num=json.loads((ep/'SLOW_DRAG_NUMERIC_REVIEW.json').read_text())
with np.load(ep/'trace.npz') as z:xyz={k:z[k].astype(float) for k in ['box','mailer']}
with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].astype(float) for k in ['box','mailer']}
loaded=[t for t,f in fs.items() if f['mode']=='top_push' and f['contact_load']['observed_vertical_load_n']>=.3 and f['target_xyz'][2]<f['observed_support_xyz'][2]]
selected=set(loaded[::20]);loss_near=set()
for b in num['bouts']:
 if b['exit_reason']=='lost_contact':loss_near.update(t for t in range(b['end']-11,b['end']+1) if t in loaded)
selected|=loss_near;records=[];core=np.array(fr['plan']['rear_cop_centering']['actual_core_size_xyz'])
for t in sorted(selected):
 f,c=fs[t],cs[t];inp=c['task_inputs'];q=np.array(inp['current']);previous=np.array(inp['previous']);J=np.array(inp['jacobian']);error=np.array(inp['error']);damp=np.array(inp['damping']);prior=np.array(inp['preferred_step']);parent=np.array(c['joint_edge_refinement']['final_upper_command']);offset=np.array(f['control_offset_local']);R=Rotation.from_quat(quat['box'][t]).as_matrix()
 low=np.maximum.reduce([np.array(inp['lower'])-q,-np.array(inp['step_limits']),previous-.055-q]);high=np.minimum.reduce([np.array(inp['upper'])-q,np.array(inp['step_limits']),previous+.055-q]);assert np.all(low<high)
 def pj(x):
  T,jl,jw=g.fk('right',x);off=T[:3,:3]@offset;return T[:3,3]+off,jl-skew(off)@jw
 origin,j0=pj(q);assert np.max(abs(origin-f['observed_support_xyz']))<1e-6
 points=[];weights=[]
 for contact in packets[t-1]['parcel_contacts']:
  slots=[i for i,s in enumerate(contact['shapes']) if '/parcel_box/' in s]
  if len(slots)!=1 or not any('right_wrist' in s for s in contact['shapes']):continue
  force=np.array(contact['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@R[:,2])
  if load>.05:points.append(contact['position_world']);weights.append(load)
 if sum(weights)<.3:continue
 cop=np.average(points,axis=0,weights=weights);local=R.T@(cop-xyz['box'][t]);axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01]
 normals=np.array([np.array([0.,0.,-1.]),np.array([0.,-1.,0.])]+[-np.sign(local[k])*R[:,k] for k in axes])
 margin=np.zeros(len(normals));margin[0]=min(.00025,origin[2]-f['target_xyz'][2])
 def constraint(delta):return normals@(pj(q+delta)[0]-origin)-margin
 def jac(delta):return normals@pj(q+delta)[1]
 def cost(delta):
  residual=J@delta-error;reg=delta-prior;return float(residual@residual+np.sum((damp*reg)**2))*5000,10000*(J.T@residual+damp*damp*reg)
 fit=linprog(np.zeros(11),A_ub=-normals@j0,b_ub=-margin,bounds=list(zip(low,high)),method='highs');record=dict(step=t,near_loss=t in loss_near,load_n=f['contact_load']['observed_vertical_load_n'],target_error_xyz_mm=((np.array(f['target_xyz'])-origin)*1000).tolist(),original_exact_nominal_delta_mm=((pj(parent)[0]-origin)*1000).tolist(),original_direction_m=constraint(parent-q).tolist(),linear_feasible=bool(fit.success),linear_status=int(fit.status),candidate_accepted=False)
 if fit.success:
  candidates=[]
  for label,initial in [('linear_feasible',fit.x),('bounded_parent',np.clip(parent-q,low,high))]:
   sol=minimize(cost,initial,jac=True,method='SLSQP',bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=constraint,jac=jac)],options=dict(maxiter=300,ftol=1e-11));cmd=(q+sol.x).astype(np.float32).astype(float);v=constraint(cmd-q);gaps=elbow.gap(cmd);Tm,_,_=g.fk('right',cmd);othergap=float(hand_face_separation('right').gap(Tm[:3,3],Rotation.from_matrix(Tm[:3,:3]).as_quat(),xyz['mailer'][t],quat['mailer'][t],[.15,.145,.04]));minz=float((g.vertices['right']@Tm[:3,:3].T+Tm[:3,3])[:,2].min())
   accepted=bool(sol.success and v.min()>=-1e-7 and min(gaps)>=.005-2e-7 and othergap>=.01-2e-7 and minz>=.75-2e-7 and np.all(cmd-q>=low-2e-7) and np.all(cmd-q<=high+2e-7))
   candidate=dict(seed=label,accepted=accepted,status=int(sol.status),iterations=int(sol.nit),direction_m=v.tolist(),elbow_gaps_m=gaps.tolist(),other_gap_m=othergap,hand_lowest_z_m=minz,command=cmd.tolist(),exact_nominal_delta_mm=((pj(cmd)[0]-origin)*1000).tolist(),objective=cost(cmd-q)[0],linear_task_residual_mm=((J@(cmd-q)-error)*1000).tolist());candidates.append(candidate)
  record['attempts']=candidates;accepted=[a for a in candidates if a['accepted']]
  if accepted:record.update(candidate_accepted=True,chosen=min(accepted,key=lambda a:a['objective']))
 records.append(record);print(t,'accepted',record['candidate_accepted'],'old dz',round(record['original_exact_nominal_delta_mm'][2],3),'new',record.get('chosen',{}).get('exact_nominal_delta_mm'),flush=True)
sources=[Path(__file__),stage/'articulated_hand_geometry.py',w/'audit_unloaded_wrist_task_optimality.py',stage/'elbow_torso_hulls.json',repo/'simfoundry/data/hand_obstacle_clearance.py',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json',*[ep/n for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json','SLOW_DRAG_NUMERIC_REVIEW.json']]]
report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),selected_recorded_rows=len(records),accepted=sum(x['candidate_accepted'] for x in records),loss_window_rows=sum(x['near_loss'] for x in records),loss_window_accepted=sum(x['near_loss'] and x['candidate_accepted'] for x in records),records=records,source_sha256={str(p):sha(p) for p in sources},runtime_unchanged=True,training_ready=False,limitations=['Sampled recorded states only; not causally evolved trajectories.','Nominal URDF geometry is not physical force or future COP.','No whole-body or continuous/substep certificate; first-stage probe only. Positive downward margin is not calibrated contact force.'])
(r/'DOWNWARD_MARGIN_SCREEN.json').write_text(json.dumps(report,indent=2));print('DONE',report['accepted'],'/',len(records),flush=True)
