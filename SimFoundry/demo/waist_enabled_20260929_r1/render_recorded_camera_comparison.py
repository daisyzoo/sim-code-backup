"""Static RTX observation diagnostic, NOT dynamics replay or training data.
Set recorded joints/parcel poses, forward kinematics without physics, render both
original intrinsics and0.4 focal scale. Original recorded RGB is retained alongside.
Refuse while any collector is active. All eight completed push conditions required.
"""
from pathlib import Path
import argparse,json,sys,hashlib,os,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--out',required=True)
AppLauncher.add_app_launcher_args(p);a=p.parse_args();r=Path(a.run).resolve();out=Path(a.out).resolve()
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  tokens=proc.joinpath('cmdline').read_bytes().split(b'\0');state=proc.joinpath('stat').read_text().split(') ',1)[1].split()[0]
 except (OSError,IndexError):continue
 if state!='Z' and any(Path(os.fsdecode(t)).name=='collect_paired_sorting.py' for t in tokens if t):raise RuntimeError('Physical collector remains active: '+proc.name)
assert not out.exists(),'New output directory required'
protocol=json.loads((r/'PROTOCOL.json').read_text());sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
for path,digest in protocol['frozen_files_sha256'].items():assert sha(path)==digest,path
episodes=[]
for item in protocol['commands']:
 if item['wait']:continue
 for task in item['tasks']:
  ep=r/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}"
  assert json.loads((ep/'quality.json').read_text())['frames']==1200
  for name in ['raw.npz','trace.npz','parcel_orientation.npz','viewer_observer.json']:assert (ep/name).is_file()
  episodes.append(ep)
assert len(episodes)==8
out.mkdir(parents=True)
app=AppLauncher(a,enable_cameras=True).app
import torch
from PIL import Image,ImageDraw
from scipy.spatial.transform import Rotation
from isaaclab.envs import ManagerBasedRLEnv
from simfoundry.isaac_envs.registry import resolve_scene_env
from simfoundry.robots.g1_assets import G1_U1_23DOF_JOINT_NAMES,u1_sorting_default_qpos_np
from simfoundry.calibration.sorting_station import reset_sorting_parcels,_set_visible,_write_pose,_DECORATIVE_PARCELS
from simfoundry.scene_bridge.labels import sync_shipping_labels
from simfoundry.data.sorting_quality import resolve_hand_indices,palm_xyz
cfg=resolve_scene_env('sorting_station_g1_23').env_cfg_cls();cfg.scene.num_envs=1;cfg.seed=0;cfg.sim.device=a.device
cfg.sim.physics.default.solver_cfg.use_mujoco_contacts=False
cfg.scene.robot.init_state.joint_pos=dict(zip(G1_U1_23DOF_JOINT_NAMES,u1_sorting_default_qpos_np(zero_upper_body=True).tolist()))
env=None;reports=[];frames=[0,395,795,1195]
def save_status(state,error=None):
 (out/'STATUS.json').write_text(json.dumps(dict(state=state,pid=os.getpid(),error=error,completed_episodes=len(reports),training_ready=False),indent=2))
