#!/usr/bin/env python3
"""Bounded recontact height diagnostic; no rendering, no object assistance."""
import argparse,json,sys,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
env=None
try:
 import numpy as np,torch
 from isaaclab.envs import ManagerBasedRLEnv
 from simfoundry.isaac_envs.registry import resolve_scene_env
 from simfoundry.robots.g1_assets import u1_sorting_default_qpos_np,G1_U1_23DOF_JOINT_NAMES,U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
 from simfoundry.data.search_episode import SearchEpisode,tensor
 from simfoundry.data.search_expert_interface import terminal_batch_audit
 from simfoundry.data.search_reward import terminal_search_scores
 from simfoundry.data.sorting_cartesian_expert import CartesianSweepState,cartesian_sweep_palm
 protocol=json.loads((ROOT/'demo/near_feedback_engaged_20260929_r1/PROTOCOL.json').read_text());args.out.mkdir(parents=True,exist_ok=False)
 cfg=resolve_scene_env('sorting_station_g1_23').env_cfg_cls();cfg.scene.num_envs=1;cfg.sim.device=args.device;cfg.episode_length_s=80.
 cfg.sim.physics.default.solver_cfg.use_mujoco_contacts=False;cfg.scene.d435i=None;cfg.scene.viewer_cam=None;cfg.observations.rgb=None
 default=u1_sorting_default_qpos_np(zero_upper_body=True);cfg.scene.robot.init_state.joint_pos=dict(zip(G1_U1_23DOF_JOINT_NAMES,default.tolist()))
 env=ManagerBasedRLEnv(cfg=cfg);rows=[];begin=time.perf_counter()
 for case in protocol['cases']:
  source=Path(case['source']);assert hashlib.sha256(source.read_bytes()).hexdigest()==case['sha256']
  with np.load(source) as src:first=src['action'][:480].copy()
  layout=json.loads(Path(case['layout']).read_text());task=0 if case['task']=='push_box_to_bin' else 1;side='right' if task==0 else 'left';obj='box' if task==0 else 'mailer'
  for lead in protocol['feedback_leads_m']:
   episode=SearchEpisode(env,[layout],[task]);qs=[];acts=[];traces={k:[] for k in ['box','mailer','palm_left','palm_right']};ori={k:[] for k in ['box','mailer']};controls=[];previous=default.copy();expert=None;engagement=None
   for t in range(640):
    q,tr=episode.snapshot()
    if t<480:target=first[t].copy()
    else:
     if t==480:
      xyz=tr[obj][0].cpu().numpy();expert=CartesianSweepState(side,float(xyz[0]),float(xyz[1]),exit_y=.30,contact_x_bias=0.,contact_palm_z=.845 if task==0 else .840,staging_palm_z=1.,contact_side_offset=-.04 if (-1 if task==0 else 1)*xyz[1]<-.03 else -.13,object_feedback_lead=0.)
     if lead and expert.mode=='sweep' and not expert.object_feedback_lead and (-1 if task==0 else 1)*(float(tr[obj][0,1])-expert.parcel_y)>=.02:
      expert.object_feedback_lead=lead;expert.feedback_target_y=float(tr['palm_'+side][0,1]);engagement=dict(step=t,object_y=float(tr[obj][0,1]),palm_y=expert.feedback_target_y,lead=lead)
     action=np.zeros(23,dtype=np.float32);cartesian_sweep_palm(episode.robot,episode.hands,action,state=expert,step=t-480,default_q=default,observed_parcel_y=float(tr[obj][0,1]) if lead else None)
     target=np.clip(default+action,previous-.055,previous+.055);target=np.clip(target,U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI).astype(np.float32);target[12]=0.
    assert np.isfinite(target).all() and np.abs(target-previous).max()<=.055001 and target[12]==0
    qs.append(q[0].cpu().numpy().copy());acts.append(target.copy())
    for k in traces:traces[k].append(tr[k][0].cpu().numpy().copy())
    for k,name in [('box','parcel_box'),('mailer','mailer')]:ori[k].append(tensor(env.scene[name].data.root_quat_w)[0].cpu().numpy().copy())
    controls.append(dict(step=t,mode=expert.mode if expert else 'frozen_first_pass',target_xyz=expert.last_target_xyz if expert else None))
    _,_,terminated,truncated,_=env.step(torch.as_tensor((target-default)[None],device=env.device));assert not bool(terminated.any() or truncated.any());previous=target.copy()
   q=np.asarray(qs);action=np.asarray(acts);traces={k:np.asarray(v) for k,v in traces.items()};ori={k:np.asarray(v) for k,v in ori.items()};assert np.array_equal(action[:480],first) and np.abs(q[0,12:]).max()<1e-4
   reports=terminal_batch_audit(np.array([task]),q[:,None],action[:,None],{k:v[:,None] for k,v in traces.items()});_,fitness=terminal_search_scores(reports,[task],{k:v[:,None] for k,v in traces.items()},{k:v[:,None] for k,v in ori.items()})
   folder=args.out/f"case_{case['layout_id']}_lead_{round(lead*1000):02d}mm";folder.mkdir();path=folder/'trajectory.npz';np.savez_compressed(path,q=q,action=action,**traces,**{k+'_quat':v for k,v in ori.items()})
   row=dict(case=case,engagement=engagement,lead_m=lead,report=reports[0],fitness=fitness[0],second_progress_m=float((-1 if task==0 else 1)*(traces[obj][-1,1]-traces[obj][480,1])),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),training_ready=False)
   (folder/'report.json').write_text(json.dumps(row,indent=2));(folder/'control.json').write_text(json.dumps(controls));rows.append(row);(args.out/'RESULT.json').write_text(json.dumps(dict(rows=rows,elapsed_s=time.perf_counter()-begin,complete=False,training_ready=False),indent=2));print('CASE',case['layout_id'],lead,reports[0]['passed'],row['second_progress_m'],reports[0]['reasons'],flush=True)
 (args.out/'RESULT.json').write_text(json.dumps(dict(rows=rows,elapsed_s=time.perf_counter()-begin,complete=True,training_ready=False,goal_complete=False),indent=2))
except BaseException as exc:
 import traceback
 detail=traceback.format_exc();print(detail,flush=True)
 if args.out.exists():(args.out/'ERROR.json').write_text(json.dumps(dict(error=repr(exc),traceback=detail)))
 raise
finally:
 if env is not None:env.close()
 app.close()
