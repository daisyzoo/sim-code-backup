"""One-step recorded-Jacobian screen: does fixed inactive anchor limit rear pushing?
Not a controller, no command is sent, no contact or clearance guarantee.
"""
from pathlib import Path
import importlib.util,json,hashlib,sys
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w));sys.path.insert(0,str(w.parents[1]))
from audit_rear_coupled_execution_live import inspect,replay_record
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ep=Path(sys.argv[1]).resolve();report=inspect(ep);assert report['passed'] and report['complete_push_coverage'] and report['selected']
p=ep.parent/'provenance.json';prov=json.loads(p.read_text());name='simfoundry/data/bounded_ik.py';src=ep.parent/'source_snapshot'/name;assert sha(src)==prov['source_sha256'][name]
spec=importlib.util.spec_from_file_location('archived_anchor_solver',src);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(np.float32);u=z['action'][:,12:23].astype(np.float32)
cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];es={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};side='right' if 'push_box' in ep.name else 'left';ai=list(range(3,6)) if side=='right' else list(range(3));ii=list(range(3)) if side=='right' else list(range(3,6))
lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;penalty=np.full(11,np.float32(.045**2),dtype=np.float32);penalty[0]=np.float32(.12**2)
rows=[]
for f in fr:
 if f['mode']!='top_push':continue
 t=f['step'];c=cs[t];replay_record(c,f,es[t],q[t],u[t-1],u[t],side,m.bounded_damped_step)
 jac=np.vstack([np.asarray(c['control_jacobian_world'],dtype=np.float32),np.asarray(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]);errors=[]
 for hand in ['left','right']:
  target=f['target_xyz'] if hand==side else c['inactive_anchor'];point=np.asarray(c['control_point_positions'][hand],dtype=np.float32);errors.extend(np.clip(np.float32(.72)*(np.asarray(target,dtype=np.float32)-point),np.float32(-.035),np.float32(.035)).tolist())
 err=np.r_[np.asarray(errors,dtype=np.float32),np.asarray(c['contact_normal_tracking']['error'],dtype=np.float32)];variants=[]
 for weight in [1.,.25,0.]:
  weights=np.ones(9,dtype=np.float32);weights[ii]=weight;dq=m.bounded_damped_step(jac*weights[:,None],err*weights,q[t],lo,hi,limits,np.sqrt(penalty),preferred_step=np.zeros(11,dtype=np.float32));target=q[t]+dq;target[0]=np.clip(target[0],-.98,.98);cmd=np.clip(np.clip(target.astype(np.float32),u[t-1]-np.float32(.055),u[t-1]+np.float32(.055)),np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32)
  if weight==1.:assert np.array_equal(cmd,u[t])
  actual_delta=cmd-q[t];residual=jac@actual_delta-err
  variants.append(dict(inactive_row_weight=weight,active_residual_xyz_mm=(residual[ai]*1000).tolist(),active_residual_norm_mm=float(np.linalg.norm(residual[ai])*1000),normal_residual_norm=float(np.linalg.norm(residual[6:])),inactive_anchor_residual_mm=float(np.linalg.norm(residual[ii])*1000),inactive_linear_motion_mm=float(np.linalg.norm(jac[ii]@actual_delta)*1000),waist_command_rad=float(cmd[0]),max_command_difference_rad=float(np.max(abs(cmd-u[t]))),command=cmd.tolist()))
 rows.append(dict(step=t,loaded=f['contact_load']['observed_vertical_load_n']>=.2,variants=variants))
summary=[];loaded=[r for r in rows if r['loaded']]
for j,weight in enumerate([1.,.25,0.]):
 vals=[r['variants'][j] for r in loaded];base=[r['variants'][0] for r in loaded];improve=np.array([b['active_residual_norm_mm']-a['active_residual_norm_mm'] for a,b in zip(vals,base)])
 summary.append(dict(weight=weight,loaded_frames=len(vals),median_active_residual_mm=float(np.median([a['active_residual_norm_mm'] for a in vals])),median_improvement_mm=float(np.median(improve)),max_improvement_mm=float(max(improve)),frames_improved_over_0_1mm=int(sum(improve>.1)),frames_worsened_over_0_1mm=int(sum(improve<-.1)),max_inactive_linear_motion_mm=max(a['inactive_linear_motion_mm'] for a in vals),max_inactive_anchor_residual_mm=max(a['inactive_anchor_residual_mm'] for a in vals),normal_residual_worse_over_1e_4_frames=sum(a['normal_residual_norm']>b['normal_residual_norm']+1e-4 for a,b in zip(vals,base)),waist_bound_frames=sum(abs(a['waist_command_rad'])>=.9799 for a in vals)))
out=dict(episode=ep.name,baseline_replay_exact=True,full_push_frames=len(rows),summary=summary,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json','expert_control.json']},solver_sha256=sha(src),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Recorded one-step linear Jacobian tradeoff only. Original damping/joint/step/final slew limits; baseline exactly replayed. Weight0 permits inactive world motion, does not assert whole-arm collision clearance, FK accuracy, sustained tracking, contact or task success; no physics change.')
(ep/'INACTIVE_ANCHOR_TRADEOFF.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['rows','source_sha256']},indent=2))
