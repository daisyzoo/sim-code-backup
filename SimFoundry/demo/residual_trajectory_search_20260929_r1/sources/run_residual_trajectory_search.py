#!/usr/bin/env python3
"""Infrastructure-only vector physics probe; no learning, admission or assistance."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--num-envs',type=int,default=128)
AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import torch
from isaaclab.envs import ManagerBasedRLEnv
from simfoundry.isaac_envs.registry import resolve_scene_env
from simfoundry.robots.g1_assets import u1_sorting_default_qpos_np,G1_U1_23DOF_JOINT_NAMES
from isaaclab_newton.physics.newton_manager import NewtonManager

import numpy as np
from simfoundry.data.search_episode import SearchEpisode
from simfoundry.data.sorting_quality import palm_xyz
import hashlib,shutil
from simfoundry.data.residual_trajectory import residual_actions
from simfoundry.data.search_reward import terminal_search_scores
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
env=None
try:
    args.out.mkdir(parents=True,exist_ok=False)
    protocol_path=ROOT/'demo/residual_trajectory_search_20260929_r1/PROTOCOL.json';protocol=json.loads(protocol_path.read_text());sources=protocol['sources'];population=protocol['population'];assert args.num_envs==population*8
    (args.out/'PROTOCOL.json').write_bytes(protocol_path.read_bytes());templates=[];layouts=[];tasks=[]
    for row in sources:
        path=Path(row['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        with np.load(path) as z:templates.append(z['action'])
        layouts.append(row['layout']);tasks.append(0 if row['task']=='push_box_to_bin' else 1)
    template=np.stack(templates,axis=1);expected=np.array([x['baseline_passed'] for x in sources]);rng=np.random.default_rng(protocol['seed'])
    cfg=resolve_scene_env('sorting_station_g1_23').env_cfg_cls();cfg.scene.num_envs=args.num_envs;cfg.sim.device=args.device;cfg.episode_length_s=40.
    cfg.sim.physics.default.solver_cfg.use_mujoco_contacts=False;cfg.scene.d435i=None;cfg.scene.viewer_cam=None;cfg.observations.rgb=None
    default=u1_sorting_default_qpos_np(zero_upper_body=True);cfg.scene.robot.init_state.joint_pos=dict(zip(G1_U1_23DOF_JOINT_NAMES,default.tolist()))
    env=ManagerBasedRLEnv(cfg=cfg);episode=SearchEpisode(env,layouts*population,tasks*population)
    def evaluate(parameters):
        actions=np.concatenate([residual_actions(template,tasks,x,U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI) for x in parameters],axis=1)
        episode.reset()
        for t in range(160):_,reports=episode.step_absolute(torch.as_tensor(actions[t],device=env.device))
        trace={k:torch.stack(v).cpu().numpy() for k,v in episode.traces.items()};ori={k:torch.stack(v).cpu().numpy() for k,v in episode.orientations.items()}
        _,fitness=terminal_search_scores(reports,np.array(tasks*population),trace,ori);rankings=[]
        for j in range(population):
            rs=reports[j*8:(j+1)*8];fs=fitness[j*8:(j+1)*8];passed=np.array([x['passed'] for x in rs]);success=[x['search_success'] for x in fs]
            preserved=bool(np.all(passed[expected]));groups=int(all(success[:4]))+int(all(success[4:]));count=sum(success);soft=0.
            for k,(report,fit) in enumerate(zip(rs,fs)):
                m=report['metrics'];obj='box' if tasks[k]==0 else 'mailer';other='mailer' if obj=='box' else 'box';direction=-1 if obj=='box' else 1
                soft+=float(np.clip(m['target_final_progress_m']/.15,-1,1)+np.clip(direction*trace[obj][-1,j*8+k,1]/.20,-1,1)-20*m[other+'_max_xy_m']-.1*(m['left_table_pen_frames']+m['right_table_pen_frames'])-3*max(fit['max_tilt_rad'].values()))
            rankings.append((int(preserved),groups,count,soft))
        return actions,reports,fitness,trace,ori,rankings
    begin=time.perf_counter();zero=np.zeros((population,4,5));actions,reports,fitness,trace,ori,ranks=evaluate(zero)
    assert np.array_equal(actions,np.tile(template,(1,population,1)))
    assert np.array_equal(np.array([x['passed'] for x in reports]).reshape(population,8),np.tile(expected,(population,1)))
    (args.out/'BASELINE.json').write_text(json.dumps(dict(passed=sum(x['passed'] for x in reports),expected_passed=int(expected.sum())*population,all128_statuses_match=True,actions_exact=True,ranks=ranks,seconds=time.perf_counter()-begin,training_ready=False),indent=2));print('BASELINE_VERIFIED',sum(x['passed'] for x in reports),'/',args.num_envs,flush=True)
    mean=np.zeros((4,5));std=np.full((4,5),.08);best_params=np.zeros((4,5));best_rank=max(ranks);history=[]
    for generation in range(protocol['max_generations']):
        assert shutil.disk_usage(args.out).free>20.15*2**30
        parameters=np.clip(rng.normal(mean,std,(population,4,5)),-.25,.25);parameters[0]=0;parameters[1]=best_params
        actions,reports,fitness,trace,ori,ranks=evaluate(parameters)
        order=sorted(range(population),key=lambda i:ranks[i],reverse=True);winner=order[0];rank=ranks[winner]
        record=dict(generation=generation,ranks=ranks,winner=winner,winner_parameters=parameters[winner].tolist(),elapsed_s=time.perf_counter()-begin);history.append(record)
        if rank>best_rank:
            best_rank=rank;best_params=parameters[winner].copy();folder=args.out/f'best_gen_{generation:02d}';folder.mkdir()
            for k in range(8):
                i=winner*8+k;path=folder/f'case_{k}.npz'
                np.savez_compressed(path,q=torch.stack(episode.qs)[:,i].cpu().numpy(),action=actions[:,i],**{key:v[:,i] for key,v in trace.items()},**{key+'_quat':v[:,i] for key,v in ori.items()})
                path.with_suffix('.json').write_text(json.dumps(dict(source=sources[k],report=reports[i],fitness=fitness[i],rank=rank,parameters=best_params.tolist(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),training_ready=False,visual_review='pending'),indent=2))
        elite=parameters[order[:4]];mean=.5*mean+.5*elite.mean(axis=0);std=np.clip(.5*std+.5*elite.std(axis=0),.02,.15)
        (args.out/'HISTORY.json').write_text(json.dumps(history,indent=2));print('GEN',generation,'best',best_rank,'current',rank,flush=True)
    (args.out/'RESULT.json').write_text(json.dumps(dict(status='bounded_residual_search_complete_pending_review',best_rank=best_rank,best_parameters=best_params.tolist(),generations=len(history),transitions=(len(history)+1)*160*args.num_envs,elapsed_s=time.perf_counter()-begin,training_ready=False,goal_complete=False),indent=2))
finally:
    if env is not None:env.close()
    app.close()
