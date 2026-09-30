#!/usr/bin/env python3
"""Infrastructure-only vector physics probe; no learning, admission or assistance."""
import argparse,json,sys,time,subprocess,os,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--num-envs',type=int,default=32)
AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import torch
from isaaclab.envs import ManagerBasedRLEnv
from simfoundry.isaac_envs.registry import resolve_scene_env
from simfoundry.robots.g1_assets import u1_sorting_default_qpos_np,G1_U1_23DOF_JOINT_NAMES
from isaaclab_newton.physics.newton_manager import NewtonManager
from simfoundry.data.vector_sorting_reset import reset_paired_layouts

env=None
try:
    args.out.mkdir(parents=True,exist_ok=False)
    cfg=resolve_scene_env('sorting_station_g1_23').env_cfg_cls()
    cfg.scene.num_envs=args.num_envs;cfg.sim.device=args.device;cfg.episode_length_s=40.
    cfg.sim.physics.default.solver_cfg.use_mujoco_contacts=False
    cfg.scene.d435i=None;cfg.scene.viewer_cam=None;cfg.observations.rgb=None
    default=u1_sorting_default_qpos_np(zero_upper_body=True)
    cfg.scene.robot.init_state.joint_pos=dict(zip(G1_U1_23DOF_JOINT_NAMES,default.tolist()))
    env=ManagerBasedRLEnv(cfg=cfg)
    assignments=[];layouts=[]
    for i in range(args.num_envs):
        lid=66004+(i//2)%8;task=('push_box_to_bin','nudge_mailer_to_bin')[i%2]
        path=ROOT/f'demo/natural_coverage24_20260929_r1/case_{lid}/explicit_layout.json'
        layouts.append(json.loads(path.read_text()));assignments.append(dict(env_id=i,layout_id=lid,task=task,layout_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    assert args.num_envs%16==0
    requested=reset_paired_layouts(env,list(range(args.num_envs)),layouts)
    reset_errors={}
    for key,name in [('box','parcel_box'),('mailer','mailer')]:
        asset=env.scene[name];pose=requested[key];xyz=asset.data.root_pos_w;quat=asset.data.root_quat_w
        position_error=float((xyz-pose[:,:3]).abs().max());quat_error=float(torch.minimum(torch.linalg.norm(quat-pose[:,3:],dim=1),torch.linalg.norm(quat+pose[:,3:],dim=1)).max())
        assert position_error<1e-5 and quat_error<1e-5
        reset_errors[key]=dict(position_error_m=position_error,quaternion_error=quat_error)
    robot=env.scene['robot'];ids=[robot.joint_names.index(n) for n in G1_U1_23DOF_JOINT_NAMES]
    q0=robot.data.joint_pos[:,ids].clone();assert float(q0[:,12:].abs().max())<1e-4
    origin=env.scene.env_origins.clone()
    initial={k:env.scene[k].data.root_pos_w.clone()-origin for k in ['parcel_box','mailer']}
    assert len(torch.unique(origin,dim=0))==args.num_envs
    assert len({x['layout_id'] for x in assignments})==8
    action=torch.zeros((args.num_envs,23),device=env.device)
    for _ in range(5):env.step(action)
    snapshot={name:env.scene[name].data.root_state_w.clone() for name in ['parcel_box','mailer']}
    q_before=robot.data.joint_pos.clone();v_before=robot.data.joint_vel.clone()
    replacement=json.loads((ROOT/'demo/natural_coverage24_20260929_r1/case_66010/explicit_layout.json').read_text())
    partial=reset_paired_layouts(env,[0],[replacement]);isolation={}
    for name in snapshot:
        difference=float((env.scene[name].data.root_state_w[1:]-snapshot[name][1:]).abs().max());assert difference<1e-7;isolation[name]=difference
    isolation['robot_q']=float((robot.data.joint_pos[1:]-q_before[1:]).abs().max());isolation['robot_qd']=float((robot.data.joint_vel[1:]-v_before[1:]).abs().max())
    assert isolation['robot_q']<1e-7 and isolation['robot_qd']<1e-7
    assert float(robot.data.joint_pos[0,ids[12:]].abs().max())<1e-4
    for key,name in [('box','parcel_box'),('mailer','mailer')]:
        assert float((env.scene[name].data.root_pos_w[0]-partial[key][0,:3]).abs().max())<1e-5
    # Restore the complete assignment as a fresh episode before timing.
    reset_paired_layouts(env,list(range(args.num_envs)),layouts)
    for _ in range(5):env.step(action)
    torch.cuda.synchronize();begin=time.perf_counter();max_q=0.
    for _ in range(128):
        obs,reward,terminated,truncated,info=env.step(action)
        assert not bool(terminated.any() or truncated.any())
        q=robot.data.joint_pos[:,ids];assert torch.isfinite(q).all()
        max_q=max(max_q,float(q[:,12:].abs().max()))
    torch.cuda.synchronize();duration=time.perf_counter()-begin
    final={k:(env.scene[k].data.root_pos_w-origin).cpu().tolist() for k in initial}
    solver=NewtonManager._solver
    gpu_query=subprocess.run(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],capture_output=True,text=True)
    gpu_process_mib=[line for line in gpu_query.stdout.splitlines() if line.split(',')[0].strip()==str(os.getpid())]
    report=dict(assignments=assignments,reset_errors=reset_errors,partial_reset_state_isolation=isolation,own_process_gpu_memory_mib=gpu_process_mib,status='physics_probe_complete',num_envs=args.num_envs,control_steps=128,
        timed_seconds=duration,env_transitions_per_second=128*args.num_envs/duration,
        first_upper_q_max_rad=float(q0[:,12:].abs().max()),max_upper_q_during_zero_action_rad=max_q,
        origins=origin.cpu().tolist(),initial={k:v.cpu().tolist() for k,v in initial.items()},final=final,
        cuda_peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
        mujoco_mapping_shape=list(solver.mjc_geom_to_newton_shape.shape),
        action='zero offsets throughout; waist zero; no object writes after reset',
        limitations='Infrastructure only. Cameras removed; 8 frozen layouts x2 tasks repeated twice. Partial reset isolation is an immediate state check, not proof of identical future dynamics or solver warmstart. Zero actions only; no task training or admission.',training_ready=False,goal_complete=False)
    (args.out/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
finally:
    if env is not None:env.close()
    app.close()
