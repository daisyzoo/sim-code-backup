"""Unexecuted recontact-pose planning: actual lowest vertex in core inset10mm.
A new pose may change the hand normal only while unloaded; a future controller
would have to reach it safely and capture its measured normal for the next bout.
This is an offline screen, not that controller or a collision/dynamics proof.
Object poses fixed; active hand6..7mm above top; inactive whole hand>=.84;
original bounds/elbow5mm and active-hand/other10mm. Compare wrist preference
without choosing a free virtual contact point. Sample joint interpolation and
first-order tracking with local bias, retaining all rejected attempts.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import minimize,Bounds
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_unloaded_wrist_prior';sys.path[:0]=[str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from articulated_hand_geometry import skew
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);reports=[]
for cid,task,side,wi in [(840001,'push_box_to_bin','right',10),(840004,'nudge_mailer_to_bin','left',5)]:
 ep=w/'unloaded_wrist_prior_groups_r1'/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());cs={v['step']:v for v in json.loads((ep/'coordination.json').read_text())};key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';inactive='left' if side=='right' else 'right'
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);commands=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);otherxyz=z[other].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rots=Rotation.from_quat(z[key]).as_matrix();otherquat=z[other].copy()
 core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);other_size=np.array([.15,.145,.04] if other=='mailer' else [.14,.09,.045]);verts=guard.model.vertices[side];sep=hand_face_separation(side);decay=np.array(fr['plan']['region_causal_response']['decay']);crosses=[];last=None
 for r in fr['rows']:
  if r['mode']=='top_cross' and last!='top_cross' and r['recontacts']>0:crosses.append(r)
  last=r['mode']
 for r in [crosses[0],crosses[-1]]:
  t=r['step'];q=qs[t];rot=rots[t];obj=xyz[t];c=cs[t];half=core[:2]/2-.01;normal0=np.array(c['contact_normal_tracking']['target_local_up']);anchor=np.array(c['inactive_anchor']);bias=(q-commands[t-1])-decay*(qs[t-1]-commands[t-1]);assert r['contact_load']['observed_vertical_load_n']==0
  def geom(x):
   T,jl,jw=guard.model.fk(side,x);R=T[:3,:3];points=(verts@R.T+T[:3,3]-obj)@rot;ix=int(points[:,2].argmin());J=rot.T@(jl-skew(R@verts[ix])@jw);Ti,jli,jwi=guard.model.fk(inactive,x);iv=guard.model.vertices[inactive];ip=iv@Ti[:3,:3].T+Ti[:3,3];ii=int(ip[:,2].argmin());ij=(jli-skew(Ti[:3,:3]@iv[ii])@jwi)[2];gap=sep.gap(T[:3,3],Rotation.from_matrix(R).as_quat(),otherxyz[t],otherquat[t],other_size)
   return points[ix],J,float(ip[ii,2]),ij,float(gap),ix,R[2],Ti[:3,3]+Ti[:3,:3]@np.array([.20,0,.007])
  def cons(x):
   p,J,iz,ij,gap,ix,n,ip=geom(x)
   return np.r_[half-p[:2],half+p[:2],p[2]-core[2]/2-.006,core[2]/2+.007-p[2],iz-.84,guard.geometry.constraints(x)-.005],np.vstack([-J[:2],J[:2],J[2],-J[2],ij,guard.geometry.jacobian(x)])
  variants=[]
  for wrist in [False,True]:
   def cost(x):
    d=x-q;return float(.002*(d@d)+(x[wi]**2 if wrist else 0)),.004*d+(2*np.eye(11)[wi]*x[wi] if wrist else 0)
   starts=[np.clip(q,guard.lower,guard.upper)];s=starts[0].copy();s[wi]=0.;starts.append(s);s=np.clip(qs[crosses[0]['step']],guard.lower,guard.upper);s[wi]=0.;starts.append(s);attempts=[]
   for start in starts:
    fit=minimize(cost,start,jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:geom(x)[4]-.01)],method='SLSQP',options=dict(maxiter=220,ftol=1e-12));x=fit.x;p,J,iz,ij,gap,ix,n,ip=geom(x);minimum=float(min(cons(x)[0]));valid=bool(fit.success and minimum>=-2e-7 and gap>=.01-2e-7)
    item=dict(success=valid,status=int(fit.status),iterations=int(fit.nit),objective=float(fit.fun),minimum_constraint=minimum,candidate=x.tolist(),physical_vertex_index=ix,contact_object_local=p.tolist(),core_xy_margin_mm=((core[:2]/2-abs(p[:2]))*1000).tolist(),wrist_rad=float(x[wi]),wrist_abs_reduction_rad=float(abs(q[wi])-abs(x[wi])),normal_change_rad=float(np.arccos(np.clip(n@normal0,-1,1))),inactive_palm_displacement_m=float(np.linalg.norm(ip-anchor)),inactive_min_z_m=iz)
    if valid:
     steps=max(1,int(np.ceil(max(abs(x-q)/(guard.limits*.5)))));path=[np.clip(q+(x-q)*i/steps,guard.lower,guard.upper) for i in range(steps+1)];tracking=[]
     for response in ['ideal','calibrated_local_bias']:
      current=q.copy();previous=commands[t-1].copy();minimums=dict(active_above_top_m=float('inf'),inactive_z_m=float('inf'),other_gap_m=float('inf'),elbow_gap_m=float('inf'));failure=None
      for k,u in enumerate(path+[path[-1]]*15):
       check=guard.command(u,current,previous)
       nxt=u.astype(float) if response=='ideal' else (1-decay)*u+decay*current+bias
       for pose in [u,nxt]:
        gp=geom(pose);minimums['active_above_top_m']=min(minimums['active_above_top_m'],float(gp[0][2]-core[2]/2));minimums['inactive_z_m']=min(minimums['inactive_z_m'],gp[2]);minimums['other_gap_m']=min(minimums['other_gap_m'],gp[4]);minimums['elbow_gap_m']=min(minimums['elbow_gap_m'],float(min(guard.geometry.constraints(pose))))
       physical_lower=guard.lower.copy();physical_upper=guard.upper.copy();physical_lower[0]=-1.;physical_upper[0]=1.
       accepted=bool(check['accepted'] and np.all(nxt>=physical_lower-2e-7) and np.all(nxt<=physical_upper+2e-7) and minimums['active_above_top_m']>=.004 and minimums['inactive_z_m']>=.84 and minimums['other_gap_m']>=.01 and minimums['elbow_gap_m']>0)
       if not accepted:failure=dict(tick=k,command_checks=check['checks']);break
       current=nxt;previous=u
      final=geom(current);tracking.append(dict(response=response,requested_ticks=len(path)+15,executed_ticks=k+1,failure=failure,minimums=minimums,final_q=current.tolist(),final_contact_local=final[0].tolist(),final_wrist_rad=float(current[wi]),scope='Frozen-pose sampled hand/parcel+elbow checks, fitted response extrapolation; no full-body/substep/contact certification.'))
     item['path_screens']=tracking
    attempts.append(item)
   best=min(attempts,key=lambda x:(not x['success'],x['objective']));variants.append(dict(wrist_preference=wrist,best=best,attempts=attempts));print(ep.name,t,'wrist',wrist,'endpoint',best['success'],'reduction',best['wrist_abs_reduction_rad'],'path',[(v['response'],v['failure']) for v in best.get('path_screens',[])],flush=True)
  reports.append(dict(episode=ep.name,step=t,variants=variants,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','coordination.json','frontal_bypass.json']}))
  (w/'RECONTACT_POSE_REGION_SCREEN.json').write_text(json.dumps(dict(scope=__doc__,rows=reports,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',repo/'simfoundry/data/hand_obstacle_clearance.py']},model_sources=guard.model.source_sha256,controller_changed=False,physical_validation=False,training_ready=False),indent=2))
