"""Prospective top-contact endpoint screen for every diagnosed rear route.
Compare initial object pose and hypothetical rear-X endpoints with original Y or
safe Y preposition; frozen initial orientation. Full11D movable arms/waist within
original command bounds. Selected hand/parcel/elbow geometry only: no whole-body,
continuous path, tracking, pressure or physical contact certificate.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
from scipy.optimize import minimize,Bounds
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_closed_peak_trial';sys.path[:0]=[str(STAGE),str(ROOT),str(W)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from articulated_hand_geometry import skew
from audit_minimum_motion_plan_reentrant import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(run):
 run=Path(run).resolve();out=run/'INITIAL_REAR_TOP_CONTACT_SCREEN.json';assert not out.exists();guard=ClearanceGuard(ROOT,STAGE);independent=PlanAudit(ROOT,STAGE);refpath=run/'RECORDED_CONTACT_FORCE_SIGN_CHECK.json';refs=json.loads(refpath.read_text())['records'];records=[];sources={str(refpath):sha(refpath)}
 def save(complete):
  files=[Path(__file__),W/'audit_minimum_motion_plan_reentrant.py',W/'audit_recontact_interior_events.py',W/'audit_recontact_pose_events.py',STAGE/'clearance_runtime.py',STAGE/'recontact_scene.py',STAGE/'articulated_hand_geometry.py',STAGE/'self_clearance.py',STAGE/'elbow_torso_hulls.json',*[Path(p) for p in guard.model.source_sha256]]
  sources.update({str(p):sha(p) for p in files});out.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=complete,records=records,source_sha256=sources,runtime_changed=False,training_ready=False,full_route_verified=False),indent=2))
 for ref in refs:
  ep=next(run.glob('case_*/'+ref['episode']));data=json.loads((ep/'frontal_bypass.json').read_text());p=data['plan'];fr=next(x for x in data['rows'] if x['mode']=='rear_push');t=fr['step'];side='right' if ep.name.endswith('push_box_to_bin') else 'left';target='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';visual={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};core=np.array(p['region_causal_response']['actual_core']['collision_core_size_xyz']);q=np.array(next(c for c in json.loads((ep/'coordination.json').read_text()) if c['step']==t)['task_inputs']['current']);prov=json.loads((ep.parent/'provenance.json').read_text())
  for name in ['clearance_runtime.py','recontact_scene.py','articulated_hand_geometry.py','self_clearance.py','elbow_torso_hulls.json']:
   f=STAGE/name;assert sha(f)==prov['source_sha256'][str(f.relative_to(ROOT))]
  with np.load(ep/'trace.npz') as z:initial=z[target][t].copy();obstacle=z[other][t].copy()
  with np.load(ep/'parcel_orientation.npz') as z:tq=z[target][t].copy();oq=z[other][t].copy()
  rt=(abs(Rotation.from_quat(tq).as_matrix())@(visual[target]/2))[:2];ro=(abs(Rotation.from_quat(oq).as_matrix())@(visual[other]/2))[:2];rear_x=obstacle[0]+rt[0]+ro[0]+p['margin'];direction=p['direction'];goal_y=p['front_route_candidates']['goal_y'];limit_y=obstacle[1]-direction*(rt[1]+ro[1]+p['margin']);advance=max(0.,min(direction*(limit_y-initial[1]),direction*(goal_y-initial[1])));end=initial.copy();end[0]=rear_x;pre=end.copy();pre[1]+=direction*advance
  episode=dict(episode=ep.name,original_task_passed=json.loads((ep/'quality.json').read_text())['passed'],observed_precontact_step=t,initial_target=initial.tolist(),safe_y_advance_m=float(advance),scenes=[]);records.append(episode)
  for name,pos in [('initial_top',initial),('rear_x_initial_y',end),('rear_x_prepositioned_y',pre)]:
   scene=RecontactScene(guard,side,pos,tq,core,obstacle,oq,visual[other]);normal=scene.rotation[:,2];axis=np.linalg.eigh(np.cov(guard.model.vertices[side].T))[1][:,0];half=core[:2]/2-.020
   def align(x):
    T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@axis;return float(normal@v),normal@(-skew(v)@jw)
   def cost(x):d=x-q;return float(d@d),2*d
   def cons(x):
    d=scene.details(x);P=d['point'];J=d['jacobian'];a,da=align(x);return np.r_[a*a-.8**2,half-P[:2],half+P[:2],P[2]-core[2]/2-.006,core[2]/2+.007-P[2],d['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([2*a*da,-J[:2],J[:2],J[2],-J[2],d['inactive_z_jacobian'],guard.geometry.jacobian(x)])
   attempts=[]
   seeds=[('observed_precontact',q)]+[(f'neutral_waist{yaw}',np.r_[yaw,np.zeros(10)]) for yaw in [-.5,0.,.5]]
   for label,seed in seeds:
    fit=minimize(cost,np.clip(seed,guard.lower,guard.upper),jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options=dict(maxiter=180,ftol=1e-12));x=np.array(fit.x);g,d=independent.geometry(x,scene.record());a=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis);minimum=float(min(a*a-.8**2,*list(core[:2]/2-.020-abs(d['point'][:2])),g['active_above_top_m']-.006,.007-g['active_above_top_m'],independent.hand.minz(x,scene.inactive)-.84,g['elbow_gap_m']-.005));assert abs(minimum-float(min(cons(x)[0])))<2e-7
    accepted=bool(fit.success and minimum>=-2e-7 and min(g['hand_parcel_gaps_m'].values())>=.01-2e-7 and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7));attempts.append(dict(seed=label,accepted=accepted,solver_success=bool(fit.success),status=int(fit.status),iterations=int(fit.nit),minimum_constraint_m=minimum,independent_geometry=g,support_local_m=d['point'].tolist(),alignment_abs=float(a),candidate_q=x.tolist(),objective=float(fit.fun)))
   scene_row=dict(name=name,scene=scene.record(),attempts=attempts,accepted_endpoints=sum(a['accepted'] for a in attempts));episode['scenes'].append(scene_row);save(False);print(json.dumps(dict(episode=ep.name,scene=name,accepted=scene_row['accepted_endpoints'],minimums=[a['minimum_constraint_m'] for a in attempts])),flush=True)
  for f in [ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'coordination.json',ep/'quality.json',ep.parent/'provenance.json']:sources[str(f)]=sha(f)
 save(True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();main(a.run)
