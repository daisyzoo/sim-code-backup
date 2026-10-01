"""Causal bounded region QP from measured failed states; no physical commands."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
s=(w/'screen_rear_top_contact_reach.py').read_text();exec(compile(s.split("run=root/'current_lateral_profile_r1'")[0],'<checked FK and Jacobians>','exec'))
buffer=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
assert 0<=buffer<=.001
start_mode=sys.argv[2] if len(sys.argv)>2 else "terminal"
assert start_mode in ("terminal","first_eligible")
cases=[w/'contact_bout_yaw_groups_r1/case_898001/layout_898001_push_box_to_bin',w/'fresh_diagonal_02_trial_v2_r1/case_840004/layout_840004_nudge_mailer_to_bin'];results=[]
for ep in cases:
 side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);other_size=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'raw.npz') as z:allq=z['q'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:alltr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:allori={k:z[k] for k in z.files}
 coords=json.loads((ep/'coordination.json').read_text());by_step={x['step']:x for x in coords};verts=np.array(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);half=size[:2]/2-.01;t=len(allq)-1
 if start_mode=='first_eligible':
  eligible=None
  for event in json.loads((ep/'frontal_bypass.json').read_text())['rows']:
   i=event['step']
   if event['mode'] not in ('top_cross','top_descend') or by_step[i]['contact_normal_tracking'] is not None:continue
   mat,_,_=fk(side,allq[i]);rot=Rotation.from_quat(allori[key][i]).as_matrix();ref=projected_support_reference(verts,mat[:3,:3],rot[:,2]);point=mat[:3,3]+mat[:3,:3]@ref['lowest_vertex_local'];loc=rot.T@(point-alltr[key][i])
   if np.all(abs(loc[:2])<=half) and loc[2]>=size[2]/2+.004:eligible=i;break
  if eligible is None:raise RuntimeError('No causal precontact activation frame for '+ep.name)
  t=eligible
 q0=allq[t];tr={k:v[t] for k,v in alltr.items()};ori={k:v[t] for k,v in allori.items()};coord=by_step[t];assert coord['contact_normal_tracking'] is None;anchor=np.array(coord['inactive_anchor']);rotation=Rotation.from_quat(ori[key]).as_matrix();normal=rotation[:,2]
 def geometry(q):
  m,jl,jw=fk(side,q);r=m[:3,:3];ref=projected_support_reference(verts,r,normal);point=m[:3,3]+r@ref['lowest_vertex_local'];local=rotation.T@(point-tr[key]);jp=rotation.T@(jl-skew(r@ref['lowest_vertex_local'])@jw);mi,jli,jwi=fk(inactive,q);po=np.array([.20,0,.007]);pi=mi[:3,3]+mi[:3,:3]@po;ji=jli-skew(mi[:3,:3]@po)@jwi
  gap=float(hand_face_separation(side).gap(m[:3,3],Rotation.from_matrix(r).as_quat(),tr[other],ori[other],other_size));minz=float((verts@r.T+m[:3,3])[:,2].min());return local,jp,pi,ji,gap,minz,int(ref['support_index'])
 m,_,_=fk(side,q0);fk_error=float(np.linalg.norm(m[:3,3]+m[:3,:3]@np.array([.20,0,.007])-tr['palm_'+side]));assert fk_error<.0001
 q=q0.copy();history=[];stop='iteration_limit'
 for k in range(600):
  local,jp,pi,ji,gap,minz,index=geometry(q);height=float(local[2]-size[2]/2);inside=bool(np.all(abs(local[:2])<=half+1e-7));inactive_error=float(np.linalg.norm(pi-anchor));row=dict(step=k,physical_point_local_xyz=local.tolist(),top_gap_m=height,inside_10mm_inset=inside,inactive_error_m=inactive_error,hand_other_gap_m=gap,min_hand_z_m=minz,support_index=index,waist_rad=float(q[0]),q=q.tolist());history.append(row)
  if not inside or gap<.005 or minz<.746:stop='geometry_guard';break
  if .003<=height<=.005 and inactive_error<.002:stop='geometric_approach_reached';break
  # Leave both tangential DOFs free inside the original region. Constrain their
  # linearized boundary, minimize a feedback1.5mm descent and inactive-anchor error.
  design=np.vstack([jp[2:3],ji,np.diag(damping)]);rhs=np.r_[.72*(max(.004,height-.0015)-height),np.clip(.72*(anchor-pi),-.035,.035),np.zeros(11)]
  hessian=design.T@design;linear=design.T@rhs
  lower=np.maximum(lo-q,-limits);upper=np.minimum(hi-q,limits);assert np.all(lower<upper)
  cj=np.vstack([jp[:2],-jp[:2]]);offset=np.r_[local[:2]+half-buffer,half-buffer-local[:2]]
  fit=minimize(lambda d: .5*d@hessian@d-linear@d,np.clip(np.zeros(11),lower,upper),jac=lambda d:hessian@d-linear,bounds=list(zip(lower,upper)),constraints=[dict(type='ineq',fun=lambda d:offset+cj@d,jac=lambda d:cj)],method='SLSQP',options=dict(ftol=1e-13,maxiter=100))
  row['qp_success']=bool(fit.success);row['qp_step_rad']=fit.x.tolist();row['line_search_attempts']=[]
  if not fit.success:stop='qp_failure: '+fit.message;break
  accepted=False
  for divisor in [1,2,4,8,16,32,64,128]:
   dq=fit.x/divisor;nq=q+dq;nl,_,npi,_,ngap,nminz,ni=geometry(nq)
   row['line_search_attempts'].append(dict(divisor=divisor,physical_point_local_xyz=nl.tolist(),support_index=ni,inside_10mm_inset=bool(np.all(abs(nl[:2])<=half+1e-7)),hand_other_gap_m=ngap,min_hand_z_m=nminz,inactive_error_m=float(np.linalg.norm(npi-anchor))))
   if np.all(abs(nl[:2])<=half+1e-7) and nl[2]>=size[2]/2+.003 and ngap>=.005 and nminz>=.746 and np.all(nq>=lo-1e-6) and np.all(nq<=hi+1e-6):accepted=True;break
  row['line_search_divisor']=divisor
  if not accepted:stop='nonlinear_geometry_guard';break
  assert np.max(abs(dq))<=.04000001 and abs(dq[0])<=.01500001
  row['max_joint_step_rad']=float(np.max(abs(dq)));q=nq
  if np.max(abs(dq))<1e-9:stop='stagnation';break
 result=dict(episode=ep.name,actual_frame=t,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),actual_fk_error_m=fk_error,stop=stop,steps=len(history),geometric_approach_reached=stop=='geometric_approach_reached',min_hand_other_gap_m=min(x['hand_other_gap_m'] for x in history),support_switches=sum(a['support_index']!=b['support_index'] for a,b in zip(history,history[1:])),final=history[-1],history=history);results.append(result);print(json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)
report=dict(start_mode=start_mode,planning_linearization_buffer_m=buffer,rows=results,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Causal measured-state local QP: no optimized target q, no future trajectory, no static multistart solution consumed. Original11joint bounds, per-step limits/damping/inactive anchor, original10mm-inset target region. Lowest physical vertex tangential coordinates allowed to move inside region; actual nonlinear FK line-search guards support region, height and sampled hand/table/other-object geometry. Parcels fixed and joint tracking ideal; NOT full-arm/self/swept collision, contact forces, load transition, camera improvement, dynamic pressing or sorting proof. No control source modified and no q physically executed.',training_ready=False)
(w/('CAUSAL_CONTACT_REGION_SCREEN.json' if buffer==0 else f'CAUSAL_CONTACT_REGION_BUFFER{round(buffer*1e6)}UM_{start_mode.upper()}_SCREEN.json')).write_text(json.dumps(report,indent=2))
