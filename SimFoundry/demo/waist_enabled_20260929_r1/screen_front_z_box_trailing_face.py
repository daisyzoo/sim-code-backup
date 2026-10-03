"""Static trailing-side face search at four real post-clearance states.
No simulation, commands, force injection, trajectory or training admission.
"""
from pathlib import Path
import json,sys,hashlib,ast,argparse
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
args=argparse.Namespace(waist_bound=.98)
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w/'staged_front_corridor_midpoint_integrated'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();assert args.waist_bound<=min(-lo[0],hi[0]);lo[0]=-args.waist_bound;hi[0]=args.waist_bound;out=w/'front_z_box_trailing_face_static_r1';out.mkdir(exist_ok=False);reports=[];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
from clearance_runtime import ClearanceGuard
guard=ClearanceGuard(repo,w/'staged_front_corridor_midpoint_integrated')
def sat(vertices,normals,edges,center,rotation,half):
 v=(vertices-center)@rotation;ns=normals@rotation;es=edges@rotation;axes=np.concatenate([ns,np.eye(3)]+[np.cross(es,k) for k in np.eye(3)]);length=np.linalg.norm(axes,axis=1);axes=axes[length>1e-8]/length[length>1e-8,None];project=v@axes.T;radius=abs(axes)@half;return float(np.maximum(project.min(axis=0)-radius,-radius-project.max(axis=0)).max())
for cid,task in [(840020,'push_box_to_bin')]:
 ep=w/f'front_z_priority_physical_r1/case_{cid}/layout_{cid}_{task}';key='box' if 'push_box' in task else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';inactive='left' if side=='right' else 'right';direction=-1 if key=='box' else 1;fr=json.loads((ep/'frontal_bypass.json').read_text());selected=next((r for r in fr['rows'] if r.get('route_stage')=='lateral_y' and r['mode']=='top_push'),None)
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
 tangent_axis=1-axis;region_lo=np.array([-half[tangent_axis]+.01,-half[2]+.005]);region_hi=-region_lo;assert np.all(region_lo<region_hi)
 search_lo=np.r_[lo,region_lo];search_hi=np.r_[hi,region_hi];seeds=[np.r_[v,0.,.003] for v in seeds]
 for face in chosen:
  lp=centers[face];ln=normals[face]
  def calc(variables):
   q=variables[:11]
   T,_,_=model.fk(side,q);I,_,_=model.fk(inactive,q);R=T[:3,:3];v=verts@R.T+T[:3,3];point=R@lp+T[:3,3];normal=R@ln;pi=I[:3,3]+I[:3,:3]@np.array([.2,0,.007]);return T,R,v,point,normal,pi
  def face_goal(variables):
   local=np.zeros(3);local[axis]=sign*(half[axis]+.002);local[tangent_axis]=variables[11];local[2]=variables[12];return center+rot@local
  def residual(q):
   T,R,v,point,normal,pi=calc(q);return np.r_[point-face_goal(q),.015*(normal+n),20*max(0,.7462-v[:,2].min()),pi-ipalm,.0001*(q[:11]-qref),20*np.maximum(.005-guard.geometry.constraints(q[:11]),0)]
  for si,seed in enumerate(seeds):
   fit=least_squares(residual,seed,bounds=(search_lo,search_hi),max_nfev=220,ftol=1e-8,xtol=1e-8,gtol=1e-8);T,R,v,point,normal,pi=calc(fit.x);actual_goal=face_goal(fit.x);error=float(np.linalg.norm(point-actual_goal));angle=float(np.arccos(np.clip(normal@(-n),-1,1)));low=float(v[:,2].min());inactive_error=float(np.linalg.norm(pi-ipalm));gaps=None
   if error<=.003 and angle<=np.deg2rad(20) and low>=.7459 and inactive_error<=.002:gaps={key:sat(v,normals@R.T,edges@R.T,center,rot,half),other:sat(v,normals@R.T,edges@R.T,ocenter,orot,osize/2)}
   elbows=guard.geometry.constraints(fit.x[:11]);inactive_pose=guard.model.fk(inactive,fit.x[:11])[0];inactive_vertices=guard.model.vertices[inactive]@inactive_pose[:3,:3].T+inactive_pose[:3,3];palm=point-R@lp+R@np.array([.2,0,.007]);original_palm_table_margin=float(min(palm[2],pi[2])-.049-.746)
   ok=gaps is not None and gaps[key]>=.001 and gaps[other]>=.005 and min(elbows)>=.005-2e-7 and inactive_vertices[:,2].min()>=.746 and original_palm_table_margin>=0
   attempts.append(dict(face_id=face,seed=si,q=fit.x[:11].tolist(),face_region_coordinates_m=fit.x[11:].tolist(),goal=actual_goal.tolist(),solver_success=bool(fit.success),position_error_m=error,normal_error_rad=angle,hand_min_z_m=low,inactive_palm_error_m=inactive_error,sat_gaps_m=gaps,static_candidate=bool(ok),elbow_gaps_m=elbows.tolist(),inactive_hand_min_z_m=float(inactive_vertices[:,2].min()),original_palm_table_margin_m=original_palm_table_margin,evaluations=fit.nfev))
 attempts.sort(key=lambda r:(not r['static_candidate'],r['position_error_m']+.05*r['normal_error_rad']+4*max(0,.746-r['hand_min_z_m'])+r['inactive_palm_error_m']))
 row=dict(waist_bound_rad=args.waist_bound,face_region_lower_m=region_lo.tolist(),face_region_upper_m=region_hi.tolist(),episode=str(ep),actual_frame=t,actual_stage=selected.get('route_stage','rear_handover'),core_scale=scale.tolist(),goal=goal.tolist(),object_outward_normal=n.tolist(),fk_palm_error_m=fk_error,attempts=attempts,static_candidates=sum(r['static_candidate'] for r in attempts),source_sha256={f:sha(ep/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']});reports.append(row)
 (out/'RESULT.json').write_text(json.dumps(dict(rows=reports,complete=len(reports)==1,source_sha256={str(p):sha(p) for p in [Path(__file__),w/'staged_front_corridor_midpoint_integrated/articulated_hand_geometry.py',w/'staged_front_corridor_midpoint_integrated/clearance_runtime.py',w/'staged_front_corridor_midpoint_integrated/self_clearance.py',w/'staged_front_corridor_midpoint_integrated/elbow_torso_hulls.json',repo/'assets/robots/g1_hand_support_vertices.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']},scope='Bounded static diagnostic on new failed box at first actual lateral_y top_push. Original0.98rad waist only; same48-or-fewer facet/seed attempts and220 evaluations. Retain original balanced residual and add original5mm elbow penalty/check, both-palm table criterion and inactive-hand table check. Stricter positive1mm target precontact SAT gap replaces old minus1mm overlap eligibility. Other-object5mm, point3mm, face20deg, inactive palm2mm remain. No contact, unload path, full arm sweep, tracking uncertainty, dynamics, instruction policy or training proof. Local search failure is not impossibility. This one-condition diagnostic does not replace any full comparison group.',training_ready=False),indent=2));print(json.dumps(dict(episode=ep.name,frame=t,candidates=row['static_candidates'],attempts=len(attempts),best=attempts[0])),flush=True)
