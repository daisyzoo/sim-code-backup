"""Counterfactual recursive unloaded dwell using the original Cartesian/normal task.
URDF observation and fixed recorded parcel poses; no simulator, contact, or object
writes. Compare prior off/on for 60 control ticks with ideal tracking, calibrated
first-order response, and its locally measured constant bias. Predictions beyond
one step are not validated dynamics; this is a rejection/feasibility preflight.
No stronger wrist prior or changed geometry/limits. Original target remains .86m.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_unloaded_wrist_prior';sys.path[:0]=[str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from articulated_hand_geometry import skew
from task_ik import solve
from simfoundry.data.projected_support_reference import projected_support_reference,projected_support_jacobian
from simfoundry.data.contact_normal_constraint import contact_normal_constraint
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);reports=[]
for cid,task,side,wi in [(840001,'push_box_to_bin','right',10),(840004,'nudge_mailer_to_bin','left',5)]:
 ep=w/'unloaded_wrist_prior_groups_r1'/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())}
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);commands=z['action'][:,12:23].astype(float)
 crossings=[];last=None
 for r in fr['rows']:
  if r['mode']=='top_cross' and last!='top_cross' and r['recontacts']>0:crossings.append(r)
  last=r['mode']
 for r in [crossings[0],crossings[-1]]:
  t=r['step'];c=cs[t];q0=qs[t];u0=commands[t-1];reference=c['active_support_reference'];world_normal=np.array(reference['world_normal']);center=np.array(reference['center_local']);normal=np.array(c['contact_normal_tracking']['target_local_up']);inactive='left' if side=='right' else 'right';anchor=np.array(c['inactive_anchor']);target=np.array(r['target_xyz']);assert abs(target[2]-.86)<1e-6
  decay=np.array(fr['plan']['region_causal_response']['decay']);local_bias=(q0-u0)-decay*(qs[t-1]-u0)
  def task_at(q):
   js=[];errors=[];points={};height=None
   for s in ['left','right']:
    T,jl,jw=guard.model.fk(s,q);R=T[:3,:3]
    if s==side:
     ref=projected_support_reference(guard.model.vertices[s],R,world_normal,center_local=center);point=T[:3,3]+R@ref['reference_local'];J=projected_support_jacobian(jl,jw,R,ref);goal=target;height=float((guard.model.vertices[s]@R.T+T[:3,3])[:,2].min());normal_c=contact_normal_constraint(R,jw,normal)
    else:
     off=R@np.array([.20,0,.007]);point=T[:3,3]+off;J=jl-skew(off)@jw;goal=anchor
    js.append(J);errors.append(np.clip(.72*(goal-point),-.035,.035));points[s]=point
   js.append(normal_c['jacobian']);errors.append(normal_c['error'])
   return np.vstack(js).astype(np.float32),np.concatenate(errors).astype(np.float32),points,height,float(normal_c['angle_error_rad'])
  J,e,_,_,_=task_at(q0);initial_j_error=float(np.max(abs(J-np.array(c['task_inputs']['jacobian']))));initial_e_error=float(np.max(abs(e-np.array(c['task_inputs']['error']))));assert initial_j_error<2e-5 and initial_e_error<2e-6,(initial_j_error,initial_e_error)
  variants=[]
  for model in ['ideal','calibrated_zero_bias','calibrated_local_bias']:
   a=np.zeros(11) if model=='ideal' else decay;bias=local_bias if model=='calibrated_local_bias' else np.zeros(11)
   for prior_on in [False,True]:
    q=q0.copy();prev=u0.copy();records=[];failure=None
    for k in range(60):
     J,e,points,z,angle=task_at(q);prior=np.zeros(11)
     if prior_on and z>=.84:prior[wi]=np.float32(np.clip(-.15*q[wi],-.04,.04))
     inp=dict(jacobian=J,error=e,current=q,previous=prev,lower=guard.lower,upper=guard.upper,step_limits=guard.limits,damping=np.array(c['task_inputs']['damping']),preferred_step=prior)
     u,meta=solve(enabled=True,geometry=guard.geometry,**inp)
     if u is None:failure=dict(tick=k,reason='original_solver_no_command');break
     check=guard.command(u,q,prev);nextq=(1-a)*u+a*q+bias;_,_,npnt,nz,na=task_at(nextq);_,_,_,uz,_=task_at(u)
     upper=guard.upper.copy();lower=guard.lower.copy();upper[0]=1.;lower[0]=-1.
     accepted=bool(check['accepted'] and uz>=.84 and nz>=.84 and np.all(nextq>=lower-2e-7) and np.all(nextq<=upper+2e-7) and min(guard.geometry.constraints(nextq))>0)
     records.append(dict(tick=k,wrist_rad=float(nextq[wi]),prior_applied=bool(prior[wi]),active_error_mm=float(np.linalg.norm(npnt[side]-target)*1000),inactive_error_mm=float(np.linalg.norm(npnt[inactive]-anchor)*1000),normal_angle_rad=na,command_height_m=uz,predicted_height_m=nz,accepted=accepted,command=u.tolist(),predicted_q=nextq.tolist()))
     if not accepted:failure=dict(tick=k,reason='command_or_predicted_geometry',command_checks=check['checks']);break
     q=nextq;prev=u
    summary=dict(model=model,prior_on=prior_on,ticks=len(records),failure=failure,initial_wrist_rad=float(q0[wi]),final_wrist_rad=float(q[wi]),wrist_abs_reduction_rad=float(abs(q0[wi])-abs(q[wi])),applied_ticks=sum(x['prior_applied'] for x in records),max_active_error_mm=max((x['active_error_mm'] for x in records),default=None),max_inactive_error_mm=max((x['inactive_error_mm'] for x in records),default=None),final_active_error_mm=records[-1]['active_error_mm'] if records else None,final_normal_angle_rad=records[-1]['normal_angle_rad'] if records else None,minimum_hand_height_m=min((x['predicted_height_m'] for x in records),default=None))
    variants.append(dict(summary=summary,records=records));print(ep.name,t,json.dumps(summary),flush=True)
  reports.append(dict(episode=ep.name,step=t,initial_jacobian_error=initial_j_error,initial_task_error=initial_e_error,local_response_bias_rad=local_bias.tolist(),variants=variants,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json']}))
  (w/'UNLOADED_WRIST_RECURSIVE_DWELL_SCREEN.json').write_text(json.dumps(dict(scope=__doc__,rows=reports,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'task_ik.py',stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',repo/'simfoundry/data/projected_support_reference.py',repo/'simfoundry/data/contact_normal_constraint.py']},model_sources=guard.model.source_sha256,controller_changed=False,physical_validation=False,training_ready=False),indent=2))
