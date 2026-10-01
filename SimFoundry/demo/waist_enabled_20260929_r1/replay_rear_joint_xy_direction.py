"""Archived one-step IK screen for two-axis geometry candidates; no rollout."""
from pathlib import Path
import json,hashlib,sys,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w));sys.path.insert(0,str(w.parents[1]))
from audit_rear_coupled_execution_live import inspect,replay_record
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=w/'REAR_JOINT_XY_DIRECTION_SCREEN.json';screen=json.loads(p.read_text());reports=[]
for case in screen['episodes']:
 if case['run']!='rear_coupled_progress_groups_r1':continue
 ep=w/case['run']/('case_'+case['episode'].split('_')[1])/case['episode'];audit=inspect(ep);assert audit['passed'] and audit['complete_push_coverage']
 for n,h in case['source_sha256'].items():assert sha(ep/n)==h
 prov=json.loads((ep.parent/'provenance.json').read_text());name='simfoundry/data/bounded_ik.py';src=ep.parent/'source_snapshot'/name;assert sha(src)==prov['source_sha256'][name];spec=importlib.util.spec_from_file_location('recorded_xy_solver',src);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fs={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};es={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};side='right' if 'push_box' in ep.name else 'left';ai=list(range(3,6)) if side=='right' else list(range(3));ii=list(range(3)) if side=='right' else list(range(3,6));direction=-1 if side=='right' else 1
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(np.float32);u=z['action'][:,12:23].astype(np.float32)
 lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;penalty=np.full(11,np.float32(.045**2),dtype=np.float32);penalty[0]=np.float32(.12**2);rows=[]
 for sample in case['rows']:
  if not sample['feasible']:continue
  t=sample['step'];c=cs[t];f=fs[t];replay_record(c,f,es[t],q[t],u[t-1],u[t],side,m.bounded_damped_step);jac=np.vstack([np.asarray(c['control_jacobian_world'],dtype=np.float32),np.asarray(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]);variants=[]
  for name,target in [('actual',f['target_xyz']),('joint_xy',sample['candidate_command_xyz'])]:
   errors=[]
   for hand in ['left','right']:
    goal=target if hand==side else c['inactive_anchor'];point=np.asarray(c['control_point_positions'][hand],dtype=np.float32);errors.extend(np.clip(np.float32(.72)*(np.asarray(goal,dtype=np.float32)-point),np.float32(-.035),np.float32(.035)).tolist())
   err=np.r_[np.asarray(errors,dtype=np.float32),np.asarray(c['contact_normal_tracking']['error'],dtype=np.float32)];dq=m.bounded_damped_step(jac,err,q[t],lo,hi,limits,np.sqrt(penalty),preferred_step=np.zeros(11,dtype=np.float32));assigned=q[t]+dq;assigned[0]=np.clip(assigned[0],-.98,.98);cmd=np.clip(np.clip(assigned.astype(np.float32),u[t-1]-np.float32(.055),u[t-1]+np.float32(.055)),np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32)
   if name=='actual':assert np.array_equal(cmd,u[t])
   movement=jac@(cmd-q[t]);residual=movement-err
   variants.append(dict(name=name,active_step_residual_xyz_mm=(residual[ai]*1000).tolist(),active_predicted_step_xyz_mm=(movement[ai]*1000).tolist(),active_goal_after_linear_step_xyz_mm=((np.asarray(target)-np.asarray(c['control_point_positions'][side])-movement[ai])*1000).tolist(),normal_residual_norm=float(np.linalg.norm(residual[6:])),inactive_residual_mm=float(np.linalg.norm(residual[ii])*1000),max_action_change_rad=float(np.max(abs(cmd-u[t]))),waist_command_rad=float(cmd[0]),command=cmd.tolist()))
  rows.append(dict(step=t,loaded=f['contact_load']['observed_vertical_load_n']>=.2,variants=variants))
 summaries=[]
 for j in range(2):
  rr=[r['variants'][j] for r in rows if r['loaded']];base=[r['variants'][0] for r in rows if r['loaded']];summaries.append(dict(name=rr[0]['name'],loaded_frames=len(rr),median_predicted_forward_point_step_mm=float(np.median([direction*r['active_predicted_step_xyz_mm'][1] for r in rr])),median_abs_step_x_residual_mm=float(np.median([abs(r['active_step_residual_xyz_mm'][0]) for r in rr])),median_abs_step_y_residual_mm=float(np.median([abs(r['active_step_residual_xyz_mm'][1]) for r in rr])),median_abs_goal_x_error_mm=float(np.median([abs(r['active_goal_after_linear_step_xyz_mm'][0]) for r in rr])),median_forward_step_gain_mm=float(np.median([direction*(r['active_predicted_step_xyz_mm'][1]-b['active_predicted_step_xyz_mm'][1]) for r,b in zip(rr,base)])),normal_residual_worse_over_1e_4_frames=sum(r['normal_residual_norm']>b['normal_residual_norm']+1e-4 for r,b in zip(rr,base)),inactive_residual_worse_over_0_1mm_frames=sum(r['inactive_residual_mm']>b['inactive_residual_mm']+.1 for r,b in zip(rr,base)),max_command_change_rad=max(r['max_action_change_rad'] for r in rr)))
 reports.append(dict(episode=ep.name,summary=summaries,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','expert_control.json','frontal_bypass.json']},archived_solver_sha256=sha(src)));print(ep.name,summaries)
out=dict(episodes=reports,screen_sha256=sha(p),checker_sha256=sha(Path(__file__)),baseline_replay_exact=True,training_ready=False,scope='Independent recorded-state one-step IK, original normal/inactive rows/damping/bounds/final slew. Baseline actual11D action exactly replayed. Predicted POINT displacement and linear errors, not object motion or COP, no nonlinear FK or safety validation, no recursive rollout or physics. Source screen only geometric reference constraints.')
p=w/'REAR_JOINT_XY_IK_SCREEN.json';assert not p.exists();p.write_text(json.dumps(out,indent=2))
