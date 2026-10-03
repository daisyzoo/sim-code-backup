"""Exact linear-system attribution on archived unconstrained parent IK states.
Separates active XY, active Z, inactive XYZ, hand attitude and regularization
prior contributions to the original one-step joint target. Only applies when
the unconstrained solution reproduces the actual emitted command, with no
terminal/geometry override or active bound. This is algebra, not attribution of
physical contact dynamics, and does not simulate any alternative trajectory.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;C=W/'front_initial_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stats(v):
 a=np.asarray(v,float);assert a.size and np.isfinite(a).all();return dict(min=float(a.min()),median=float(np.median(a)),mean=float(a.mean()),max=float(a.max()))
def one(ep):
 f=json.loads((ep/'frontal_bypass.json').read_text());coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};track=json.loads((ep/'FRONT_LOADED_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json').read_text());numeric=json.loads((ep/'FRONT_INITIAL_STAGE_NUMERIC_REVIEW.json').read_text())
 for p,h in track['source_sha256'].items():assert sha(p)==h,p
 by_step={r['step']:r for r in track['rows']}
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 side='right' if f['plan']['direction']==-1 else 'left';ix=[3,4,5] if side=='right' else [0,1,2];inactive=[0,1,2] if side=='right' else [3,4,5];rows=[];excluded=[]
 for r in f['rows']:
  if r['mode']!='top_push':continue
  t=r['step'];c=coords[t];a=c['task_inputs'];assert a is not None
  if c['self_clearance_task']['override'] or c.get('terminal_joint_hold') or any(isinstance(v,dict) and (v.get('override') is True or v.get('changed') is True) for k,v in c.items() if k not in ['task_inputs','self_clearance_task']):excluded.append(dict(step=t,reason='actual_override_or_terminal'));continue
  J=np.asarray(a['jacobian']);e=np.asarray(a['error']);damp=np.asarray(a['damping']);prior=np.asarray(a['preferred_step']);np.testing.assert_allclose(a['current'],q[t],atol=1e-7,rtol=0)
  H=J.T@J+np.diag(damp*damp);parts={}
  for name,ids in [('active_xy',ix[:2]),('active_z',[ix[2]]),('inactive_xyz',inactive),('attitude',list(range(6,len(e))))]:parts[name]=np.linalg.solve(H,J[ids].T@e[ids])
  parts['regularization_prior']=np.linalg.solve(H,damp*damp*prior)
  delta=sum(parts.values());command=q[t]+delta;low=np.maximum.reduce([a['lower'],q[t]-a['step_limits'],np.asarray(a['previous'])-.055]);high=np.minimum.reduce([a['upper'],q[t]+a['step_limits'],np.asarray(a['previous'])+.055])
  if np.any(command<low-2e-7) or np.any(command>high+2e-7):excluded.append(dict(step=t,reason='bound_affects_unconstrained_solution'));continue
  mismatch=float(np.max(abs(command-u[t])));assert mismatch<1e-6,(ep.name,t,mismatch)
  np.testing.assert_allclose(J[ix]@(u[t]-q[t])*1000,by_step[t]['linearized_task_position_step_mm'],atol=1e-8,rtol=0)
  pred=J@delta;decomp={name:(J[ix]@p*1000).tolist() for name,p in parts.items()};np.testing.assert_allclose(sum(np.asarray(v) for v in decomp.values()),pred[ix]*1000,atol=1e-10,rtol=0)
  rows.append(dict(step=t,bout=by_step[t]['bout'],parent_command_match_max_rad=mismatch,requested_active_xyz_mm=(e[ix]*1000).tolist(),achieved_linear_active_xyz_mm=(pred[ix]*1000).tolist(),contributions_active_xyz_mm=decomp,observed_previous24_load_mean_N=by_step[t]['previous_action24_load']['mean'],actual_next_reference_xyz_mm=by_step[t]['next_observed_delta_frozen_reference_mm'],observed_object_xyz=by_step[t]['object_xyz'],bias_at_min=abs(by_step[t]['bias_m']+.006)<1e-10))
 def summarize(rs):
  if not rs:return None
  return dict(rows=len(rs),requested_z_mm=stats([r['requested_active_xyz_mm'][2] for r in rs]),linearized_z_mm=stats([r['achieved_linear_active_xyz_mm'][2] for r in rs]),z_contributions_mm={name:stats([r['contributions_active_xyz_mm'][name][2] for r in rs]) for name in parts},active_xy_adds_upward_z_frames=sum(r['contributions_active_xyz_mm']['active_xy'][2]>0 for r in rs),load24_mean_N=stats([r['observed_previous24_load_mean_N'] for r in rs]),bias_at_min_frames=sum(r['bias_at_min'] for r in rs))
 bouts=[dict(bout=b,summary=summarize([r for r in rows if r['bout']==b])) for b in sorted({r['bout'] for r in rows})]
 return dict(episode=ep.name,original_task_and_pose_passed=numeric['original_task_and_pose_passed'],original_progress_mm=numeric['progress_mm'],total_push_rows=len(by_step),excluded=excluded,summary=summarize(rows),bouts=bouts,rows=rows,source_sha256={str(ep/n):sha(ep/n) for n in ['raw.npz','frontal_bypass.json','coordination.json','FRONT_LOADED_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json','FRONT_INITIAL_STAGE_NUMERIC_REVIEW.json']})
rows=[one(p.parent) for p in sorted(C.glob('case_*/layout_*/FRONT_LOADED_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json'))];assert len(rows)==8
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,conditions=8,episodes=rows,script_sha256=sha(__file__),controller_changed=False,physical_alternative_tested=False,training_ready=False)
out=W/'FRONT_LOADED_TASK_COUPLING_FULL8_DIAGNOSTIC.json'
with out.open('x') as f:json.dump(report,f,indent=2)
for r in rows:
 print(json.dumps(dict(episode=r['episode'],passed=r['original_task_and_pose_passed'],eligible=r['summary']['rows'],excluded=len(r['excluded']),first=r['bouts'][0],last=r['bouts'][-1]),indent=2))
