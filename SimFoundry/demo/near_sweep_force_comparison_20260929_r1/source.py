#!/usr/bin/env python3
"""Read-only solved-force observation during exact frozen action replays."""
import argparse,json,sys,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app;env=None
try:
 import numpy as np,torch
 from isaaclab.envs import ManagerBasedRLEnv
 from simfoundry.isaac_envs.registry import resolve_scene_env
 from simfoundry.robots.g1_assets import u1_sorting_default_qpos_np,G1_U1_23DOF_JOINT_NAMES,U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
 from simfoundry.data.search_episode import SearchEpisode,tensor
 from simfoundry.data.search_expert_interface import terminal_batch_audit
 from simfoundry.data.search_reward import terminal_search_scores
 from simfoundry.data.solved_contact_trace import read_solved_contact_forces
 root=args.root.resolve();protocol=json.loads((root/'PROTOCOL.json').read_text());out=root/'run';out.mkdir(exist_ok=False)
 cfg=resolve_scene_env('sorting_station_g1_23').env_cfg_cls();cfg.scene.num_envs=1;cfg.sim.device=args.device;cfg.episode_length_s=80.;cfg.sim.physics.default.solver_cfg.use_mujoco_contacts=False;cfg.scene.d435i=None;cfg.scene.viewer_cam=None;cfg.observations.rgb=None
 default=u1_sorting_default_qpos_np(zero_upper_body=True);cfg.scene.robot.init_state.joint_pos=dict(zip(G1_U1_23DOF_JOINT_NAMES,default.tolist()));env=ManagerBasedRLEnv(cfg=cfg);rows=[]
 for c in protocol['cases']:
  path=Path(c['source']);assert hashlib.sha256(path.read_bytes()).hexdigest()==c['sha256']
  with np.load(path) as source:actions=source['action'].copy()
  assert actions.shape==(640,23) and np.isfinite(actions).all() and np.abs(actions[0,12:]).max()<1e-4 and np.all(actions[:,12]==0) and np.abs(np.diff(actions,axis=0)).max()<=.055001
  assert np.all(actions>=np.asarray(U1_JOINT_LIMIT_LO)-1e-6) and np.all(actions<=np.asarray(U1_JOINT_LIMIT_HI)+1e-6)
  layout=json.loads(Path(c['layout']).read_text());task=0 if c['task']=='push_box_to_bin' else 1;e=SearchEpisode(env,[layout],[task]);qs=[];traces={k:[] for k in ['box','mailer','palm_left','palm_right']};ori={k:[] for k in ['box','mailer']};forces=[]
  for t,target in enumerate(actions):
   q,tr=e.snapshot();qs.append(q[0].cpu().numpy().copy())
   for key in traces:traces[key].append(tr[key][0].cpu().numpy().copy())
   for key,name in [('box','parcel_box'),('mailer','mailer')]:ori[key].append(tensor(env.scene[name].data.root_quat_w)[0].cpu().numpy().copy())
   _,_,terminated,truncated,_=env.step(torch.as_tensor((target-default)[None],device=env.device));assert not bool(terminated.any() or truncated.any())
   if protocol['force_start']<=t<=protocol['force_end']:
    force=read_solved_contact_forces(t);_,post=e.snapshot();force['post_action_object_xyz']={key:post[key][0].cpu().numpy().tolist() for key in ['box','mailer']};forces.append(force)
  q=np.asarray(qs);traces={k:np.asarray(v) for k,v in traces.items()};ori={k:np.asarray(v) for k,v in ori.items()};assert np.abs(q[0,12:]).max()<1e-4
  reports=terminal_batch_audit(np.array([task]),q[:,None],actions[:,None],{k:v[:,None] for k,v in traces.items()});_,fitness=terminal_search_scores(reports,[task],{k:v[:,None] for k,v in traces.items()},{k:v[:,None] for k,v in ori.items()})
  folder=out/c['name'];folder.mkdir();dest=folder/'trajectory.npz';np.savez_compressed(dest,q=q,action=actions,**traces,**{k+'_quat':v for k,v in ori.items()});(folder/'forces.json').write_text(json.dumps(dict(scope='Solved last-physics-tick forces only; no integrated impulse, no refresh, no changes to force buffer',rows=forces),indent=2))
  with np.load(path) as source:
   errors={key:float(np.abs(traces[key]-source[key]).max()) for key in traces};q_error=float(np.abs(q-source['q']).max())
  row=dict(case=c,report=reports[0],fitness=fitness[0],force_samples=len(forces),force_buffer_unchanged=all(x['solver_force_buffer_unchanged'] for x in forces),max_q_error=q_error,max_trace_errors=errors,raw_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),training_ready=False);rows.append(row);(folder/'report.json').write_text(json.dumps(row,indent=2));(out/'RESULT.json').write_text(json.dumps(dict(rows=rows,complete=False,training_ready=False),indent=2));print('COMPLETE',c['name'],reports[0]['passed'],flush=True)
 (out/'RESULT.json').write_text(json.dumps(dict(rows=rows,complete=True,training_ready=False,goal_complete=False),indent=2))
except BaseException as exc:
 import traceback
 detail=traceback.format_exc();print(detail,flush=True)
 if args.root.exists():(args.root/'ERROR.json').write_text(json.dumps(dict(error=repr(exc),traceback=detail)))
 raise
finally:
 if env is not None:env.close()
 app.close()
