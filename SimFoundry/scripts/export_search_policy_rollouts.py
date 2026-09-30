#!/usr/bin/env python3
"""Infrastructure-only vector physics probe; no learning, admission or assistance."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--num-envs',type=int,default=32)
p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--config',type=Path,required=True);
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
from simfoundry.data.search_reward import terminal_search_scores
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS
env=None
try:
    args.out.mkdir(parents=True,exist_ok=False);assert shutil.disk_usage(args.out).free>20.1*2**30
    cfg=resolve_scene_env('sorting_station_g1_23').env_cfg_cls();cfg.scene.num_envs=args.num_envs;cfg.sim.device=args.device;cfg.episode_length_s=40.
    cfg.sim.physics.default.solver_cfg.use_mujoco_contacts=False;cfg.scene.d435i=None;cfg.scene.viewer_cam=None;cfg.observations.rgb=None
    default=u1_sorting_default_qpos_np(zero_upper_body=True);cfg.scene.robot.init_state.joint_pos=dict(zip(G1_U1_23DOF_JOINT_NAMES,default.tolist()))
    env=ManagerBasedRLEnv(cfg=cfg);layouts=[];tasks=[]
    for i in range(args.num_envs):
        lid=66008+(i//2)%4;path=ROOT/f'demo/natural_coverage24_20260929_r1/case_{lid}/explicit_layout.json'
        layouts.append(json.loads(path.read_text()));tasks.append(i%2)
    episode=SearchEpisode(env,layouts,tasks);wrapper=SearchVecEnv(episode)
    runner=OnPolicyRunner(wrapper,json.loads(args.config.read_text()),log_dir=None,device=args.device)
    runner.load(str(args.checkpoint));policy=runner.get_inference_policy()
    obs_rows=[];raw_rows=[]
    for t in range(160):
        obs=wrapper.get_observations()
        with torch.no_grad():raw=policy(obs)
        obs_rows.append(obs['policy'].clone());raw_rows.append(raw.clone())
        _,reports=episode.step(raw)
        assert (reports is not None)==(t==159)
    trace={k:torch.stack(v).cpu().numpy() for k,v in episode.traces.items()};orientation={k:torch.stack(v).cpu().numpy() for k,v in episode.orientations.items()}
    scores,fitness=terminal_search_scores(reports,np.asarray(tasks),trace,orientation)
    q=torch.stack(episode.qs).cpu().numpy();action=torch.stack(episode.actions).cpu().numpy();raw=np.stack([x.cpu().numpy() for x in raw_rows]);observations=np.stack([x.cpu().numpy() for x in obs_rows]);rows=[]
    checkpoint_sha=hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()
    for i in range(args.num_envs):
        assert np.abs(q[0,i,12:]).max()<1e-4 and np.abs(action[0,i,12:]).max()<1e-4 and np.all(action[:,i,12]==0)
        folder=args.out/f'env_{i:02d}';folder.mkdir();path=folder/'trajectory.npz'
        np.savez_compressed(path,q=q[:,i],action=action[:,i],raw_actor_action=raw[:,i],privileged_observation=observations[:,i],**{k:v[:,i] for k,v in trace.items()},**{k+'_quat':v[:,i] for k,v in orientation.items()})
        task=('push_box_to_bin','nudge_mailer_to_bin')[tasks[i]]
        meta=dict(env_id=i,layout=layouts[i],task_id=task,prompt=PAIRED_SORTING_PROMPTS[task],report=reports[i],fitness=fitness[i],checkpoint_sha256=checkpoint_sha,trajectory_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),assist_frames=0,training_ready=False,visual_review='pending',scope='Deterministic privileged expert evaluation on training layouts; not independent VLA evaluation or training admission.')
        (folder/'meta.json').write_text(json.dumps(meta,indent=2));rows.append(meta)
    (args.out/'RESULT.json').write_text(json.dumps(dict(rows=rows,success=sum(x['search_success'] for x in fitness),numeric_passed=sum(x['passed'] for x in reports),training_ready=False,goal_complete=False),indent=2));print('EVALUATION',sum(x['search_success'] for x in fitness),'/',args.num_envs,flush=True)
finally:
    if env is not None:env.close()
    app.close()
