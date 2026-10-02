"""All eight original front routes: physical lowest-vertex centered first landing.
Uses the first actual unloaded top_cross state and present object poses. The
center constraint is on the actual hand hull, not the virtual plane reference.
No simulator, object mutation, force, whole-body sweep or training proof.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
import numpy as np
from scipy.optimize import minimize,Bounds
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from articulated_hand_geometry import skew
from minimum_motion_recontact import interpolate,lift_endpoint
from audit_minimum_motion_plan_reentrant import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);ind=PlanAudit(ROOT,S);records=[];out=W/'FRONT_INITIAL_CENTER_LANDING_PROBE.json';assert not out.exists();sources={str(p):sha(p) for p in [Path(__file__),S/'recontact_scene.py',S/'articulated_hand_geometry.py',S/'minimum_motion_recontact.py',S/'clearance_runtime.py',W/'audit_minimum_motion_plan_reentrant.py']};sources.update(guard.model.source_sha256)
def save(status,**kw):
 tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,simulation_started=False,collector_integrated=False,training_ready=False,**kw),indent=2));tmp.replace(out)
try:
 save('running')
 for ep in sorted((W/'fresh_closed_peak_trials_r1').glob('case_*/layout_*')):
  f=ep/'frontal_bypass.json'
  if not f.exists():continue
  d=json.loads(f.read_text());plan=d['plan']
  if not plan.get('front_route_selected'):continue
  r=next(x for x in d['rows'] if x['mode']=='top_cross' and x['contact_load']['observed_vertical_load_n']==0. and x['contact_load']['filtered_vertical_load_n']<=.05);t=r['step'];side='right' if 'push_box_to_bin' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
  with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:target=z[key][t];obstacle=z[other][t]
  with np.load(ep/'parcel_orientation.npz') as z:tq=z[key][t];oq=z[other][t]
  scene=RecontactScene(guard,side,target,tq,sizes[key],obstacle,oq,sizes[other]);core=scene.core;normal=scene.rotation[:,2];axis=np.linalg.eigh(np.cov(guard.model.vertices[side].T))[1][:,0];start_scene,start=ind.geometry(q,scene.record());record=dict(episode=ep.name,step=t,original_task_passed=json.loads((ep/'quality.json').read_text())['passed'],actual_start_q=q.tolist(),scene=scene.record(),initial_scene_check=start_scene,initial_physical_lowest_point_local_m=start['point'].tolist(),recorded_virtual_reference_goal_m=r['target_xyz'],actual_previous_observed_load_n=r['contact_load']['observed_vertical_load_n'],attempts=[],raised_paths=[],source_sha256={str(ep/n):sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','quality.json']});records.append(record)
  if not start_scene['accepted']:record['reason']='original_unloaded_start_scene_rejected';save('running');continue
  def align(x):
   T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@axis;return float(normal@v),normal@(-skew(v)@jw)
  def cost(x):delta=x-q;return float(delta@delta),2*delta
  def cons(x):
   g=scene.details(x);p=g['point'];J=g['jacobian'];a,da=align(x)
   return np.r_[a*a-.8**2,.002-p[:2],.002+p[:2],p[2]-core[2]/2-.006,core[2]/2+.007-p[2],g['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([2*a*da,-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
  for label,seed in [('actual_unloaded',q)]+[(f'neutral_waist_{y}',np.r_[y,np.zeros(10)]) for y in [-.5,0.,.5]]:
   save('running',current_episode=ep.name,current_seed=label);fit=minimize(cost,np.clip(seed,guard.lower,guard.upper),jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options=dict(maxiter=220,ftol=1e-12));x=np.asarray(fit.x);g,detail=ind.geometry(x,scene.record());a=abs(detail['rotation'][:,2]@detail['pose'][:3,:3]@axis);minimum=float(min(a*a-.8**2,*list(.002-abs(detail['point'][:2])),g['active_above_top_m']-.006,.007-g['active_above_top_m'],ind.hand.minz(x,scene.inactive)-.84,g['elbow_gap_m']-.005));assert abs(minimum-float(min(cons(x)[0])))<2e-7;accepted=bool(fit.success and minimum>=-2e-7 and min(g['hand_parcel_gaps_m'].values())>=.01-2e-7 and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7));path=interpolate(scene,[q,x]) if accepted else None
   if path:
    points,checks=ind.path([q,x],scene.record());assert np.max(abs(np.array(points)-np.array(path['waypoints'])))<1e-12;path['independent_checks']=checks;path['independently_accepted']=bool(path['accepted'] and all(v['accepted'] and v['elbow_gap_m']>=.005-2e-7 for v in checks))
   record['attempts'].append(dict(seed=label,solver_status=int(fit.status),iterations=int(fit.nit),accepted_endpoint=accepted,candidate_q=x.tolist(),independent_minimum_constraint_m=minimum,independent_geometry=g,independent_actual_point_local_m=detail['point'].tolist(),objective=float(fit.fun),nominal_path=path))
  good=[a for a in record['attempts'] if a['accepted_endpoint']];straight=[a for a in good if a['nominal_path']['independently_accepted']]
  if good and not straight:
   chosen=min(good,key=lambda a:a['objective']);end=np.array(chosen['candidate_q'])
   for height in [.015,.030,.060]:
    first=lift_endpoint(scene,q,max(height,float(start['point'][2]-core[2]/2)));last=lift_endpoint(scene,end,height);nodes=[q,np.array(first['candidate']),np.array(last['candidate']),end] if first['accepted'] and last['accepted'] else None;path=interpolate(scene,nodes) if nodes is not None else None
    if path:
     points,checks=ind.path(nodes,scene.record());assert np.max(abs(np.array(points)-np.array(path['waypoints'])))<1e-12;path['independent_checks']=checks;path['independently_accepted']=bool(path['accepted'] and all(v['accepted'] and v['elbow_gap_m']>=.005-2e-7 for v in checks))
    record['raised_paths'].append(dict(height_m=height,start_lift=first,end_lift=last,path=path))
  record.update(accepted_endpoints=len(good),accepted_straight_paths=len(straight),accepted_raised_paths=sum(bool(a['path'] and a['path']['independently_accepted']) for a in record['raised_paths']));save('running');print(ep.name,'endpoints',len(good),'straight',len(straight),'raised',record['accepted_raised_paths'],flush=True)
 assert len(records)==8;save('complete')
except Exception as e:save('failed',error=repr(e));raise
