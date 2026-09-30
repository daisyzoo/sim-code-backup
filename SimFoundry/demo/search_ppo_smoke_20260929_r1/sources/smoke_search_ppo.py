#!/usr/bin/env python3
"""Infrastructure-only vector physics probe; no learning, admission or assistance."""
import argparse,json,sys,time
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

import numpy as np
from simfoundry.data.search_episode import SearchEpisode
from simfoundry.data.sorting_quality import palm_xyz
import copy,hashlib,shutil
from rsl_rl.runners import OnPolicyRunner
from simfoundry.data.search_vec_env import SearchVecEnv
env=None
try:
    args.out.mkdir(parents=True,exist_ok=False);assert shutil.disk_usage(args.out).free>20.1*2**30
    torch.manual_seed(20260929);np.random.seed(20260929)
    cfg=resolve_scene_env('sorting_station_g1_23').env_cfg_cls();cfg.scene.num_envs=args.num_envs;cfg.sim.device=args.device;cfg.episode_length_s=40.
    cfg.sim.physics.default.solver_cfg.use_mujoco_contacts=False;cfg.scene.d435i=None;cfg.scene.viewer_cam=None;cfg.observations.rgb=None
    default=u1_sorting_default_qpos_np(zero_upper_body=True);cfg.scene.robot.init_state.joint_pos=dict(zip(G1_U1_23DOF_JOINT_NAMES,default.tolist()))
    env=ManagerBasedRLEnv(cfg=cfg);layouts=[];tasks=[]
    for i in range(args.num_envs):
        lid=66008+(i//2)%4;path=ROOT/f'demo/natural_coverage24_20260929_r1/case_{lid}/explicit_layout.json'
        layouts.append(json.loads(path.read_text()));tasks.append(i%2)
    episode=SearchEpisode(env,layouts,tasks);wrapper=SearchVecEnv(episode)
    config=dict(seed=20260929,num_steps_per_env=32,save_interval=100,check_for_nan=True,
        obs_groups={'actor':['policy'],'critic':['policy']},logger='tensorboard',
        actor=dict(class_name='MLPModel',hidden_dims=[128,128],activation='elu',obs_normalization=True,distribution_cfg=dict(class_name='GaussianDistribution',init_std=.3,std_type='log')),
        critic=dict(class_name='MLPModel',hidden_dims=[128,128],activation='elu',obs_normalization=True,distribution_cfg=None),
        algorithm=dict(class_name='PPO',num_learning_epochs=2,num_mini_batches=4,learning_rate=.0003,schedule='fixed',gamma=.99,lam=.95,entropy_coef=.005,desired_kl=.01,max_grad_norm=1.,value_loss_coef=1.,use_clipped_value_loss=True,clip_param=.2,rnd_cfg=None,symmetry_cfg=None))
    (args.out/'CONFIG.json').write_text(json.dumps(config,indent=2))
    (args.out/'PROTOCOL.json').write_text(json.dumps(dict(purpose='Six-update infrastructure smoke, not task convergence or admission',updates=6,steps_per_update=32,envs=args.num_envs,max_transitions=6*32*args.num_envs,wall_timeout_s=240,training_ready=False,goal_complete=False),indent=2))
    runner=OnPolicyRunner(wrapper,copy.deepcopy(config),log_dir=None,device=args.device)
    before=[p.detach().clone() for p in runner.alg.actor.parameters()];begin=time.perf_counter()
    runner.learn(6,init_at_random_ep_len=False)
    delta=max(float((p-b).abs().max()) for p,b in zip(runner.alg.actor.parameters(),before));assert delta>0
    assert wrapper.completed_batches==1 and episode.t==32
    policy=runner.get_inference_policy();obs=wrapper.get_observations()
    with torch.no_grad():prediction=policy(obs).clone()
    assert torch.isfinite(prediction).all()
    checkpoint=args.out/'smoke_checkpoint.pt';runner.save(str(checkpoint),infos={'diagnostic_only':True})
    restored=OnPolicyRunner(wrapper,copy.deepcopy(config),log_dir=None,device=args.device);restored.load(str(checkpoint));restored_policy=restored.get_inference_policy()
    with torch.no_grad():prediction2=restored_policy(obs)
    assert torch.equal(prediction,prediction2)
    (args.out/'TERMINAL.json').write_text(json.dumps(wrapper.last_terminal,indent=2))
    result=dict(status='six_update_save_reload_smoke_passed',actor_max_parameter_change=delta,prediction_reload_exact=True,elapsed_learning_and_reload_s=time.perf_counter()-begin,completed_batches=wrapper.completed_batches,history=wrapper.history,remaining_episode_step=episode.t,checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),training_ready=False,goal_complete=False)
    (args.out/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
finally:
    if env is not None:env.close()
    app.close()
