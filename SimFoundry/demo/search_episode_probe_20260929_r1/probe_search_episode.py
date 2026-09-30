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
env=None
try:
    args.out.mkdir(parents=True,exist_ok=False)
    cfg=resolve_scene_env('sorting_station_g1_23').env_cfg_cls();cfg.scene.num_envs=args.num_envs;cfg.sim.device=args.device;cfg.episode_length_s=40.
    cfg.sim.physics.default.solver_cfg.use_mujoco_contacts=False;cfg.scene.d435i=None;cfg.scene.viewer_cam=None;cfg.observations.rgb=None
    default=u1_sorting_default_qpos_np(zero_upper_body=True);cfg.scene.robot.init_state.joint_pos=dict(zip(G1_U1_23DOF_JOINT_NAMES,default.tolist()))
    env=ManagerBasedRLEnv(cfg=cfg);layouts=[];tasks=[];paths=[];expected=[];saved_actions=[]
    for i in range(args.num_envs):
        lid=66008+(i//2)%4;task=('push_box_to_bin','nudge_mailer_to_bin')[i%2]
        base=ROOT/f'demo/natural_coverage24_20260929_r1/case_{lid}'
        layouts.append(json.loads((base/'explicit_layout.json').read_text()));tasks.append(i%2);p=base/f'layout_{lid}_{task}'
        paths.append(str(p));expected.append(json.loads((p/'quality.json').read_text()))
        with np.load(p/'raw.npz') as z:saved_actions.append(z['action'])
    episode=SearchEpisode(env,layouts,tasks);result=[]
    for mode in ['zero','historical_replay']:
        episode.reset();begin=time.perf_counter();palm_error=0.
        for t in range(160):
            if t in [0,80,159]:
                _,tr=episode.snapshot()
                for side,idx in episode.hands.items():
                    for j in [0,args.num_envs-1]:
                        scalar=torch.tensor(palm_xyz(episode.robot,idx,j),device=env.device)-env.scene.env_origins[j]
                        palm_error=max(palm_error,float((tr['palm_'+side][j]-scalar).abs().max()))
            if mode=='zero':obs,reports=episode.step(torch.zeros((args.num_envs,5),device=env.device))
            else:obs,reports=episode.step_absolute(torch.tensor(np.stack([x[t] for x in saved_actions]),device=env.device))
            assert (reports is not None)==(t==159)
        assert palm_error<1e-5
        q=torch.stack(episode.qs).cpu().numpy();action=torch.stack(episode.actions).cpu().numpy();trace={k:torch.stack(v).cpu().numpy() for k,v in episode.traces.items()}
        assert np.max(np.abs(q[0,:,12:]))<1e-4 and np.max(np.abs(action[0,:,12:]))<1e-4 and np.all(action[:,:,12]==0)
        if mode=='historical_replay':assert np.array_equal(action,np.stack(saved_actions,axis=1))
        np.savez_compressed(args.out/(mode+'.npz'),q=q,action=action,**trace)
        row=dict(mode=mode,seconds=time.perf_counter()-begin,palm_scalar_max_error=palm_error,reports=reports,passed=sum(x['passed'] for x in reports),baseline_passed=sum(x['passed'] for x in expected),baseline_paths=paths)
        result.append(row);(args.out/'RESULT.json').write_text(json.dumps(dict(rows=result,training_ready=False,goal_complete=False,scope='Camera-free vector infrastructure/replay. Replay actions exact; physical outcomes need comparison. No training admission or visual review.'),indent=2));print(mode,row['passed'],'baseline',row['baseline_passed'],'seconds',row['seconds'],flush=True)
finally:
    if env is not None:env.close()
    app.close()
