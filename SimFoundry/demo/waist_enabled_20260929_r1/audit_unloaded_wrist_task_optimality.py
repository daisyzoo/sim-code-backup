"""Independent declared unloaded wrist prior plus original task KKT/feasibility.
URDF elbow transforms and support projections reconstructed without candidate
geometry/solver imports. Finite-difference constraint gradients, independent NNLS
KKT residual. Uses recorded Jacobian, does not independently measure runtime J.
Not full contact-control, whole-body, visual or training admission.
"""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import nnls
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from simfoundry.data.bounded_ik import bounded_damped_step
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def near(a,b,tol=1e-8):
 a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
 assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all() and np.max(abs(a-b),initial=0)<=tol
class IndependentElbows:
 def __init__(self,hulls,urdf):
  d=json.loads(Path(hulls).read_text());assert sha(urdf)==d['urdf_sha256'];self.v={s:np.array(d[s]['vertices']) for s in ['left','right']}
  z=np.linspace(-1,1,80);a=np.arange(80)*np.pi*(3-np.sqrt(5));self.axes=np.vstack([np.eye(3),np.c_[np.sqrt(1-z*z)*np.cos(a),np.sqrt(1-z*z)*np.sin(a),z]]);t=np.array(d['torso']['vertices'])@self.axes.T;self.tmin=t.min(0);self.tmax=t.max(0)
  xml=ET.parse(urdf).getroot();bychild={j.find('child').get('link'):j for j in xml.findall('joint')};names=['waist_yaw_joint']+[s+'_'+j+'_joint' for s in ['left','right'] for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']];self.chains={}
  for side in self.v:
   l=side+'_elbow_link';chain=[]
   while l!='torso_link':
    j=bychild[l];o=j.find('origin');T=np.eye(4)
    if o is not None:T[:3,3]=np.fromstring(o.get('xyz','0 0 0'),sep=' ');T[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix()
    axis=np.fromstring(j.find('axis').get('xyz'),sep=' ') if j.find('axis') is not None else None;chain.append((names.index(j.get('name')) if j.get('name') in names else None,T,axis));l=j.find('parent').get('link')
   self.chains[side]=list(reversed(chain))
 def gap(self,q):
  out=[]
  for side,chain in self.chains.items():
   T=np.eye(4)
   for index,O,axis in chain:
    T=T@O
    if axis is not None:
     R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(axis*(q[index] if index is not None else 0.)).as_matrix();T=T@R
   p=(self.v[side]@T[:3,:3].T+T[:3,3])@self.axes.T;out.append(max(np.max(p.min(0)-self.tmax),np.max(self.tmin-p.max(0))))
  return np.array(out)
 def gradient(self,q):
  G=np.zeros((2,11));h=2e-7
  for i in [1,2,3,4,6,7,8,9]:
   delta=np.zeros(11);delta[i]=h;G[:,i]=(self.gap(q+delta)-self.gap(q-delta))/(2*h)
  return G

def inspect(ep):
 ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());src=prov['source_sha256'];snap=ep.parent/'source_snapshot';args=prov['args'];assert args['self_clearance_task_ik'] and args['bounded_coupled_ik'] and not args['policy_port'] and not args['expert_top_contact_bout_yaw_hold'];assert args['waist_limit_rad']==1.
 for n,h in src.items():assert sha(snap/n)==h
 for n in ['simfoundry/robots/g1_assets.py','simfoundry/data/bounded_ik.py']:assert sha(repo/n)==src[n]
 def archived(name):
  paths=[snap/n for n in src if n.endswith('/'+name)];assert len(paths)==1;return paths[0]
 geom=IndependentElbows(archived('elbow_torso_hulls.json'),archived('g1_23dof_rev_1_0_u1_black.urdf'))
 from audit_unloaded_wrist_prior_live import inspect as inspect_prior
 prior_audit=inspect_prior(ep);assert prior_audit==json.loads((ep/'UNLOADED_WRIST_PRIOR_LIVE_AUDIT.json').read_text());prior_by={x['step']:x['expected_prior'] for x in prior_audit['records']}
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);side='right' if str(z['task_id'])=='push_box_to_bin' else 'left'
 rows=json.loads((ep/'coordination.json').read_text());experts={x['step']:x for x in json.loads((ep/'expert_control.json').read_text())};failure=json.loads((ep/'self_clearance.json').read_text())['failure'];records=[]
 lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.r_[.015,np.full(10,.04)];damping=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10)).astype(float)
 for c in rows:
  t=c['step']
  if t>=len(q):assert failure is not None;continue
  assert c['bounded_solver'] is True and c['contact_bout_yaw_tracking'] is None
  inp=c['task_inputs'];tr=c['self_clearance_task'];near(inp['current'],q[t],1e-6);near(inp['previous'],u[t-1],0);near(inp['lower'],lo,0);near(inp['upper'],hi,0);near(inp['step_limits'],limits,0);near(inp['damping'],damping,0)
  errors=[]
  for hand in ['left','right']:
   goal=experts[t]['target_xyz'] if hand==side else c['inactive_anchor'];point=c['control_point_positions'][hand];errors.extend(np.clip(np.float32(.72)*(np.array(goal,dtype=np.float32)-np.array(point,dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
  J=np.array(inp['jacobian']);E=np.array(inp['error']);assert J.shape[1]==11
  if 'control_jacobian_world' in c:near(J[:6],c['control_jacobian_world'],0)
  normal=c['contact_normal_tracking']
  if normal is not None:errors.extend(np.asarray(normal['error'],dtype=np.float32).tolist());near(J[6:],np.asarray(normal['jacobian'],dtype=np.float32),0)
  else:assert J.shape==(6,11)
  near(E,errors,0);prior=np.array(prior_by[t]);near(prior[0],c['preferred_waist_step_rad'],0);near(inp['preferred_step'],prior,0)
  if c['waist_preference_rad'] is None:assert prior[0]==0
  else:near(prior[0],float(np.float32(np.clip(np.float32(.15)*np.float32(c['waist_preference_rad']-q[t,0]),-.015,.015))),1e-7)
  baseline=(q[t]+bounded_damped_step(J,E,q[t],lo,hi,limits,damping,preferred_step=prior)).astype(np.float32).astype(float)
  low=np.maximum.reduce([lo,q[t]-limits,u[t-1]-.055]);high=np.minimum.reduce([hi,q[t]+limits,u[t-1]+.055]);assert np.all(low<high)
  baseline_valid=bool(np.all(baseline>=low-2e-7) and np.all(baseline<=high+2e-7) and min(geom.gap(baseline))>=.005-2e-7)
  assert tr['accepted'] is True and type(tr['override']) is bool
  if not tr['override']:
   assert baseline_valid and tr['reason']=='original_task_solution_clear';records.append(dict(step=t,override=False));continue
  assert not baseline_valid and tr['solver_success'] is True and tr['status']==0 and 0<tr['iterations']<=150
  x=np.array(tr['candidate_command']);near(x,x.astype(np.float32),0);near(tr['parent_command'],baseline,0);near(tr['previous_command'],u[t-1],0)
  gap=geom.gap(x);near(gap,tr['candidate_gaps_m'],2e-10);assert min(gap)>=.005-2e-7 and np.all(x>=low-2e-7) and np.all(x<=high+2e-7)
  delta=x-q[t];near(tr['task_residual_m'],J@delta-E,1e-10);gradient=J.T@(J@delta-E)+damping*damping*(delta-prior)
  constraints=[];G=geom.gradient(x)
  for i in range(2):
   if gap[i]-.005<=1e-6:constraints.append(G[i])
  for i in range(11):
   if x[i]-low[i]<=2e-6:constraints.append(np.eye(11)[i])
   if high[i]-x[i]<=2e-6:constraints.append(-np.eye(11)[i])
  if constraints:
   A=np.array(constraints);norm=np.linalg.norm(A,axis=1);A=A[norm>1e-12]/norm[norm>1e-12,None];_,residual=nnls(A.T,gradient,maxiter=1000)
  else:residual=float(np.linalg.norm(gradient))
  records.append(dict(step=t,override=True,kkt_residual=float(residual),stationary=residual<=1e-6))
 bad=[r for r in records if r.get('stationary') is False];return dict(passed=not bad,errors=bad,frames=len(records),overrides=sum(r['override'] for r in records),max_kkt_residual=max((r.get('kkt_residual',0) for r in records),default=0),records=records,scope=__doc__,prior_audit_sha256=sha(ep/'UNLOADED_WRIST_PRIOR_LIVE_AUDIT.json'),prior_auditor_sha256=sha(w/'audit_unloaded_wrist_prior_live.py'),training_ready=False,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','expert_control.json','self_clearance.json']},auditor_sha256=sha(Path(__file__)))
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=inspect(ep);(ep/'UNLOADED_WRIST_TASK_OPTIMALITY_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['records','source_sha256','scope']},indent=2));sys.exit(0 if out['passed'] else 1)
