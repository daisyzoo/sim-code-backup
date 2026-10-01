"""Static trailing-side face search at four real post-clearance states.
No simulation, commands, force injection, trajectory or training admission.
"""
from pathlib import Path
import json,sys,hashlib,ast
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w/'staged_front_cop_route_axis'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;out=w/'trailing_face_after_clearance_screen_r1';out.mkdir(exist_ok=False);reports=[];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sat(vertices,normals,edges,center,rotation,half):
 v=(vertices-center)@rotation;ns=normals@rotation;es=edges@rotation;axes=np.concatenate([ns,np.eye(3)]+[np.cross(es,k) for k in np.eye(3)]);length=np.linalg.norm(axes,axis=1);axes=axes[length>1e-8]/length[length>1e-8,None];project=v@axes.T;radius=abs(axes)@half;return float(np.maximum(project.min(axis=0)-radius,-radius-project.max(axis=0)).max())
for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin'),(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 ep=w/f'front_cop_route_axis_groups_r1/case_{cid}/layout_{cid}_{task}';key='box' if 'push_box' in task else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';inactive='left' if side=='right' else 'right';direction=-1 if key=='box' else 1;fr=json.loads((ep/'frontal_bypass.json').read_text());selected=next((r for r in fr['rows'] if r.get('route_stage')=='lateral_y'),None)
 if selected is None:selected=next(r for r in fr['rows'] if r.get('region_handover'))
 t=selected['step'];source=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';prov=json.loads((ep.parent/'provenance.json').read_text());assert sha(source)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets));assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'";scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=np.array([.15,.145,.04] if key=='box' else [.14,.09,.045]);half=size*scale/2
 with np.load(ep/'raw.npz') as z:qref=z['q'][t,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:center=z[key][t].astype(float);ocenter=z[other][t].astype(float);ipalm=z['palm_'+inactive][t].astype(float);apalm=z['palm_'+side][t].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key][t]).as_matrix();orot=Rotation.from_quat(z[other][t]).as_matrix()
 pose,_,_=model.fk(side,qref);fk_error=float(np.max(abs(pose[:3,3]+pose[:3,:3]@np.array([.2,0,.007])-apalm)));assert fk_error<2e-6
 wanted=np.array([0.,-direction,0.]);axis=int(np.argmax(abs(rot.T@wanted)));sign=1 if rot[:,axis]@wanted>=0 else -1;n=sign*rot[:,axis];assert axis in (0,1);goal=center+n*(half[axis]+.002);goal[2]+=min(.003,half[2]/3)
 pts=model.vertices[side];hull=ConvexHull(pts);verts=pts[hull.vertices];faces=pts[hull.simplices];normals=hull.equations[:,:3];centers=faces.mean(axis=1);areas=np.linalg.norm(np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]),axis=1)/2;edges=np.concatenate([faces[:,1]-faces[:,0],faces[:,2]-faces[:,1],faces[:,0]-faces[:,2]]);chosen=[]
 for i in np.argsort(-areas):
  if centers[i,0]<.12:continue
  if all(np.linalg.norm(centers[i]-centers[j])>.025 or normals[i]@normals[j]<.8 for j in chosen):chosen.append(int(i))
  if len(chosen)==16:break
 alt=qref.copy();begin=6 if side=='right' else 1;alt[begin:begin+5]+=np.array([-.2,.1,.5,.1,-.5]);alt[0]+=.2*direction;seeds=[np.clip(qref,lo+1e-8,hi-1e-8),np.clip(np.zeros(11),lo+1e-8,hi-1e-8),np.clip(alt,lo+1e-8,hi-1e-8)];attempts=[]
 for face in chosen:
  lp=centers[face];ln=normals[face]
  def calc(q):
   T,_,_=model.fk(side,q);I,_,_=model.fk(inactive,q);R=T[:3,:3];v=verts@R.T+T[:3,3];point=R@lp+T[:3,3];normal=R@ln;pi=I[:3,3]+I[:3,:3]@np.array([.2,0,.007]);return T,R,v,point,normal,pi
  def residual(q):
   T,R,v,point,normal,pi=calc(q);return np.r_[point-goal,.05*(normal+n),4*max(0,.746-v[:,2].min()),pi-ipalm,.0001*(q-qref)]
  for si,seed in enumerate(seeds):
   fit=least_squares(residual,seed,bounds=(lo,hi),max_nfev=180,ftol=1e-8,xtol=1e-8,gtol=1e-8);T,R,v,point,normal,pi=calc(fit.x);error=float(np.linalg.norm(point-goal));angle=float(np.arccos(np.clip(normal@(-n),-1,1)));low=float(v[:,2].min());inactive_error=float(np.linalg.norm(pi-ipalm));gaps=None
   if error<=.003 and angle<=np.deg2rad(20) and low>=.7459 and inactive_error<=.002:gaps={key:sat(v,normals@R.T,edges@R.T,center,rot,half),other:sat(v,normals@R.T,edges@R.T,ocenter,orot,osize/2)}
   ok=gaps is not None and gaps[key]>=-.001 and gaps[other]>=.005
   attempts.append(dict(face_id=face,seed=si,q=fit.x.tolist(),solver_success=bool(fit.success),position_error_m=error,normal_error_rad=angle,hand_min_z_m=low,inactive_palm_error_m=inactive_error,sat_gaps_m=gaps,static_candidate=bool(ok),evaluations=fit.nfev))
 attempts.sort(key=lambda r:(not r['static_candidate'],r['position_error_m']+.05*r['normal_error_rad']+4*max(0,.746-r['hand_min_z_m'])+r['inactive_palm_error_m']))
 row=dict(episode=str(ep),actual_frame=t,actual_stage=selected.get('route_stage','rear_handover'),core_scale=scale.tolist(),goal=goal.tolist(),object_outward_normal=n.tolist(),fk_palm_error_m=fk_error,attempts=attempts,static_candidates=sum(r['static_candidate'] for r in attempts),source_sha256={f:sha(ep/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']});reports.append(row)
 (out/'RESULT.json').write_text(json.dumps(dict(rows=reports,complete=len(reports)==4,source_sha256={str(p):sha(p) for p in [Path(__file__),w/'staged_front_cop_route_axis/articulated_hand_geometry.py',repo/'assets/robots/g1_hand_support_vertices.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']},scope='Actual post-clearance state, trailing object-local side aligned with task direction, core dimensions from archived generator. Waist and both arms within existing working bounds; parked inactive palm preserved. Selected distal hull facets,3 seeds. Static only: no swept trajectory, arm/self collisions, new physical load or success. Failure is local-search evidence, not global infeasibility. All4conditions retained.',training_ready=False),indent=2));print(json.dumps(dict(episode=ep.name,frame=t,candidates=row['static_candidates'],attempts=len(attempts),best=attempts[0])),flush=True)
