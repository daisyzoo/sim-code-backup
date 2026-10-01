"""Exact recorded-Jacobian replay before one-step Y-request allocation probes."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
cases=[('region_measured_bounds_groups_r1',840001,'push_box_to_bin'),('region_measured_bounds_groups_r1',840004,'nudge_mailer_to_bin'),('rear_cop_measured_bounds_groups_r1',840001,'push_box_to_bin'),('rear_cop_measured_bounds_groups_r1',840004,'nudge_mailer_to_bin')];reports=[]
for run,cid,task in cases:
 ep=w/run/f'case_{cid}/layout_{cid}_{task}';prov=json.loads((ep.parent/'provenance.json').read_text());src=prov['source_sha256'];snapshot=ep.parent/'source_snapshot';n='simfoundry/data/bounded_ik.py';assert sha(snapshot/n)==src[n];solver=module(snapshot/n,'archived_bounded').bounded_damped_step
 geometry=next(k for k in src if k.endswith('/articulated_hand_geometry.py'));assert sha(snapshot/geometry)==src[geometry];gm=module(snapshot/geometry,'archived_geometry');assets=['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/robots/g1_assets.py','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py']
 for a in assets:assert sha(repo/a)==src[a]
 model=gm.ArticulatedHandGeometry(repo/assets[0],repo/assets[1]);side='right' if task=='push_box_to_bin' else 'left';active_slice=slice(3,6) if side=='right' else slice(0,3);active_y=4 if side=='right' else 1
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(np.float32);u=z['action'][:,12:23].astype(np.float32)
 fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};expert={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};coord=json.loads((ep/'coordination.json').read_text());lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;penalty=np.full(11,np.float32(.045**2),dtype=np.float32);penalty[0]=np.float32(.12**2);damping=np.sqrt(penalty);rows=[]
 for c in coord:
  t=c['step'];r=fr[t]
  if 'control_jacobian_world' not in c or r['mode']!='top_push':continue
  assert not c.get('region_joint_override') and not c['terminal_joint_hold'] and c['contact_bout_yaw_tracking'] is None
  assert np.array_equal(q[t],np.array(c['upper_q'],dtype=np.float32));assert np.array_equal(np.array(r['target_xyz']),np.array(expert[t]['target_xyz']))
  position=np.array(c['control_jacobian_world'],dtype=np.float32);errors=[]
  for hand in ['left','right']:
   target=r['target_xyz'] if hand==side else c['inactive_anchor'];current=np.array(c['control_point_positions'][hand],dtype=np.float32);errors.extend(np.clip(np.float32(.72)*(np.array(target,dtype=np.float32)-current),np.float32(-.035),np.float32(.035)).tolist())
  normal=c['contact_normal_tracking'];assert normal is not None
  jac=np.vstack([position,np.array(normal['jacobian'],dtype=np.float32)]);error=np.r_[np.array(errors,dtype=np.float32),np.array(normal['error'],dtype=np.float32)];prior=np.zeros(11,dtype=np.float32);prior[0]=c['preferred_waist_step_rad'];offset=np.array(r['control_offset_local']);goal=np.array(r['target_xyz']);T,_,_=model.fk(side,q[t]);current_point=T[:3,3]+T[:3,:3]@offset;assert np.max(abs(current_point-r['observed_support_xyz']))<2e-6
  def solve(e):
   dq=solver(jac,e,q[t],lo,hi,limits,damping,preferred_step=prior);target=q[t]+dq;target[0]=np.clip(target[0],-.98,.98);assigned=target.astype(np.float32);slewed=np.clip(assigned,u[t-1]-np.float32(.055),u[t-1]+np.float32(.055));command=np.clip(slewed,np.array(U1_JOINT_LIMIT_LO)[12:23],np.array(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32);return command,dq
  command,dq=solve(error);delta=float(np.max(abs(command-u[t])));assert delta<=1.2e-7,(run,task,t,delta,command.tolist(),u[t].tolist())
  probes=[]
  original_damping=damping.copy()
  for scale in [1.,.5,.25]:
   e=error.copy();damping=original_damping*scale;cmd,step=solve(e);T,_,_=model.fk(side,cmd);point=T[:3,3]+T[:3,:3]@offset;res=jac@step-e
   probes.append(dict(damping_scale=scale,command=cmd.tolist(),waist_command_rad=float(cmd[0]),goal_minus_nominal_fk_mm=((goal-point)*1000).tolist(),nominal_point_delta_mm=((point-current_point)*1000).tolist(),weighted_position_linear_residual_xyz_mm=(res[:6]*1000).tolist(),weighted_normal_linear_residual_mm=(res[6:]*1000).tolist(),step_bounds_passed=bool(np.all(abs(step)<=limits+1e-7)),planning_bounds_passed=bool(np.all(cmd>=lo-1e-7) and np.all(cmd<=hi+1e-7))))
  damping=original_damping
  rows.append(dict(step=t,loaded=r['contact_load']['observed_vertical_load_n']>=.2,replay_max_abs_error_rad=delta,probes=probes))
 assert rows;reports.append(dict(run=run,episode=ep.name,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','frontal_bypass.json','expert_control.json','coordination.json']},archived_solver_sha256=sha(snapshot/'simfoundry/data/bounded_ik.py'),archived_geometry_sha256=sha(snapshot/geometry),asset_sha256={n:sha(repo/n) for n in assets}))
out=dict(passed=True,episodes=reports,total_sampled_push_frames=sum(len(r['rows']) for r in reports),max_actual_command_replay_error_rad=max(x['replay_max_abs_error_rad'] for r in reports for x in r['rows']),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Recorded every20frame position Jacobian and normal rows. Reconstruct exact float32 errors, bounds, regularization, prior and final slew before counterfactual damping scaling. Position/normal task errors and step/joint bounds unchanged; projected geometry still requires separate validation. Three one-step algebra/FK allocations, no measured future contact, no altered runtime, no claim of reachability of a whole trajectory or success.')
p=w/'loaded_damping_allocation_probe_r1';p.mkdir(exist_ok=False);(p/'RESULT.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='episodes'})
