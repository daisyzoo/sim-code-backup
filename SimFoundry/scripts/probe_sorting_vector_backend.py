#!/usr/bin/env python3
"""Infrastructure-only vector physics probe; no learning, admission or assistance."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--num-envs',type=int,default=4)
AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import torch
from isaaclab.envs import ManagerBasedRLEnv
from simfoundry.isaac_envs.registry import resolve_scene_env
from simfoundry.robots.g1_assets import u1_sorting_default_qpos_np,G1_U1_23DOF_JOINT_NAMES
from isaaclab_newton.physics.newton_manager import NewtonManager

env=None
try:
    args.out.mkdir(parents=True,exist_ok=False)
    cfg=resolve_scene_env('sorting_station_g1_23').env_cfg_cls()
    cfg.scene.num_envs=args.num_envs;cfg.sim.device=args.device;cfg.episode_length_s=40.
    cfg.sim.physics.default.solver_cfg.use_mujoco_contacts=False
    cfg.scene.d435i=None;cfg.scene.viewer_cam=None;cfg.observations.rgb=None
    default=u1_sorting_default_qpos_np(zero_upper_body=True)
    cfg.scene.robot.init_state.joint_pos=dict(zip(G1_U1_23DOF_JOINT_NAMES,default.tolist()))
    env=ManagerBasedRLEnv(cfg=cfg);env.reset()
    robot=env.scene['robot'];ids=[robot.joint_names.index(n) for n in G1_U1_23DOF_JOINT_NAMES]
    q0=robot.data.joint_pos[:,ids].clone();assert float(q0[:,12:].abs().max())<1e-4
    origin=env.scene.env_origins.clone()
    initial={k:env.scene[k].data.root_pos_w.clone()-origin for k in ['parcel_box','mailer']}
    assert len(torch.unique(origin,dim=0))==args.num_envs
    for v in initial.values():assert float((v-v[:1]).abs().max())<1e-4
    action=torch.zeros((args.num_envs,23),device=env.device)
    for _ in range(5):env.step(action)
    torch.cuda.synchronize();begin=time.perf_counter();max_q=0.
    for _ in range(32):
        obs,reward,terminated,truncated,info=env.step(action)
        assert not bool(terminated.any() or truncated.any())
        q=robot.data.joint_pos[:,ids];assert torch.isfinite(q).all()
        max_q=max(max_q,float(q[:,12:].abs().max()))
    torch.cuda.synchronize();duration=time.perf_counter()-begin
    final={k:(env.scene[k].data.root_pos_w-origin).cpu().tolist() for k in initial}
    solver=NewtonManager._solver
    report=dict(status='physics_probe_complete',num_envs=args.num_envs,control_steps=32,
        timed_seconds=duration,env_transitions_per_second=32*args.num_envs/duration,
        first_upper_q_max_rad=float(q0[:,12:].abs().max()),max_upper_q_during_zero_action_rad=max_q,
        origins=origin.cpu().tolist(),initial={k:v.cpu().tolist() for k,v in initial.items()},final=final,
        cuda_peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
        mujoco_mapping_shape=list(solver.mjc_geom_to_newton_shape.shape),
        action='zero offsets throughout; waist zero; no object writes after reset',
        limitations='Physics infrastructure only. Cameras removed, default layout. No task training, policy, RGB equivalence, reward validation or demonstration admission.',training_ready=False,goal_complete=False)
    (args.out/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
finally:
    if env is not None:env.close()
    app.close()
