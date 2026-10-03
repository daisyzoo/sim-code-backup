"""Observed loaded tracking and full24-solver-tick pressure diagnostic.
Kinematic target FK is an if-targets-were-reached reference, not a dynamics
prediction. Last-tick and24-tick force statistics are kept distinct. No impulse
balance, actuator torque saturation, friction law, or task-success inference.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
EP=Path(sys.argv[1]).resolve();out=EP/'FRONT_LOADED_TRACKING_RESIDUAL_DIAGNOSTIC.json';assert not out.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda n:json.loads((EP/n).read_text());fr=read('frontal_bypass.json');coords={r['step']:r for r in read('coordination.json')};pressure={r['action_step']:r for r in read('peak_load_updates.json')['rows']};packets={r['after_action_step']:r for r in read('solved_contact_forces.json')['rows']};native=read('FRONT_INITIAL_STAGE_POSE_LIVE_V2_AUDIT.json');assert native['passed'] is True
with np.load(EP/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
key='box' if fr['plan']['direction']==-1 else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
with np.load(EP/'trace.npz') as z:xyz=z[key].astype(float)
with np.load(EP/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
with np.load(EP/'substep_contacts.npz') as z:sub={k:z[k] for k in ['action_step','substep_tick','contact_offsets','shape_ids','force_torque_world']}
metadata=read('SUBSTEP_CONTACT_RECORDING.json')['metadata'];labels=metadata['shape_labels'];stride=24+metadata['expected_manager_steps'];assert stride in (25,32)
hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
def point(joints,normal,center):
 pose=hand.fk(joints,side);n=pose[:3,:3].T@normal;verts=hand.vertices[side];offset=center+n*(np.min(verts@n)-float(center@n));return pose[:3,3]+pose[:3,:3]@offset

def stats(values):
 a=np.asarray(values,float);assert a.size and np.isfinite(a).all();return dict(min=float(a.min()),median=float(np.median(a)),mean=float(a.mean()),max=float(a.max()))
rows=[];by_step={r['step']:r for r in fr['rows']};bout=0;previous_push=False
for r in fr['rows']:
 is_push=r['mode']=='top_push'
 if not is_push:previous_push=False;continue
 if not previous_push:bout+=1
 previous_push=True;t=r['step'];c=coords[t];task=c['task_inputs'];assert task is not None
 np.testing.assert_allclose(task['current'],q[t],rtol=0,atol=1e-7);np.testing.assert_allclose(task['previous'],u[t-1],rtol=0,atol=1e-7)
 center=np.array(c['active_support_reference']['center_local']);normal=rot[t,:,2];current=point(q[t],normal,center);command=point(u[t],normal,center)
 np.testing.assert_allclose(current,r['observed_support_xyz'],rtol=0,atol=2e-6)
 np.testing.assert_allclose(current,c['control_point_positions'][side],rtol=0,atol=2e-6)
 desired=np.array(r['target_xyz']);error=np.asarray(task['error']);J=np.asarray(task['jacobian']);delta=u[t]-q[t]
 np.testing.assert_allclose(error[:3],np.clip(.72*(desired-np.array(c['control_point_positions'][side])),-.035,.035),rtol=0,atol=2e-6)
 lo=np.array(task['lower']);hi=np.array(task['upper']);limits=np.array(task['step_limits']);lower=np.maximum(lo,q[t]-limits);upper=np.minimum(hi,q[t]+limits)
 assert min(u[t]-lower)>=-2e-6 and min(upper-u[t])>=-2e-6
 absolute_margin=np.minimum(u[t]-lo,hi-u[t]);step_margin=limits-abs(delta);active=[0,*range(1,6)] if side=='left' else [0,*range(6,11)]
 # Bind every substep to the preceding action. Select the first occurrence of
 # each tick as in the audited recording contract; boundary duplicates remain.
 loads=[];base=(t-1)*stride
 assert np.all(sub['action_step'][base:base+stride]==t-1)
 for tick in range(1,25):
  hits=np.flatnonzero(sub['substep_tick'][base:base+stride]==tick);assert len(hits);i=base+int(hits[0]);load=0.
  for j in range(int(sub['contact_offsets'][i]),int(sub['contact_offsets'][i+1])):
   names=[labels[int(k)] for k in sub['shape_ids'][j]]
   if any(side+'_wrist_roll' in n for n in names) and any('/'+actor+'/' in n for n in names):load+=abs(float(sub['force_torque_world'][j,2]))
  loads.append(load)
 obs=pressure[t]['preceding_observation'];assert obs['observed_after_action_step']==t-1 and obs['observed_solver_substeps']==24
 np.testing.assert_allclose([max(loads),loads[-1]],[obs['previous_action_peak_n'],obs['final_load_n']],rtol=0,atol=1e-10)
 np.testing.assert_allclose(loads[-1],r['contact_load']['observed_vertical_load_n'],rtol=1e-6,atol=1e-5)
 ratios=[]
 for contact in packets[t-1]['parcel_contacts']:
  if any(side+'_wrist_roll' in n for n in contact['shapes']) and any('/'+actor+'/' in n for n in contact['shapes']):
   local=np.asarray(contact['force_torque_contact'])
   if abs(local[0])>.05:ratios.append(float((abs(local[1])+abs(local[2]))/abs(local[0])))
 next_delta=None
 if t+1<len(q):next_delta=(point(q[t+1],normal,center)-current).tolist()
 rows.append(dict(step=t,bout=bout,observed_load_last_tick_N=loads[-1],previous_action24_load=stats(loads),substeps_loaded=sum(x>=.3 for x in loads),desired_z_minus_observed_mm=float((desired[2]-current[2])*1000),kinematic_target_minus_observed_mm=((command-current)*1000).tolist(),next_observed_delta_frozen_reference_mm=None if next_delta is None else (np.array(next_delta)*1000).tolist(),linearized_task_position_step_mm=(J[:3]@delta*1000).tolist(),requested_task_position_step_mm=(error[:3]*1000).tolist(),active_joint_absolute_margin_min_rad=float(min(absolute_margin[active])),active_joint_step_margin_min_rad=float(min(step_margin[active])),active_joint_tracking_error_max_rad=float(max(abs(u[t-1,active]-q[t,active]))),bias_m=r['contact_load']['applied_z_bias_m'],last_tick_contact_tangent_L1_over_normal=ratios,command_xy=desired[:2].tolist(),object_xyz=xyz[t].tolist()))
summaries=[]
for number in sorted({r['bout'] for r in rows}):
 rs=[r for r in rows if r['bout']==number];loaded=[r for r in rs if r['substeps_loaded']>0];after=by_step.get(rs[-1]['step']+1,{})
 summaries.append(dict(bout=number,start=rs[0]['step'],end=rs[-1]['step'],frames=len(rs),exit_reason=after.get('last_recontact_reason','episode_end'),load_last_tick_N=stats([r['observed_load_last_tick_N'] for r in rs]),per_action24_load_mean_N=stats([r['previous_action24_load']['mean'] for r in rs]),per_action24_load_peak_N=stats([r['previous_action24_load']['max'] for r in rs]),desired_z_minus_observed_mm=stats([r['desired_z_minus_observed_mm'] for r in rs]),kinematic_target_z_minus_observed_mm=stats([r['kinematic_target_minus_observed_mm'][2] for r in rs]),next_observed_delta_z_frozen_reference_mm=stats([r['next_observed_delta_frozen_reference_mm'][2] for r in rs if r['next_observed_delta_frozen_reference_mm'] is not None]),absolute_bound_near_frames=sum(r['active_joint_absolute_margin_min_rad']<=1e-5 for r in rs),step_bound_near_frames=sum(r['active_joint_step_margin_min_rad']<=1e-5 for r in rs),active_tracking_error_rad=stats([r['active_joint_tracking_error_max_rad'] for r in rs]),bias_at_original_min_frames=sum(abs(r['bias_m']+.006)<1e-10 for r in rs),contact_L1_ratio=stats([v for r in rs for v in r['last_tick_contact_tangent_L1_over_normal']]) if any(r['last_tick_contact_tangent_L1_over_normal'] for r in rs) else None,object_displacement_xy_mm=((np.array(rs[-1]['object_xyz'][:2])-np.array(rs[0]['object_xyz'][:2]))*1000).tolist()))
files=['raw.npz','coordination.json','frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json','substep_contacts.npz','SUBSTEP_CONTACT_RECORDING.json','peak_load_updates.json','FRONT_INITIAL_STAGE_POSE_LIVE_V2_AUDIT.json'];sources={str(EP/n):sha(EP/n) for n in files};sources.update({str(p):sha(p) for p in [Path(__file__),W/'audit_unloaded_wrist_prior_live.py',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']})
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=EP.name,bouts=summaries,rows=rows,source_sha256=sources,unchanged_task_gates=True,training_ready=False);out.write_text(json.dumps(report,indent=2));print(json.dumps(dict(episode=EP.name,first_bout=summaries[0],push_rows=len(rows)),indent=2))
