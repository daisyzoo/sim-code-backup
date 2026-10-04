"""Independent original-tolerance stationarity check of unissued joint proposals.
Keeps unique elbow axis/all support vertex treatment. Not a dynamic certificate.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;S=W/'staged_inactive_transport_v2';ROOT=W.parents[1]
sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from loaded_z_priority_checks import NativeCertificateGeometry
from loaded_z_priority_solver import up_and_jacobian
from loaded_z_priority_stationarity import certificate,planes
from recontact_scene import RecontactScene
G=ClearanceGuard(ROOT,S);geo=NativeCertificateGeometry(G);sources={}
def read(p):sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
probe=read(D/'RESULT.json');out=[]
for path,h in probe['source_sha256'].items():
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,path
for result in probe['results']:
 side=result['side'];inactive='right' if side=='left' else 'left';zr=2 if side=='left' else 5
 ep=W/'inactive_transport_physical_r1'/('case_'+result['episode'].split('_')[1])/result['episode'];records=read(ep/'inactive_transport_clearance.json')['rows'];coords={v['step']:v for v in read(ep/'coordination.json')}
 t=result['step'];p=records[t]['proposal'];q,qp,prev,parent,decay=[np.array(p[k]) for k in ['current','previous_q','previous_command','parent_command','decay']];u=np.array(result['command']);np.testing.assert_array_equal(parent,result['parent_command']);np.testing.assert_array_equal(q,result['current']);assert np.array_equal(u,u.astype(np.float32));bias=q-prev-decay*(qp-prev)
 def predict(x):return (1-decay)*x+decay*q+bias
 z=p['scene'];scene=RecontactScene(G,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);c=coords[t];task=c['task_inputs'];J=np.array(task['jacobian']);e=np.array(task['error']);reg=np.array(task['damping'])**2;prior=np.array(task['preferred_step']);target=np.array(c['contact_normal_tracking']['target_local_up']);target/=np.linalg.norm(target);pn=np.linalg.norm(J[6:]@(parent-q)-e[6:]);parent_up,_=up_and_jacobian(G.model,parent,side);pe=np.linalg.norm(parent_up-target)
 nodes=[(kind,alpha) for kind in ['nominal','predicted'] for alpha in [.25,.5,.75,1.]];branches={};ambiguous=[]
 for kind,alpha in nodes:
  state=q+alpha*((u if kind=='nominal' else predict(u))-q)
  for elbow_side,i in [('left',0),('right',1)]:
   gap=geo.gap(state)[i]
   if gap-.005<=1e-6:
    values=planes(geo,state,elbow_side);gaps=values.min(0);branch=int(gaps.argmax());sep=float(np.sort(gaps)[-1]-np.sort(gaps)[-2]);assert abs(gaps[branch]-gap)<1e-12
    if sep<=2e-6:ambiguous.append(dict(kind=kind,alpha=alpha,side=elbow_side,separation=sep))
    branches[kind,alpha,elbow_side]=branch
  details=scene.details(state)
  for name in ['inactive_target','inactive_other','active_other']:
   if details['gaps'][name]-.01<=2e-6:ambiguous.append(dict(kind=kind,alpha=alpha,parcel=name,reason='active_parcel_separating_axis_not_certified'))
 if ambiguous:
  out.append(dict(step=t,side=side,episode=ep.name,passed=False,reason='ambiguous_or_unverified_active_branch',details=ambiguous));continue
 def extra(x):
  pred=predict(x);err=J@(x-q)-e;up,_=up_and_jacobian(G.model,x,side);height=float(J[zr]@(x-parent));parts=[height,-height,pn-np.linalg.norm(err[6:]),pe-np.linalg.norm(up-target)];parts.extend(pred-G.lower);parts.extend(G.upper-pred)
  for kind,alpha in nodes:
   state=q+alpha*((x if kind=='nominal' else pred)-q);T,_,_=G.model.fk(inactive,state);points=G.model.vertices[inactive]@T[:3,:3].T+T[:3,3];floor=.8415 if alpha==1 else .84;parts.extend(points[:,2]-floor);details=scene.details(state)
   parts.extend(details['gaps'][name]-.01 for name in ['inactive_target','inactive_other','active_other'])
   for elbow_side,i in [('left',0),('right',1)]:
    if (kind,alpha,elbow_side) in branches:parts.extend(planes(geo,state,elbow_side)[:,branches[kind,alpha,elbow_side]]-.005)
    else:parts.append(geo.gap(state)[i]-.005)
  return np.array(parts)
 values=extra(u);jac=np.empty((len(values),11));h=2e-7
 for j in range(11):
  offset=np.eye(11)[j]*h;jac[:,j]=(extra(u+offset)-extra(u-offset))/(2*h)
 lo=np.maximum.reduce([G.lower,q-G.limits,prev-.055]);hi=np.minimum.reduce([G.upper,q+G.limits,prev+.055]);delta=u-q;gradient=J.T@(J@delta-e)+reg*(delta-prior);cert=certificate(geometry=geo,x=u,gradient=gradient,lower=lo,upper=hi,extra_values=values,extra_jacobian=jac);out.append(dict(step=t,side=side,episode=ep.name,passed=cert['passed'],certificate=cert,finite_difference_step=h,physical_command_issued=False))
 print(json.dumps(dict(step=t,side=side,episode=ep.name,passed=cert['passed'],reason=cert['reason'],stationarity_residual=cert['stationarity_residual'],primal_feasible=cert['primal_feasible'])),flush=True)
for p in [Path(__file__),S/'loaded_z_priority_stationarity.py',S/'loaded_z_priority_checks.py',S/'loaded_z_priority_solver.py',S/'self_clearance.py',S/'recontact_scene.py',S/'articulated_hand_geometry.py']:sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=all(v['passed'] for v in out),results=out,source_sha256=sources,continuous_path_certificate=False,physical_command_issued=False,training_ready=False)
with (D/'INDEPENDENT_STATIONARITY.json').open('x') as f:json.dump(report,f,indent=2)
