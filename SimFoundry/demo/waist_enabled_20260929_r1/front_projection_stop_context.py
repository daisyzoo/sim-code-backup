"""Independent verification of an unissued projection-stop observation.
Checks timing, stored q/action, measured/FK hands, parcel translations, rotations,
support reference and raw contact normal load, then scalar interval arithmetic.
The current material XY and unissued parent COP command remain logged inputs;
this diagnostic does NOT independently prove their complete route reconstruction.
Any short episode remains failed under the unchanged full-horizon quality gates.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from front_loaded_projection_independent_math import verify as verify_math
from audit_unloaded_wrist_prior_live import near

def verify(failure,*,frames,pre,previous_post,previous_final,previous_action,packet,hand,palm_offset):
 assert failure['kind']=='stop' and failure['phase']=='front_loaded_reference_cap'
 assert failure['reason']=='empty_original_slew_lead_material_intersection'
 t=failure['step'];assert type(t) is int and t==frames and t>0
 obs=failure['stop_observation'];assert obs['timing']=='current_pre_action_no_action_issued'
 assert obs['step']==obs['recorded_frames']==t and obs['previous_solved_action_step']==t-1
 assert pre['step']==t and pre['phase']=='pre' and pre['accepted'] is True
 assert previous_post['step']==t-1 and previous_post['phase']=='post'
 assert previous_final['step']==t-1 and previous_final['phase']=='final_command'
 near(obs['upper_q_waist_left_right'],pre['upper_q'],0.);near(pre['upper_q'],previous_post['upper_q'],0.)
 assert pre['runtime_link_poses']==previous_post['runtime_link_poses']
 q=np.asarray(obs['upper_q_waist_left_right']);assert q.shape==(11,)
 near(obs['previous_upper_command'],previous_final['command'],0.);near(obs['previous_upper_command'],previous_action,0.)
 assert packet['after_action_step']==t-1
 actor=obs['target_actor'];assert actor in ('parcel_box','mailer')
 key='box' if actor=='parcel_box' else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left'
 assert obs['other_actor']==('mailer' if key=='box' else 'parcel_box')
 near(obs['target_xyz'],packet['post_action_pose'][key],2e-6);near(obs['other_xyz'],packet['post_action_pose'][other],2e-6)
 rotations={}
 for which in ['target','other']:
  quat=np.asarray(obs[which+'_quat_xyzw'],float);assert quat.shape==(4,) and np.isfinite(quat).all();near(np.linalg.norm(quat),1.,1e-6);rotations[which]=Rotation.from_quat(quat).as_matrix()
 poses={}
 for s in ['left','right']:
  pose=np.asarray(obs['hand_pose_world'][s],float);assert pose.shape==(4,4);near(pose[3],[0,0,0,1],1e-8);near(pose[:3,:3].T@pose[:3,:3],np.eye(3),1e-6);assert np.linalg.det(pose[:3,:3])>.999999
  fk=hand.fk(q,s);near(pose[:3,3],fk[:3,3],1e-4);assert Rotation.from_matrix(fk[:3,:3].T@pose[:3,:3]).magnitude()<=1e-4
  near(pose[:3,3]+pose[:3,:3]@palm_offset,packet['post_action_pose']['palm_'+s],2e-6);poses[s]=pose
 r=rotations['target'];normal=0.
 for c in packet['parcel_contacts']:
  slots=[i for i,label in enumerate(c['shapes']) if '/'+actor+'/' in label]
  if len(slots)!=1 or not any(side+'_wrist' in label for label in c['shapes']):continue
  f=np.asarray(c['force_world_N'],float)*(1. if slots[0]==1 else -1.);assert f.shape==(3,) and np.isfinite(f).all()
  load=-float(f@r[:,2])
  if load>.05:normal+=load
 assert normal>=.3
 ctx=obs['projected_support_context'];pose=poses[side];center=np.asarray(ctx['center_local'],float);assert center.shape==(3,);local_normal=pose[:3,:3].T@r[:,2]
 heights=hand.vertices[side]@local_normal;offset=center+local_normal*(float(heights.min())-float(center@local_normal))
 near(ctx['reference_local'],offset,2e-6);near(ctx['world_normal'],r[:,2],2e-6)
 reference=pose[:3,3]+pose[:3,:3]@offset
 record=failure['record'];near(record['reference_xy'],reference[:2],2e-6);near(record['normal_load_n'],normal,2e-6)
 result=verify_math(record,parent=record['parent_xy'],previous=record['previous_command_xy'],reference=record['reference_xy'],material=record['material_surface_xy'],normal=normal)
 assert result['feasible'] is False
 return dict(stop_context_checks_passed=True,attempted_step=t,normal_load_n=normal,no_current_action_issued=True,material_surface_geometry_independently_verified=False,unissued_parent_cop_independently_reconstructed=False,short_episode_quality_passed=False,scope=__doc__,training_ready=False)
