"""Recorded-state causal question: does current waist command bound restrict IK?
Hypothetical1.08 command bound is an offline one-step diagnostic, not approved
working range, full-arm safety, physics rollout, or change to runtime constraints.
"""
from pathlib import Path
import json,hashlib,sys,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_rear_coupled_execution_live import inspect,replay_record
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ep=Path(sys.argv[1]).resolve();audit=inspect(ep);assert audit['passed'] and audit['selected'] and audit['complete_push_coverage'];prov=json.loads((ep.parent/'provenance.json').read_text());name='simfoundry/data/bounded_ik.py';src=ep.parent/'source_snapshot'/name;assert sha(src)==prov['source_sha256'][name];spec=importlib.util.spec_from_file_location('waist_bound_solver',src);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(np.float32);u=z['action'][:,12:23].astype(np.float32)
cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};es={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];side='right' if 'push_box' in ep.name else 'left';ai=list(range(3,6)) if side=='right' else list(range(3));ii=list(range(3)) if side=='right' else list(range(3,6));hardlo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hardhi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();assert hardlo[0]<-1.08 and hardhi[0]>1.08;limits=np.full(11,.04);limits[0]=.015;penalty=np.full(11,np.float32(.045**2),dtype=np.float32);penalty[0]=np.float32(.12**2);rows=[]
for f in fr:
 if f['mode']!='top_push':continue
 t=f['step'];c=cs[t];replay_record(c,f,es[t],q[t],u[t-1],u[t],side,m.bounded_damped_step);jac=np.vstack([np.asarray(c['control_jacobian_world'],dtype=np.float32),np.asarray(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]);errors=[]
 for hand in ['left','right']:
  target=f['target_xyz'] if hand==side else c['inactive_anchor'];point=np.asarray(c['control_point_positions'][hand],dtype=np.float32);errors.extend(np.clip(np.float32(.72)*(np.asarray(target,dtype=np.float32)-point),np.float32(-.035),np.float32(.035)).tolist())
 err=np.r_[np.asarray(errors,dtype=np.float32),np.asarray(c['contact_normal_tracking']['error'],dtype=np.float32)];variants=[]
 for bound in [.98,1.08]:
  lo=hardlo.copy();hi=hardhi.copy();lo[0]=-bound;hi[0]=bound;dq=m.bounded_damped_step(jac,err,q[t],lo,hi,limits,np.sqrt(penalty),preferred_step=np.zeros(11,dtype=np.float32));target=q[t]+dq;target[0]=np.clip(target[0],-bound,bound);cmd=np.clip(np.clip(target.astype(np.float32),u[t-1]-np.float32(.055),u[t-1]+np.float32(.055)),hardlo,hardhi).astype(np.float32)
  if bound==.98:assert np.array_equal(cmd,u[t])
  move=jac@(cmd-q[t]);res=move-err
  variants.append(dict(waist_command_bound=bound,waist_command_rad=float(cmd[0]),active_step_residual_xyz_mm=(res[ai]*1000).tolist(),active_step_residual_norm_mm=float(np.linalg.norm(res[ai])*1000),normal_residual_norm=float(np.linalg.norm(res[6:])),inactive_residual_mm=float(np.linalg.norm(res[ii])*1000),max_command_difference_rad=float(np.max(abs(cmd-u[t]))),arm_limit_indices=[i for i in range(1,11) if min(cmd[i]-hardlo[i],hardhi[i]-cmd[i])<1e-4],command=cmd.tolist()))
 rows.append(dict(step=t,loaded=f['contact_load']['observed_vertical_load_n']>=.2,variants=variants))
summary=[];loaded=[r for r in rows if r['loaded']]
for j in range(2):
 vals=[r['variants'][j] for r in loaded];base=[r['variants'][0] for r in loaded];gain=[b['active_step_residual_norm_mm']-v['active_step_residual_norm_mm'] for v,b in zip(vals,base)];summary.append(dict(bound=vals[0]['waist_command_bound'],loaded_frames=len(vals),median_active_residual_mm=float(np.median([v['active_step_residual_norm_mm'] for v in vals])),median_improvement_mm=float(np.median(gain)),max_improvement_mm=max(gain),improved_over_0_5mm=sum(x>.5 for x in gain),worsened_over_0_1mm=sum(x<-.1 for x in gain),median_abs_X_residual_mm=float(np.median([abs(v['active_step_residual_xyz_mm'][0]) for v in vals])),max_abs_waist_command_rad=max(abs(v['waist_command_rad']) for v in vals),commands_beyond_previous_0_98=sum(abs(v['waist_command_rad'])>.980001 for v in vals),commands_beyond_previous_physical_1_0=sum(abs(v['waist_command_rad'])>1. for v in vals),normal_residual_worse_over_1e_4=sum(v['normal_residual_norm']>b['normal_residual_norm']+1e-4 for v,b in zip(vals,base)),inactive_residual_worse_over_0_1mm=sum(v['inactive_residual_mm']>b['inactive_residual_mm']+.1 for v,b in zip(vals,base))))
out=dict(episode=ep.name,run=ep.parent.parent.name,baseline_replay_exact=True,push_frames=len(rows),urdf_waist_limits=[float(hardlo[0]),float(hardhi[0])],summary=summary,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json','expert_control.json']},archived_solver_sha256=sha(src),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Hypothetical one-step waist command-bound expansion .98→1.08 on same recorded state/goal/J/damping/normal/inactive/arm limits/.015waist/.04arm step and final.055slew. Exact baseline replay. No recursive state, nonlinear FK, full-arm collision or contact validation, no changed runtime/planning contract or physical evidence for expanded working range.')
(ep/'WAIST_BOUND_TRADEOFF.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['rows','source_sha256']},indent=2))
