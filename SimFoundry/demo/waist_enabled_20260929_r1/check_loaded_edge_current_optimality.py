"""Independent finite-difference stationarity of unexecuted loaded-edge proposals.
Original unscaled damped task gradient; normalized active constraint normals and
same1e-6 residual threshold. Feasibility is separately checked in the probe file.
This is NOT an audit of newly executed physical commands or training admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.optimize import nnls
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);elbows=IndependentElbows(w/'staged_recontact_pose/elbow_torso_hulls.json',urdf);probe=w/'LOADED_EDGE_CURRENT_CONTACT_CHECK.json';d=json.loads(probe.read_text());assert d['passed'];diag=json.loads((w/'LOADED_RELATIVE_CONTACT_MOTION.json').read_text());records=[];cache={}
for r in d['records']:
 if not r['override']:continue
 en=r['episode'];t=r['step'];side='right' if 'push_box' in en else 'left';key='box' if side=='right' else 'mailer';cid=840001 if side=='right' else 840004;direction=-1 if side=='right' else 1
 if en not in cache:
  ep=w/'recontact_pose_groups_r1'/f'case_{cid}'/en;fs={v['step']:v for v in json.loads((ep/'frontal_bypass.json').read_text())['rows']};cs={v['step']:v for v in json.loads((ep/'coordination.json').read_text())}
  with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
  dr=next(v for v in diag['rows'] if v['run']=='recontact_pose_groups_r1' and v['episode']==en);ds={v['step']:v for v in dr['records']};cache[en]=(fs,cs,R,ds)
 fs,cs,R,ds=cache[en];inp=cs[t]['task_inputs'];q=np.array(inp['current']);x=np.array(r['proposal']['command']);lo=np.array(r['proposal']['bound_low']);hi=np.array(r['proposal']['bound_high']);J=np.array(inp['jacobian']);E=np.array(inp['error']);damp=np.array(inp['damping']);offset=np.array(fs[t]['control_offset_local']);cop=np.array(ds[t]['cop_local_mm'])/1000;axes=r['proposal']['threatened_axes'];A=np.vstack([[-np.sign(cop[k])*R[t,:,k] for k in axes],[0,direction,0]])
 def point(q):T=hand.fk(q,side);return T[:3,3]+T[:3,:3]@offset
 def constraints(q):return np.r_[A@(point(q)-point(np.array(inp['current']))),elbows.gap(q)-.005]
 values=constraints(x);h=1e-5;G=np.column_stack([(constraints(x+np.eye(11)[i]*h)-constraints(x-np.eye(11)[i]*h))/(2*h) for i in range(11)]);normals=[G[i] for i in range(len(values)) if values[i]<=1e-6]
 for i in range(11):
  if x[i]-lo[i]<=2e-6:normals.append(np.eye(11)[i])
  if hi[i]-x[i]<=2e-6:normals.append(-np.eye(11)[i])
 gradient=J.T@(J@(x-q)-E)+damp*damp*(x-q)
 if normals:
  B=np.array(normals);n=np.linalg.norm(B,axis=1);B=B[n>1e-12]/n[n>1e-12,None];_,res=nnls(B.T,gradient,maxiter=1000)
 else:res=np.linalg.norm(gradient)
 records.append({'episode':en,'step':t,'residual':float(res),'stationary':bool(res<=1e-6),'active_constraint_count':len(normals)})
bad=[r for r in records if not r['stationary']];out={'passed':not bad,'scope':__doc__,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'threshold':1e-6,'commands':len(records),'max_residual':max(r['residual'] for r in records),'failures':bad,'records':records,'source_sha256':{str(p):sha(p) for p in [Path(__file__),probe,w/'LOADED_RELATIVE_CONTACT_MOTION.json',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',urdf,vertices,w/'staged_recontact_pose/elbow_torso_hulls.json']},'physical_validation':False,'training_ready':False};(w/'LOADED_EDGE_CURRENT_OPTIMALITY_CHECK.json').write_text(json.dumps(out,indent=2));print({k:out[k] for k in ['passed','commands','max_residual','failures']});sys.exit(0 if out['passed'] else 1)
