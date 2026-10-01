"""Full11 joint multi-seed unloaded core-interior pose screen; no commands.
Uses four hard actual states and their causal q-minus-previous-command residual.
"""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w/'staged_front_cop_route_axis'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.data.hand_obstacle_clearance import ConvexFaceSeparation
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=w/'trailing_face_region_w098_screen_r1/RESULT.json';reference=json.loads(source.read_text());assert reference['complete']
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98
out=w/'core_top_global_pose_screen_r1';out.mkdir(exist_ok=False);rows=[]
for case in reference['rows']:
 ep=Path(case['episode']);t=case['actual_frame'];key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';inactive='left' if side=='right' else 'right';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=np.array([.15,.145,.04] if key=='box' else [.14,.09,.045]);half=size*np.array(case['core_scale'])/2;inner=half[:2]-.01
 for f,h in case['source_sha256'].items():assert sha(ep/f)==h
 with np.load(ep/'raw.npz') as z:qref=z['q'][t,12:23].astype(float);residual=qref-z['action'][t-1,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:center=z[key][t].astype(float);ocenter=z[other][t].astype(float);anchor=z['palm_'+inactive][t].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key][t]).as_matrix();orot=Rotation.from_quat(z[other][t]).as_matrix()
 pts=model.vertices[side];hull=ConvexHull(pts);verts=pts[hull.vertices];faces=pts[hull.simplices];normals=hull.equations[:,:3];centers=faces.mean(axis=1);areas=np.linalg.norm(np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]),axis=1)/2;separation=ConvexFaceSeparation(pts);chosen=[]
 for i in np.argsort(-areas):
  if centers[i,0]<.12:continue
  if all(np.linalg.norm(centers[i]-centers[j])>.025 or normals[i]@normals[j]<.8 for j in chosen):chosen.append(int(i))
  if len(chosen)==16:break
 searchlo=np.r_[lo,-inner];searchhi=np.r_[hi,inner];alter=qref.copy();begin=6 if side=='right' else 1;alter[begin:begin+5]+=np.array([-.2,.1,.5,.1,-.5]);seeds=[np.r_[np.clip(qref,lo+1e-8,hi-1e-8),0.,0.],np.r_[np.clip(np.zeros(11),lo+1e-8,hi-1e-8),0.,0.],np.r_[np.clip(alter,lo+1e-8,hi-1e-8),0.,0.]];attempts=[]
 def measure(q):
  T,_,_=model.fk(side,q);I,_,_=model.fk(inactive,q);v=verts@T[:3,:3].T+T[:3,3];local=(v-center)@rot;ip=I[:3,3]+I[:3,:3]@np.array([.2,0,.007]);return T,v,local,ip
 def check(q):
  T,v,local,ip=measure(q);height=float(local[:,2].min()-half[2]);near=local[local[:,2]<=local[:,2].min()+.0001,:2];margin=inner-np.max(abs(near),axis=0);gap=separation.gap(T[:3,3],Rotation.from_matrix(T[:3,:3]).as_quat(),ocenter,Rotation.from_matrix(orot).as_quat(),osize);inactive_error=float(np.linalg.norm(ip-anchor));ok=bool(.003<=height<=.005 and np.all(margin>=0) and gap>=.005 and v[:,2].min()>=.746 and inactive_error<=.002 and np.all(q>=lo) and np.all(q<=hi))
  return dict(unloaded_top_gap_m=height,core_interior_margin_m=margin.tolist(),other_face_separation_m=gap,hand_min_z_m=float(v[:,2].min()),inactive_palm_error_m=inactive_error,working_bounds=bool(np.all(q>=lo) and np.all(q<=hi)),geometric_candidate=ok)
 for face in chosen:
  lp=centers[face];ln=normals[face]
  def objective(x):
   T,v,local,ip=measure(x[:11]);point=T[:3,:3]@lp+T[:3,3];normal=T[:3,:3]@ln;goal=center+rot@np.r_[x[11:],half[2]+.004]
   return np.r_[point-goal,.025*(normal+rot[:,2]),4*max(0,half[2]+.004-local[:,2].min()),ip-anchor,.0001*(x[:11]-qref)]
  for si,seed in enumerate(seeds):
   fit=least_squares(objective,seed,bounds=(searchlo,searchhi),max_nfev=220,ftol=1e-8,xtol=1e-8,gtol=1e-8);q=fit.x[:11];nominal=check(q);predicted=check(q+residual);attempts.append(dict(face_id=face,seed=si,q=q.tolist(),region_xy_m=fit.x[11:].tolist(),solver_success=bool(fit.success),evaluations=fit.nfev,nominal=nominal,current_residual_prediction=predicted,nominal_and_predicted_candidate=nominal['geometric_candidate'] and predicted['geometric_candidate']))
 row=dict(episode=str(ep),actual_frame=t,actual_stage=case['actual_stage'],causal_residual_rad=residual.tolist(),core_half_m=half.tolist(),inset_half_m=inner.tolist(),attempts=attempts,nominal_candidates=sum(a['nominal']['geometric_candidate'] for a in attempts),nominal_and_predicted_candidates=sum(a['nominal_and_predicted_candidate'] for a in attempts),source_sha256=case['source_sha256']);rows.append(row)
 report=dict(complete=len(rows)==4,rows=rows,reference_sha256=sha(source),script_sha256=sha(__file__),geometry_source_sha256=model.source_sha256,scope='Static full11q global multi-seed face/region pose search at four measured hard states, existing0.98rad waist bound. Lowest hand support band within real core10mm inset, gap3..5mm, passive palm within2mm, other face-axis separation>=5mm. Measured q[t]-action[t-1] used only as held residual prediction at endpoints. Nominal optimisation and both response checks reported separately. No trajectory, full-arm/self collision, real response, force, physical restart or data admission. All failures retained; no global impossibility claim.',training_ready=False)
 (out/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:row[k] for k in ['episode','actual_frame','nominal_candidates','nominal_and_predicted_candidates']}),flush=True)
