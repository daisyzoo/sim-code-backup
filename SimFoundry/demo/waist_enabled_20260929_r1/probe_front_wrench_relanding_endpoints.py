"""Static original-bounds endpoint check for causally screened recontact points.
Recorded loaded robot pose is only an optimization seed. No loaded-to-unloaded
path or control is executed. An endpoint cannot authorize withdrawal, transport,
COP placement, force, visibility, live handover or training admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
import numpy as np
from scipy.optimize import minimize,Bounds
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from articulated_hand_geometry import skew
from audit_minimum_motion_plan_reentrant import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();src=W/'FRONT_CAUSAL_WRENCH_RELANDING_SCREEN.json';inputs=json.loads(src.read_text());guard=ClearanceGuard(ROOT,S);independent=PlanAudit(ROOT,S);records=[];out=W/'FRONT_WRENCH_RELANDING_ENDPOINT_PROBE.json';assert not out.exists()
sources={str(p):sha(p) for p in [Path(__file__),src,S/'clearance_runtime.py',S/'recontact_scene.py',S/'articulated_hand_geometry.py',W/'audit_minimum_motion_plan_reentrant.py',W/'audit_recontact_interior_events.py',W/'audit_recontact_pose_events.py']};sources.update(guard.model.source_sha256)
def save(status,**kw):
 tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,simulation_started=False,collector_integrated=False,training_ready=False,**kw),indent=2));tmp.replace(out)
try:
 save('running')
 for item in inputs['episodes']:
  c=item['chosen_first_causal_inside_landing']
  if c is None:
   records.append(dict(episode=item['episode'],selected=False,reason='causal_screen_no_entry'));save('running');continue
  ep=W/item['episode'];t=c['step'];side=item['side'];key=item['target_key'];other='mailer' if key=='box' else 'box';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
  for p,h in item['source_sha256'].items():assert sha(p)==h
  with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:target=z[key][t];obstacle=z[other][t]
  with np.load(ep/'parcel_orientation.npz') as z:tq=z[key][t];oq=z[other][t]
  scene=RecontactScene(guard,side,target,tq,sizes[key],obstacle,oq,sizes[other]);core=scene.core;normal=scene.rotation[:,2];axis=np.linalg.eigh(np.cov(guard.model.vertices[side].T))[1][:,0];record=dict(episode=item['episode'],selected=True,step=t,actual_current_q=q.tolist(),observed_scene=scene.record(),original_task_passed=item['original_task_passed'],desired_contact_is_hypothetical=True,conditions=[]);records.append(record)
  for name,goal in [('past_weighted_COP',c['normal_weighted_cop_local_m'][:2]),('frozen_wrench_zero_moment_point',c['proposed_contact_local_xy_m'])]:
   goal=np.array(goal);attempts=[];condition=dict(name=name,desired_local_xy_m=goal.tolist(),attempts=attempts);record['conditions'].append(condition)
   def alignment(x):
    T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@axis;return float(normal@v),normal@(-skew(v)@jw)
   def cost(x):d=x-q;return float(d@d),2*d
   def cons(x):
    g=scene.details(x);p=g['point'];J=g['jacobian'];a,da=alignment(x);half=core[:2]/2-.012
    return np.r_[a*a-.8**2,half-p[:2],half+p[:2],.002-(p[:2]-goal),.002+(p[:2]-goal),p[2]-core[2]/2-.006,core[2]/2+.007-p[2],g['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([2*a*da,-J[:2],J[:2],-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
   seeds=[('actual_current',q)]+[(f'neutral_waist_{yaw}',np.r_[yaw,np.zeros(10)]) for yaw in [-.5,0.,.5]]
   for label,seed in seeds:
    save('running',current_episode=item['episode'],current_condition=name,current_seed=label)
    fit=minimize(cost,np.clip(seed,guard.lower,guard.upper),jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options=dict(maxiter=220,ftol=1e-12));x=np.asarray(fit.x);g,d=independent.geometry(x,scene.record());a=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis)
    minimum=float(min(a*a-.8**2,*list(core[:2]/2-.012-abs(d['point'][:2])),*list(.002-abs(d['point'][:2]-goal)),g['active_above_top_m']-.006,.007-g['active_above_top_m'],independent.hand.minz(x,scene.inactive)-.84,g['elbow_gap_m']-.005));assert abs(minimum-float(min(cons(x)[0])))<2e-7
    accepted=bool(fit.success and minimum>=-2e-7 and min(g['hand_parcel_gaps_m'].values())>=.01-2e-7 and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7));attempts.append(dict(seed=label,solver_status=int(fit.status),iterations=int(fit.nit),accepted=accepted,minimum_constraint_m=minimum,candidate_q=x.tolist(),independent_geometry=g,independent_contact_local_m=d['point'].tolist(),independent_alignment_abs=float(a),objective=float(fit.fun)))
   condition['accepted_endpoints']=sum(a['accepted'] for a in attempts);save('running');print(item['episode'],t,name,condition['accepted_endpoints'],'/',len(attempts),flush=True)
 save('complete')
except Exception as e:save('failed',error=repr(e));raise
