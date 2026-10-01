"""Static precontact endpoints using the actual lowest hand collision vertex.
No free virtual contact reference, object writes or controller changes. Compare
5/10/15mm inward shifts of the selected surface at identical frozen recorded object poses. Keep
original command bounds, elbow 5mm, inactive palm 0.5mm, hand/other gap 10mm.
Lowest vertex is constrained 6..7mm above target top in its local normal frame;
XY error is minimized, not assumed feasible. Original normal held/free compared.
Local SLSQP failure is not proof of unreachable geometry. No path/dynamics proof.
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
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
guard=ClearanceGuard(repo,stage);reports=[]
for cid,task,side in [(840001,'push_box_to_bin','right'),(840004,'nudge_mailer_to_bin','left')]:
 ep=w/'unloaded_wrist_prior_groups_r1'/f'case_{cid}/layout_{cid}_{task}'
 if not (ep/'quality.json').exists():continue
 fr=json.loads((ep/'frontal_bypass.json').read_text());cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';inactive='left' if side=='right' else 'right'
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);commands=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);otherxyz=z[other].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rots=Rotation.from_quat(z[key]).as_matrix();otherquat=z[other].copy()
 core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);other_size=np.array([.15,.145,.04] if other=='mailer' else [.14,.09,.045]);verts=guard.model.vertices[side];separation=hand_face_separation(side)
 crosses=[];last=None
 for r in fr['rows']:
  if r['mode']=='top_cross' and last!='top_cross' and r['recontacts']>0:crosses.append(r)
  last=r['mode']
 assert crosses
 for r in [crosses[0],crosses[-1]]:
  t=r['step'];q=qs[t];c=cs[t];rot=rots[t];obj=xyz[t];normal=np.array(c['contact_normal_tracking']['target_local_up']);inactive_goal=np.array(c['inactive_anchor']);selected=(rot.T@(np.array(r['parcel_top_xyz'])-obj))[:2]
  assert r['contact_load']['observed_vertical_load_n']==0
  def geom(x):
   T,jl,jw=guard.model.fk(side,x);R=T[:3,:3];points=(verts@R.T+T[:3,3]-obj)@rot;ix=int(points[:,2].argmin());v=R@verts[ix];J=rot.T@(jl-skew(v)@jw);Ti,jli,jwi=guard.model.fk(inactive,x);off=Ti[:3,:3]@np.array([.20,0,.007]);palm=Ti[:3,3]+off;Ji=jli-skew(off)@jwi;up=R[2];uj=R.T@skew([0,0,1.])@jw;gap=separation.gap(T[:3,3],Rotation.from_matrix(R).as_quat(),otherxyz[t],otherquat[t],other_size)
   return points[ix],J,palm,Ji,up,uj,float(gap),ix
  candidates=[]
  for label,xy in [(f'inward_{int(mm)}mm',selected*(1-min(mm/1000/np.linalg.norm(selected),1.))) for mm in [5,10,15]]:
   for hold in [True]:
    def cost(x):
     point,J,*_=geom(x);e=point[:2]-xy;d=x-q
     return float(e@e+1e-8*(d@d)),2*e@J[:2]+2e-8*d
    def cons(x):
     point,J,palm,Ji,up,uj,gap,ix=geom(x);e=palm-inactive_goal
     vals=np.r_[point[2]-core[2]/2-.006,core[2]/2+.007-point[2],.0005-e,.0005+e,guard.geometry.constraints(x)-.005]
     jac=np.vstack([J[2],-J[2],-Ji,Ji,guard.geometry.jacobian(x)])
     if hold:vals=np.r_[vals,.001-(up-normal),.001+(up-normal)];jac=np.vstack([jac,-uj,uj])
     return vals,jac
    # Gap constraint has finite-difference Jacobian; support geometry is analytic.
    starts=[np.clip(q,guard.lower,guard.upper)];early=qs[crosses[0]['step']].copy();early[5 if side=='left' else 10]=0.;starts.append(np.clip(early,guard.lower,guard.upper))
    tries=[]
    for start in starts:
     fit=minimize(cost,start,jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:geom(x)[6]-.01)],method='SLSQP',options=dict(maxiter=180,ftol=1e-12));x=fit.x;p,J,palm,Ji,up,uj,gap,ix=geom(x);minimum=float(min(cons(x)[0]));valid=bool(fit.success and minimum>=-2e-7 and gap>=.01-2e-7);err=float(np.linalg.norm(p[:2]-xy))
     tries.append(dict(solver_success=bool(fit.success),status=int(fit.status),iterations=int(fit.nit),constraints_passed=valid,minimum_constraint=minimum,physical_vertex_index=ix,physical_vertex_local=verts[ix].tolist(),contact_object_local=p.tolist(),xy_error_mm=err*1000,hand_other_gap_m=gap,minimum_elbow_gap_m=float(min(guard.geometry.constraints(x))),normal_error_norm=float(np.linalg.norm(up-normal)),candidate=x.tolist(),objective=float(fit.fun),endpoint_within2mm=bool(valid and err<=.002)))
    best=min(tries,key=lambda a:(not a['constraints_passed'],a['xy_error_mm']))
    if best['endpoint_within2mm']:
     goal=np.array(best['candidate']);n=max(1,int(np.ceil(max(abs(goal-q)/(guard.limits*.5)))));path=[np.clip(q+(goal-q)*i/n,guard.lower,guard.upper) for i in range(n+1)];checks=[];previous=commands[t-1];minz=float('inf');mingap=float('inf');maxinactive=0.
     for i,x in enumerate(path):
      checks.append(guard.command(x,q if i==0 else path[i-1],previous)['accepted']);previous=x;point,_,palm,_,_,_,gap,_=geom(x);minz=min(minz,float(point[2]-core[2]/2));mingap=min(mingap,gap);maxinactive=max(maxinactive,float(np.linalg.norm(palm-inactive_goal)))
     best['linear_path_screen']=dict(steps=len(path),all_command_checks=all(checks),minimum_hand_above_target_plane_m=minz,minimum_hand_other_gap_m=mingap,max_inactive_anchor_error_m=maxinactive,passed=bool(all(checks) and minz>=.004 and mingap>=.01 and maxinactive<=.015),scope='Sampled straight joint interpolation, no recursive dynamics, no full-body/substep collision proof.')
    entry=dict(target=label,hold_original_normal=hold,target_xy=xy.tolist(),best=best,attempts=tries);candidates.append(entry)
    print(ep.name,t,label,'hold',hold,'valid',best['constraints_passed'],'xy_mm',round(best['xy_error_mm'],3),'status',best['status'],flush=True)
  reports.append(dict(episode=ep.name,step=t,selected_xy=selected.tolist(),core_size=core.tolist(),candidates=candidates,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','coordination.json','frontal_bypass.json','quality.json']}))
  (w/'REAR_INWARD_PHYSICAL_CONTACT_SCREEN.json').write_text(json.dumps(dict(scope=__doc__,rows=reports,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json',repo/'simfoundry/data/hand_obstacle_clearance.py']},model_sources=guard.model.source_sha256,controller_changed=False,training_ready=False),indent=2))