try:
 env=ManagerBasedRLEnv(cfg=cfg);robot=env.scene['robot'];camera=env.scene['d435i'];hands=resolve_hand_indices(robot)
 ids=[robot.joint_names.index(n) for n in G1_U1_23DOF_JOINT_NAMES];save_status('running')
 for ep in episodes:
  layout=json.loads((ep.parent/'explicit_layout.json').read_text());task=ep.name.split(f"layout_{layout['layout_id']}_",1)[1]
  env.reset(seed=0)
  reset_sorting_parcels(env,task_id=task,single_parcel=False,rng=np.random.default_rng(layout['seed']),box_xyz=tuple(layout['box_xyz']),mailer_xyz=tuple(layout['mailer_xyz']),box_yaw=layout.get('box_yaw',0.),mailer_yaw=layout.get('mailer_yaw',0.))
  for i,name in enumerate(_DECORATIVE_PARCELS):_set_visible(env,name,False);_write_pose(env,name,(5.+i,5.,.3))
  observers={x['pre_action_step']:x for x in json.loads((ep/'viewer_observer.json').read_text())['frames']}
  dest=out/ep.name;dest.mkdir();records=[];sheet=Image.new('RGB',(1280,795));draw=ImageDraw.Draw(sheet)
  with np.load(ep/'raw.npz') as raw,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
   assert list(raw['joint_names'])==list(G1_U1_23DOF_JOINT_NAMES)
   for col,t in enumerate(frames):
    q=torch.tensor(raw['q'][t:t+1],dtype=torch.float32,device=env.device)
    robot.write_joint_state_to_sim_index(position=q,velocity=torch.zeros_like(q),joint_ids=ids)
    for key,name in [('box','parcel_box'),('mailer','mailer')]:
     asset=env.scene[name];pose=torch.tensor(np.r_[tr[key][t],ori[key][t]][None],dtype=torch.float32,device=env.device)
     asset.write_root_pose_to_sim_index(root_pose=pose);asset.write_root_velocity_to_sim_index(root_velocity=torch.zeros((1,6),device=env.device))
    env.scene.write_data_to_sim();env.sim.forward();sync_shipping_labels(env)
    observed=observers[t];K=np.asarray(observed['policy_camera_intrinsics'],dtype=np.float32);original=Image.fromarray(raw['rgb'][t].transpose(1,2,0));original.save(dest/f'{t:04d}_recorded.png')
    sheet.paste(original.resize((320,240)),(col*320,0));draw.text((col*320,242),f'{t} recorded')
    for row,scale in enumerate([1.,.4],start=1):
     desired=K.copy();desired[0,0]*=scale;desired[1,1]*=scale
     camera.set_intrinsic_matrices(torch.tensor(desired[None],device=env.device))
     for _ in range(5):
      env.sim.render();env.scene.update(0.)
      _=camera.data.output['rgb'].torch
     data=camera.data;rgb=data.output['rgb'].torch[0,:,:,:3].detach().cpu().numpy().copy()
     actual_K=data.intrinsic_matrices.torch[0].detach().cpu().numpy();pos=data.pos_w.torch[0].detach().cpu().numpy();quat=data.quat_w_ros.torch[0].detach().cpu().numpy()
     errors=dict(joint_max_abs_rad=float(np.max(abs(robot.data.joint_pos.torch[0,ids].cpu().numpy()-raw['q'][t]))),camera_position_max_m=float(np.max(abs(pos-np.array(observed['policy_camera_position_world'])))),camera_rotation_matrix_max=float(np.max(abs(Rotation.from_quat(quat).as_matrix()-Rotation.from_quat(observed['policy_camera_quat_ros_xyzw']).as_matrix()))),intrinsics_max=float(np.max(abs(actual_K-desired))))
     for side in ['left','right']:errors[side+'_palm_max_m']=float(np.max(abs(np.asarray(palm_xyz(robot,hands[side]))-tr['palm_'+side][t])))
     for key,name in [('box','parcel_box'),('mailer','mailer')]:
      errors[key+'_position_max_m']=float(np.max(abs(env.scene[name].data.root_pos_w.torch[0].cpu().numpy()-tr[key][t])))
      errors[key+'_rotation_matrix_max']=float(np.max(abs(Rotation.from_quat(env.scene[name].data.root_quat_w.torch[0].cpu().numpy()).as_matrix()-Rotation.from_quat(ori[key][t]).as_matrix())))
     assert all(v<1e-4 for k,v in errors.items() if k!='intrinsics_max'),errors
     assert errors['intrinsics_max']<1e-3,errors
     filename=f'{t:04d}_focal{scale:g}.png';Image.fromarray(rgb).save(dest/filename)
     sheet.paste(Image.fromarray(rgb).resize((320,240)),(col*320,row*265));draw.text((col*320,row*265+242),f'{t} RTX focal {scale:g}')
     record=dict(frame=t,scale=scale,image=filename,image_sha256=sha(dest/filename),errors=errors)
     if scale==1.:record['recorded_rgb_mean_abs_pixel_difference']=float(np.mean(abs(rgb.astype(float)-np.asarray(original).astype(float))))
     records.append(record)
  sheet.save(dest/'COMPARISON.jpg');report=dict(episode=ep.name,frames=frames,records=records,source_sha256={name:sha(ep/name) for name in ['raw.npz','trace.npz','parcel_orientation.npz','viewer_observer.json']},comparison_sha256=sha(dest/'COMPARISON.jpg'),actual_visual_review='pending',training_ready=False)
  (dest/'REPORT.json').write_text(json.dumps(report,indent=2));reports.append(report);save_status('running');print(ep.name,'RENDERED_STATIC_NOT_PHYSICS',flush=True)
 (out/'REPORT.json').write_text(json.dumps(dict(scope=__doc__,episodes=reports,script_sha256=sha(__file__),camera_cfg_sha256=sha(ROOT/'simfoundry/isaac_envs/sorting_env_cfg.py'),protocol_sha256=sha(r/'PROTOCOL.json'),training_ready=False),indent=2));save_status('render_complete_visual_review_pending')
except Exception as exc:
 save_status('failed',repr(exc));raise
finally:
 if env is not None:env.close()
 app.close()
