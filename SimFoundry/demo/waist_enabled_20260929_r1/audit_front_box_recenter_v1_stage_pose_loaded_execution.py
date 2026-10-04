"""Full rear force/refinement audit with independently verified nonlinear task-parent execution. Original force/edge mathematics and guards remain; no candidate nonlinear solver is executed."""
from audit_parent_seed_retry_metadata import verify_parent_seed_retry_metadata
from pathlib import Path
import ast,json,hashlib,importlib.util,sys,subprocess
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog,nnls
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_rear_coupled_execution_live import replay_record
from audit_front_box_recenter_v1_stage_rear_xy import reconstruct
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def near(a,b,tol=1.2e-7):
 a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all() and np.max(abs(a-b))<=tol

def verify_original_refinement(trace,parent,actual,previous,q,J,error,damping,lower,upper,limits,point_and_jacobian,rotation,local,core,direction,active):
 assert type(trace['override']) is bool
 near(trace['parent_final_upper_command'],parent,0);near(trace['final_upper_command'],actual,0);near(trace['previous_upper_command'],previous,0)
 axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01];assert axes
 normals=np.asarray([-np.sign(local[k])*rotation[:,k] for k in axes]);p0,_=point_and_jacobian(q)
 def directions(command):
  point,jac=point_and_jacobian(command);motion=point-p0
  return np.r_[normals@motion,direction*motion[1]],np.vstack([normals@jac,direction*jac[1]])
 pd,_=directions(parent);assert trace['threatened_axes']==axes;near(trace['parent_nominal_edge_inward_m'],pd[:-1],2e-10);near(trace['parent_nominal_forward_m'],pd[-1],2e-10)
 low=np.maximum.reduce([lower-q,-limits,previous.astype(float)-.055-q]);high=np.minimum.reduce([upper-q,limits,previous.astype(float)+.055-q])
 if pd.min()>=-1e-7:
  assert trace['override'] is False and trace['reason']=='parent_direction_valid';near(actual,parent,0);return dict(refined=False,reason=trace['reason'])
 if not trace['override']:
  near(actual,parent,0);reason=trace['reason']
  if reason=='empty_original_bound_intersection':assert (low>=high).any()
  elif reason=='linear_initialization_infeasible':
   A=np.vstack([normals@J[active],direction*J[active][1]]);check=linprog(np.zeros(11),A_ub=-A,b_ub=np.zeros(len(A)),bounds=list(zip(low,high)),method='highs');assert check.status==2
  elif reason in ['linear_initialization_failed','nonlinear_solver_failed']:assert type(trace['solver_status']) is int and trace['solver_status']!=0
  elif reason in ['final_float32_constraint_violation','nonfinite_output']:pass
  else:raise AssertionError(('unknown fallback',reason))
  return dict(refined=False,reason=reason,numeric_fallback=reason not in ['empty_original_bound_intersection','linear_initialization_infeasible'])
 assert trace['reason']=='nonlinear_joint_direction' and type(trace['iterations']) is int and 0<trace['iterations']<=300;near(trace['command'],actual,0)
 dq=actual.astype(float)-q;assert np.min(dq-low)>=-2e-7 and np.min(high-dq)>=-2e-7
 d,G=directions(actual);assert d.min()>=-1e-7;near(trace['nominal_edge_inward_m'],d[:-1],2e-10);near(trace['nominal_forward_m'],d[-1],2e-10)
 # Independent first-order stationarity check with analytic URDF Jacobian.
 # Candidate uses finite-difference SLSQP; no candidate optimizer is executed here.
 grad=J.T@(J@dq-error)+damping*damping*dq
 active_grad=[G[i] for i in range(len(d)) if d[i]<=1e-6]
 for i in range(11):
  if dq[i]-low[i]<=2e-6:active_grad.append(np.eye(11)[i])
  if high[i]-dq[i]<=2e-6:active_grad.append(-np.eye(11)[i])
 if active_grad:
  normals_kkt=np.asarray(active_grad);length=np.linalg.norm(normals_kkt,axis=1);normals_kkt=normals_kkt[length>1e-12]/length[length>1e-12,None];_,res=nnls(normals_kkt.T,grad,maxiter=1000)
 else:res=float(np.linalg.norm(grad))
 assert res<=1e-6,('stationarity',res)
 return dict(refined=True,reason=trace['reason'],nominal_min_edge_inward_m=float(min(d[:-1])),nominal_forward_m=float(d[-1]),stationarity_residual=float(res))

