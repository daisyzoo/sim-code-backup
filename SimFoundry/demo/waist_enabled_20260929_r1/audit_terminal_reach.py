from pathlib import Path
import ast,json,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent
urdf=root.parents[1]/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'
xml=ET.parse(urdf).getroot();bychild={j.find('child').get('link'):j for j in xml.findall('joint')}
src=ast.parse((root/'audit_hand_mesh_contact.py').read_text());exec(compile(ast.Module(body=[n for n in src.body if isinstance(n,ast.FunctionDef) and n.name in ['chain','matrix']],type_ignores=[]),'<validated_fk>','exec'))
# Cache the fixed transforms to speed pure CPU finite-difference IK.
chains={}
for side in ['left','right']:
 rows=[]
 for j in chain(side):
  origin=j.find('origin');m=np.eye(4)
  if origin is not None:m[:3,3]=np.fromstring(origin.get('xyz','0 0 0'),sep=' ');m[:3,:3]=Rotation.from_euler('xyz',np.fromstring(origin.get('rpy','0 0 0'),sep=' ')).as_matrix()
  axis=np.fromstring(j.find('axis').get('xyz'),sep=' ') if j.get('type') in ['revolute','continuous'] else None
  rows.append((j.get('name'),m,axis))
 chains[side]=rows
def palm(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,orig,axis in chains[side]:
  m=m@orig
  if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
 return (m@np.array([.20,0,.007,1]))[:3]
names=['waist_yaw_joint']+[f'{s}_{j}_joint' for s in ['left','right'] for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']]
lo=[];hi=[]
for name in names:
 j=next(j for j in xml.findall('joint') if j.get('name')==name);lo.append(float(j.find('limit').get('lower')));hi.append(float(j.find('limit').get('upper')))
lo=np.array(lo);hi=np.array(hi);lo[0]=-.63;hi[0]=.63
p=root/'contact_x_ablation_r1/uncapped/layout_62004_nudge_mailer_to_bin'
with np.load(p/'raw.npz') as z:initial=z['q'][-1,12:23].copy()
anchor=palm('right',dict(zip(names,np.zeros(11))));anchor[0]-=.10;anchor[1]-=.08
results=[];rng=np.random.default_rng(930)
for target in [[.60,.15,.84],[.60,.23,.84],[.55,.23,.84],[.52,.30,.84]]:
 for coupled in [False,True]:
  target=np.array(target)
  def residual(q):
   d=dict(zip(names,q));r=palm('left',d)-target
   return np.r_[r,palm('right',d)-anchor] if coupled else r
  best=None
  for q in [initial,np.zeros(11),*rng.uniform(lo,hi,(5,11))]:
   fit=least_squares(residual,np.clip(q,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=180);err=float(np.linalg.norm(fit.fun))
   if best is None or err<best['total_error_m']:best=dict(total_error_m=err,active_error_m=float(np.linalg.norm(fit.fun[:3])),inactive_error_m=float(np.linalg.norm(fit.fun[3:])),q=fit.x.tolist(),actual_palm=palm('left',dict(zip(names,fit.x))).tolist())
  results.append(dict(target=target.tolist(),coupled=coupled,best=best))
result=dict(rows=results,waist_limit_rad=.63,scope='Offline bounded multistart position-only IK. No orientation, collision, dynamics or camera constraints. Failure is not a proof of global infeasibility. Do not execute solved joint poses directly.',training_ready=False)
(root/'TERMINAL_REACH_AUDIT.json').write_text(json.dumps(result,indent=2))
for r in results:print(r['target'],r['coupled'],r['best']['active_error_m'],r['best']['inactive_error_m'])
