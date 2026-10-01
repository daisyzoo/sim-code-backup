"""Original recorded Cartesian IK inputs, frozen observed states, no recursive dynamics.
Checks default compatibility and geometry-constrained task feasibility at logged
Jacobian frames. Historical colliding current states are reported, not hidden.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_self_clearance_task_ik_probe';sys.path[:0]=[str(repo),str(stage),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from self_clearance import BilateralElbowClearance
from task_ik import solve
from simfoundry.data.bounded_ik import bounded_damped_step
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');geometry=BilateralElbowClearance(model,stage/'elbow_torso_hulls.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23];hi=np.array(U1_JOINT_LIMIT_HI)[12:23];lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;penalty=np.full(11,np.float32(.045**2),dtype=np.float32);penalty[0]=np.float32(.12**2);reports=[]
for cid in [840001,840004,840000,840005]:
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ep=w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}';coord=json.loads((ep/'coordination.json').read_text());experts={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};side='right' if task=='push_box_to_bin' else 'left'
  with np.load(ep/'raw.npz') as z:actions=z['action'][:,12:23];measured=z['q'][:,12:23]
  records=[]
  for c in coord:
   if 'control_jacobian_world' not in c:continue
   t=c['step'];q=np.array(c['upper_q'],dtype=np.float32);assert np.array_equal(q,measured[t].astype(np.float32));assert c['contact_bout_yaw_tracking'] is None
   J=np.array(c['control_jacobian_world'],dtype=np.float32);error=[]
   for hand in ['left','right']:
    target=experts[t]['target_xyz'] if hand==side else c['inactive_anchor'];point=np.array(c['control_point_positions'][hand],dtype=np.float32);error.extend(np.clip(np.float32(.72)*(np.array(target,dtype=np.float32)-point),np.float32(-.035),np.float32(.035)))
   error=np.array(error,dtype=np.float32)
   if c['contact_normal_tracking'] is not None:J=np.vstack([J,np.array(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]);error=np.r_[error,np.array(c['contact_normal_tracking']['error'],dtype=np.float32)]
   prior=np.zeros(11,dtype=np.float32);prior[0]=c['preferred_waist_step_rad'];args=dict(jacobian=J,error=error,current=q,previous=actions[t-1],lower=lo,upper=hi,step_limits=limits,damping=np.sqrt(penalty),geometry=geometry,preferred_step=prior)
   baseline=q.astype(float)+bounded_damped_step(J,error,q,lo,hi,limits,np.sqrt(penalty),preferred_step=prior);off,_=solve(enabled=False,**args);assert np.array_equal(off,baseline)
   command,meta=solve(enabled=True,**args);meta.update(step=t,mode=experts[t]['mode'],current_minimum_gap_m=float(geometry.constraints(q).min()),default_off_equal=True)
   if command is not None:
    assert np.min(geometry.constraints(command))>=.005-2e-7;assert np.max(abs(command-actions[t-1]))<=.0550002;assert np.all(abs(command-q)<=limits+2e-7)
    meta['command']=command.tolist()
   records.append(meta)
  report=dict(episode=ep.name,input_count=len(records),accepted=sum(r['accepted'] for r in records),overrides=sum(r.get('override',False) for r in records),historical_current_below_margin=sum(r['current_minimum_gap_m']<.005 for r in records),records=records,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','expert_control.json']});reports.append(report);print(ep.name,'inputs',len(records),'accepted',report['accepted'],'overrides',report['overrides'],'historical unsafe',report['historical_current_below_margin'],flush=True)
  (stage/'PROGRESS.json').write_text(json.dumps(dict(episodes=reports,training_ready=False),indent=2))
out=dict(scope=__doc__,episodes=reports,source_sha256={p.name:sha(p) for p in [stage/'task_ik.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json']},checker_sha256=sha(Path(__file__)),default_off_equal=True,collector_wired=False,physical_started=False,training_ready=False);(stage/'RECORD_INPUT_CHECK.json').write_text(json.dumps(out,indent=2))