def verify_retry_metadata(trace,enabled,eligible,mode):
 assert type(enabled) is bool
 retry=trace.get('analytic_retry') if trace else None
 if retry is None:return False
 assert enabled and eligible and mode=='top_push'
 assert set(retry)=={'attempted','initial_solver_status','initial_iterations','retry_solver_status','retry_iterations','initializer'}
 assert retry['attempted'] is True and type(retry['initial_solver_status']) is int and retry['initial_solver_status']==8
 assert retry['initializer']=='original_linear_feasible_point'
 for k in ['initial_iterations','retry_iterations']:assert type(retry[k]) is int and 0<retry[k]<=300
 assert type(retry['retry_solver_status']) is int and 0<=retry['retry_solver_status']<=9
 if trace['override']:
  assert retry['retry_solver_status']==0 and trace['iterations']==retry['retry_iterations']
 elif trace['reason']=='nonlinear_solver_failed':
  assert retry['retry_solver_status']==trace['solver_status'] and trace['solver_status']!=0
 else:assert trace['reason'] in ['final_float32_constraint_violation','nonfinite_output'] and retry['retry_solver_status']==0
 return True

from audit_closed_peak_trial_refinement import verify_refinement,normalized_trace

def replay(ep,expected_collector):
 from audit_front_box_recenter_v1_stage_contract import verify_front_recontact_v1_stage_source
 verify_front_recontact_v1_stage_source(ep)
 ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];coords=json.loads((ep/'coordination.json').read_text());cs={c['step']:c for c in coords};ex={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())}
 declared=args.get('rear_joint_edge_command',False);assert type(declared) is bool;rear=bool(plan.get('rear_joint_xy_progress',{}).get('enabled'));selected=plan.get('rear_joint_edge_command',{}).get('enabled',False);assert type(selected) is bool and selected==(declared and rear)
 retry_enabled=args.get('rear_joint_edge_analytic_retry',False);assert type(retry_enabled) is bool and (not retry_enabled or declared)
 retry_config=dict(enabled=True,primary_solver_unchanged=True,retry_status=8,finite_endpoint_required=True,maximum_retries=1,initializer='original_linear_feasible_point',objective_bounds_tolerances_unchanged=True,failed_retry='preserve_parent_command')
 if retry_enabled and selected:
  assert plan.get('rear_joint_edge_analytic_retry')==retry_config
  for k,v in retry_config.items():assert type(plan['rear_joint_edge_analytic_retry'][k]) is type(v)
 else:assert 'rear_joint_edge_analytic_retry' not in plan
 snap=ep.parent/'source_snapshot';source=prov['source_sha256']
 for name,h in source.items():assert sha(snap/name)==h
 if declared:
  assert args['role']=='diagnostic' and args['rear_joint_xy_progress'] and args['rear_coupled_progress'] and args['waist_limit_rad']==1. and args['motion_protocol']=='waist_yaw_enabled_v1' and not args['waist_probe']
  for name in ['joint_edge_command.py','joint_edge_adapter.py','collect_paired_sorting.py']:
   names=[n for n in source if n.endswith('/'+name)];assert len(names)==1 and sha(snap/names[0])==sha(expected_collector if name=='collect_paired_sorting.py' else w/'staged_front_box_recenter_v3'/name)
 if selected:
  config=dict(enabled=True,core_inset_m=.01,waist_command_limit_rad=.98,waist_step_rad=.015,arm_step_rad=.04,final_slew_rad=.055,original_guard_priority=True,first_loaded_preserved=True,requires_joint_xy_override=True,reference='current_offset_frozen_virtual_reference_not_physical_contact',fallback='preserve_parent_command',full_push_ik_trace=True)
  assert plan['rear_joint_edge_command']==config
  for k,v in config.items():assert type(plan['rear_joint_edge_command'][k]) is type(v)
 if not rear:
  assert not any('joint_edge_refinement' in c or 'joint_edge_clearance_intersection' in c for c in coords)
  return dict(passed=True,selected=False,parent_full_push_replay_frames=0,refinement_frames=0,records=[],errors=[],training_ready=False)
 for n in ['simfoundry/robots/g1_assets.py','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py','third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json']:assert sha(repo/n)==source[n]
 solver=module(snap/'simfoundry/data/bounded_ik.py','edge_original_ik').bounded_damped_step
 gp=next(n for n in source if n.endswith('/articulated_hand_geometry.py'));geometry=module(snap/gp,'edge_independent_fk').ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
 key='box' if 'push_box' in ep.name else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';direction=-1 if side=='right' else 1;active=[3,4,5] if side=='right' else [0,1,2]
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(np.float32);u=z['action'][:,12:23].astype(np.float32)
 assert q.shape==u.shape==(1200,11) and np.isfinite(q).all() and np.isfinite(u).all();assert np.max(abs(q[0]))==np.max(abs(u[0]))==0 and np.max(abs(np.diff(u,axis=0)))<=.055002
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
 R=Rotation.from_quat(quat).as_matrix();packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};region=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next((r['step'] for r in region if r['solver'] and r['solver'].get('handover')),None)
 reference=reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover);assert reference['passed'],reference['errors'];overrides={v['step'] for v in reference['records'] if v['joint_xy_override']}
 cfg=ast.parse((snap/'simfoundry/scene_bridge/isaac_cfg.py').read_text());node=next(n for n in ast.walk(cfg) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='core_scale' for t in n.targets));assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'";scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));core=np.asarray(plan['top_recontact']['contact_size_xyz'])*scale;near(core,plan['region_causal_response']['actual_core']['collision_core_size_xyz'],1e-7)
 inward_enabled=bool(plan.get('rear_box_inward_correction',{}).get('enabled'))
 lower=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();upper=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lower[0]=-.98;upper[0]=.98;limits=np.full(11,.04);limits[0]=.015;damping=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10));records=[];parent_count=0
 from audit_front_box_recenter_v1_stage_loaded_parent import build_parent_verifier
 loaded_parent,task_evidence=build_parent_verifier(ep,expected_collector.parent)
 from audit_unloaded_wrist_prior_live import HandModel
 from audit_self_clearance_task_optimality import IndependentElbows
 from audit_joint_edge_clearance_record import verify as verify_intersection
 independent_hand_model=HandModel(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
 elbows=IndependentElbows(expected_collector.parent/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
 intersection_checks=[]
 assert {r['step'] for r in fr['rows']}==set(range(1,1200))
 for f in fr['rows']:
  t=f['step'];c=cs[t];trace=c.get('joint_edge_refinement');eligible=t in overrides and not c.get('region_joint_override') and not c.get('terminal_joint_hold')
  if selected:
   assert isinstance(trace,dict) and type(trace['input_selected']) is bool and trace['input_selected']==eligible
   parent=np.asarray(trace['parent_final_upper_command'],dtype=np.float32);near(parent,trace['parent_final_upper_command'],0);edge_final=np.asarray(trace['final_upper_command'],dtype=np.float32);near(edge_final,trace['final_upper_command'],0);near(trace['previous_upper_command'],u[t-1],0)
  else:assert trace is None;parent=u[t];edge_final=u[t]
  needs_intersection=bool(trace and trace['override'])
  assert ('joint_edge_clearance_intersection' in c)==needs_intersection
  if not needs_intersection:near(edge_final,u[t],0)
  if selected:normalized_trace(trace,inward_enabled)
  verify_parent_seed_retry_metadata(trace,enabled=args['rear_joint_edge_parent_seed_retry'],analytic_enabled=retry_enabled,eligible=bool(eligible),mode=f['mode'],original_verifier=verify_retry_metadata)
  if f['mode']=='top_push':
   loaded_parent(c,f,ex[t],q[t],u[t-1],parent,side,solver);parent_count+=1
  if not selected:continue
  if f['mode']!='top_push' or not eligible:
   assert trace['override'] is False and trace['reason']==('original_mode_guard' if f['mode']!='top_push' else 'original_rear_not_overridden');near(u[t],parent,0);records.append(dict(step=t,refined=False,reason=trace['reason']));continue
  points=[];weights=[]
  packet=packets[t-1];near(packet['post_action_pose'][key],xyz[t],1e-6)
  for contact in packet['parcel_contacts']:
   slots=[i for i,s in enumerate(contact['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1 or not any(side+'_wrist' in s for s in contact['shapes']):continue
   force=np.asarray(contact['force_world_N'])*(1 if slots[0]==1 else -1);weight=-float(force@R[t,:,2])
   if weight>.05:points.append(np.asarray(contact['position_world']));weights.append(weight)
  assert sum(weights)>=.3;world=np.average(points,axis=0,weights=weights);near(world,f['rear_cop_centering']['cop_world'],1e-7);local=R[t].T@(world-xyz[t]);offset=np.asarray(f['control_offset_local'])
  def point_and_jacobian(command):
   T,jl,jw=geometry.fk(side,command);off=T[:3,:3]@offset;x,y,z=off;skew=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);return T[:3,3]+off,jl-skew@jw
  current_point,_=point_and_jacobian(q[t]);near(current_point,f['observed_support_xyz'],2e-6);near(current_point,c['control_point_positions'][side],2e-6)
  J=np.vstack([np.asarray(c['control_jacobian_world'],dtype=np.float32),np.asarray(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]).astype(float);errors=[]
  for hand in ['left','right']:
   goal=f['target_xyz'] if hand==side else c['inactive_anchor'];errors.extend(np.clip(np.float32(.72)*(np.asarray(goal,dtype=np.float32)-np.asarray(c['control_point_positions'][hand],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
  error=np.r_[np.asarray(errors,dtype=np.float32),np.asarray(c['contact_normal_tracking']['error'],dtype=np.float32)].astype(float)
  check=verify_refinement(trace,parent,edge_final,u[t-1],q[t].astype(float),J,error,damping,lower,upper,limits,point_and_jacobian,R[t],local,core,direction,active,inward_enabled=inward_enabled);records.append(dict(step=t,**check))
  if needs_intersection:
   proof=verify_intersection(hand=independent_hand_model,elbows=elbows,coordinate=c,row=f,trace=c['joint_edge_clearance_intersection'],q=q[t].astype(float),previous=u[t-1].astype(float),command=u[t].astype(float),object_xyz=xyz[t],object_rotation=R[t],core_size=plan['region_causal_response']['actual_core']['collision_core_size_xyz'],lower=lower,upper=upper,limits=limits)
   assert proof['passed'];intersection_checks.append(dict(step=t,**proof))
 return dict(passed=True,selected=selected,nonlinear_task_execution=task_evidence,final_intersection_records=intersection_checks,final_intersection_changed=sum(v["changed"] for v in intersection_checks),parent_full_push_replay_frames=parent_count,refinement_frames=sum(r['refined'] for r in records),numeric_fallback_frames=sum(r.get('numeric_fallback',False) for r in records),records=records,retry_attempts=sum(bool(c.get('joint_edge_refinement',{}).get('analytic_retry')) for c in coords),parent_seed_retry_attempts=sum(bool(c.get('joint_edge_refinement',{}).get('parent_seed_retry')) for c in coords),errors=[],max_stationarity_residual=max((r.get('stationarity_residual',0) for r in records),default=0),source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','expert_control.json','frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json','region_approach.json']},training_ready=False)


def inspect(ep):
 from audit_front_box_recenter_v1_stage_pose_live import inspect as inspect_pose,source_contract
 ep=Path(ep).resolve();stage=source_contract(ep);pose=inspect_pose(ep)
 assert pose==json.loads((ep/'FRONT_BOX_RECENTER_V1_STAGE_POSE_LIVE_V2_AUDIT.json').read_text())
 geometry=json.loads((ep/'FRONT_BOX_RECENTER_V1_STAGE_SELF_CLEARANCE_V2_AUDIT.json').read_text())
 assert geometry['passed'] and geometry['episode_clearance_passed']
 assert geometry['auditor_sha256']==sha(w/'audit_front_box_recenter_v1_stage_self_clearance.py')
 for name,digest in geometry['source_sha256'].items():assert sha(ep/name)==digest
 out=replay(ep,stage/'collect_paired_sorting.py')
 out.update(pose_audit_sha256=sha(ep/'FRONT_BOX_RECENTER_V1_STAGE_POSE_LIVE_V2_AUDIT.json'),pose_auditor_sha256=sha(w/'audit_front_box_recenter_v1_stage_pose_live.py'),auditor_sha256=sha(Path(__file__)),original_loaded_auditor_sha256=sha(w/'audit_unloaded_wrist_loaded_execution.py'),scope=__doc__)
 return out
if __name__=='__main__':
 ep=Path(sys.argv[1]);path=ep/'FRONT_BOX_RECENTER_V1_STAGE_POSE_LOADED_EXECUTION_V2_AUDIT.json';assert not path.exists();out=inspect(ep);path.write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['records','source_sha256','scope']})
