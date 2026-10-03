"""Exercise stop-context diagnostics on declared synthetic coherent archives.
Both hand sides are covered. These fixtures are not physical rollout evidence;
old actual stop files must be rejected for lacking the new source/pose archive.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(W))
from front_projection_stop_context import verify
from front_loaded_material_projection import cap_loaded_reference
from audit_unloaded_wrist_prior_live import HandModel
from audit_front_projection_stop_context import inspect
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';verts=ROOT/'assets/robots/g1_hand_support_vertices.json';quality=ROOT/'simfoundry/data/sorting_quality.py'
hand=HandModel(urdf,verts);tree=ast.parse(quality.read_text());offset=np.array(ast.literal_eval(next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PALM_OFFSET' for t in n.targets))))
positives=[];negative=[]
for side,key,actor,other in [('left','mailer','mailer','parcel_box'),('right','box','parcel_box','mailer')]:
 q=np.zeros(11);poses={s:hand.fk(q,s) for s in ['left','right']};pose=poses[side];normal=np.array([0.,0.,1.]);center=hand.vertices[side].mean(axis=0);local_normal=pose[:3,:3].T@normal;ref_local=center+local_normal*(float((hand.vertices[side]@local_normal).min())-float(center@local_normal));ref=pose[:3,3]+pose[:3,:3]@ref_local
 material=ref[:2]+[1.,0.];parent=ref[:2]+[.001,0.];prev=ref[:2];record=cap_loaded_reference(enabled=True,capture_complete=True,mode='top_push',parent_xy=parent,previous_xy=prev,reference_xy=ref[:2],surface_xy=material,normal_load_n=1.)
 assert record['requires_recontact'];target=[*material,.77];otherxyz=[.5,.2,.77];pre=dict(step=2,phase='pre',accepted=True,upper_q=q.tolist(),runtime_link_poses={'synthetic_link':np.eye(4).tolist()});post=dict(pre,step=1,phase='post');final=dict(step=1,phase='final_command',command=[0.]*11)
 obs=dict(timing='current_pre_action_no_action_issued',step=2,recorded_frames=2,previous_solved_action_step=1,upper_q_waist_left_right=q.tolist(),previous_upper_command=[0.]*11,target_actor=actor,other_actor=other,target_xyz=target,other_xyz=otherxyz,target_quat_xyzw=[0.,0.,0.,1.],other_quat_xyzw=[0.,0.,0.,1.],hand_pose_world={k:v.tolist() for k,v in poses.items()},projected_support_context={'center_local':center.tolist(),'reference_local':ref_local.tolist(),'world_normal':normal.tolist()})
 packet=dict(after_action_step=1,post_action_pose={key:target,'box' if key=='mailer' else 'mailer':otherxyz,**{'palm_'+s:(m[:3,3]+m[:3,:3]@offset).tolist() for s,m in poses.items()}},parcel_contacts=[dict(shapes=['/World/robot/'+side+'_wrist_roll','/World/'+actor+'/geometry'],force_world_N=[0.,0.,-1.])])
 failure=dict(kind='stop',phase='front_loaded_reference_cap',step=2,reason='empty_original_slew_lead_material_intersection',record=record,stop_observation=obs)
 kw=dict(frames=2,pre=pre,previous_post=post,previous_final=final,previous_action=np.zeros(11),packet=packet,hand=hand,palm_offset=offset)
 result=verify(failure,**kw);assert result['stop_context_checks_passed'] and not result['short_episode_quality_passed'] and not result['material_surface_geometry_independently_verified'];positives.append(dict(side=side,synthetic_fixture=True,result=result))
 changes={
 'wrong_step':lambda f,k:f['stop_observation'].update(step=3),
 'wrong_q':lambda f,k:f['stop_observation']['upper_q_waist_left_right'].__setitem__(0,.1),
 'wrong_previous_command':lambda f,k:f['stop_observation']['previous_upper_command'].__setitem__(0,.1),
 'wrong_target_xyz':lambda f,k:f['stop_observation']['target_xyz'].__setitem__(0,9.),
 'nonunit_quaternion':lambda f,k:f['stop_observation'].update(target_quat_xyzw=[0.,0.,0.,2.]),
 'wrong_hand_pose':lambda f,k:f['stop_observation']['hand_pose_world'][side][0].__setitem__(3,9.),
 'wrong_packet_time':lambda f,k:k['packet'].update(after_action_step=0),
 'no_load':lambda f,k:k['packet']['parcel_contacts'][0].update(force_world_N=[0.,0.,0.]),
 'wrong_reference':lambda f,k:f['stop_observation']['projected_support_context'].update(reference_local=[1.,1.,1.]),
 'false_emission':lambda f,k:f['record'].update(command_xy=[0.,0.]),
 }
 for label,mutate in changes.items():
  f=copy.deepcopy(failure);k=copy.deepcopy(kw);mutate(f,k);rejected=False
  try:verify(f,**k)
  except (AssertionError,KeyError,ValueError):rejected=True
  assert rejected,label;negative.append(dict(side=side,case=label,rejected=True))
for layout,task in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
 ep=W/'front_loaded_physical_r1'/f'case_{layout}'/f'layout_{layout}_{task}';rejected=False
 try:inspect(ep)
 except (AssertionError,KeyError):rejected=True
 assert rejected;negative.append(dict(case='old_source_missing_new_stop_archive',episode=ep.name,rejected=True))
files=[Path(__file__),W/'front_projection_stop_context.py',W/'audit_front_projection_stop_context.py',W/'front_loaded_projection_independent_math.py',W/'front_loaded_material_projection.py',W/'audit_unloaded_wrist_prior_live.py',W/'front_projection_stage_source_binding.py',urdf,verts,quality]
out=W/'FRONT_PROJECTION_STOP_CONTEXT_CHECK.json';assert not out.exists();out.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,positive=positives,negative=negative,source_sha256={str(p):sha(p) for p in files},actual_new_stop_physics_verified=False,training_ready=False),indent=2));print('Passed2 synthetic sides,20 tampering cases and2 old-source rejections; no physical stop claim')
