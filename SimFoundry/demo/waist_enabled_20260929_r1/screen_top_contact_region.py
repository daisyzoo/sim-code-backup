"""Independent top-region IK screen, no controller install or physical execution."""
from pathlib import Path
import sys,json,hashlib,zipfile
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
s=(w/'screen_lateral_camera_reach.py').read_text();exec(compile(s.split("run=root/'fresh_lateral_00_pilot_r1'")[0],'<validated FK and original camera>','exec'))
from simfoundry.data.projected_support_reference import projected_support_reference
ep=Path(sys.argv[1]).resolve();run=ep.parents[1];t=1199
side='right' if 'push_box_to_bin' in ep.name else 'left';inactive_side='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=(.14,.09,.045) if key=='box' else (.15,.145,.04);other_size=(.15,.145,.04) if key=='box' else (.14,.09,.045)
with np.load(ep/'raw.npz') as z:q0=z['q'][t,12:23].astype(float);intr=z['intrinsics']
with np.load(ep/'trace.npz') as z:tr={k:z[k][t] for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k][t] for k in z.files}
coord=json.loads((ep/'coordination.json').read_text())[-1];assert coord['step']==t and coord['contact_normal_tracking'] is None
anchor=np.array(coord['inactive_anchor']);verts=np.array(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);box_rotation=Rotation.from_quat(ori[key]).as_matrix();normal=box_rotation[:,2]
errors={side:float(np.linalg.norm(transform(side,q0)[:3,3]+transform(side,q0)[:3,:3]@np.array([.20,0,.007])-tr['palm_'+side])) for side in ['left','right']};assert max(errors.values())<.0001
# Actual lowest point must lie within original10mm-inset top rectangle, not at
# a preselected tangential point; no virtual hull center masquerades as contact.
half=np.array(size[:2])/2;inset=.010;region=half-inset
ys,fractions=camera_fraction(tr[key],ori[key],size,intr,640,480);allowed=np.flatnonzero(fractions>=.5);assert len(allowed)>1 and np.all(np.diff(allowed)==1);window=[float(ys[allowed[0]]),float(ys[allowed[-1]])]
def geometry(q):
 m=transform(side,q);r=m[:3,:3];ref=projected_support_reference(verts,r,normal);point=m[:3,3]+r@ref['lowest_vertex_local'];local=box_rotation.T@(point-tr[key]);mi=transform(inactive_side,q);pi=mi[:3,3]+mi[:3,:3]@np.array([.20,0,.007]);return m,point,local,pi,ref
rng=np.random.default_rng(2026093004);results=[]
for require_camera in [False,True]:
 lower=lo.copy();upper=hi.copy()
 if require_camera:lower[0],upper[0]=window
 starts=[q0,np.zeros(11),rng.uniform(lower,upper)]
 for clearance in [.004,0.]:
  target_z=size[2]/2+clearance
  def residual(q):
   m,p,local,pi,ref=geometry(q)
   violation=local[:2]-np.clip(local[:2],-region,region)
   return np.r_[violation,local[2]-target_z,pi-anchor]
  fits=[]
  for start_id,start in enumerate(starts):
   fit=least_squares(residual,np.clip(start,lower+1e-6,upper-1e-6),bounds=(lower,upper),max_nfev=500,ftol=1e-10,gtol=1e-10,xtol=1e-10)
   m,point,local,pi,ref=geometry(fit.x);gap=float(hand_face_separation(side).gap(m[:3,3],Rotation.from_matrix(m[:3,:3]).as_quat(),tr[other],ori[other],other_size));region_error=float(np.linalg.norm(local[:2]-np.clip(local[:2],-region,region)));zerror=float(abs(local[2]-target_z));inactive=float(np.linalg.norm(pi-anchor));min_z=float((verts@m[:3,:3].T+m[:3,3])[:,2].min())
   fits.append(dict(start=start_id,residual_norm_m=float(np.linalg.norm(fit.fun)),region_error_m=region_error,top_height_error_m=zerror,physical_lowest_point_local_target_xyz=local.tolist(),inactive_palm_error_m=inactive,hand_other_face_gap_m=gap,hand_min_world_z_m=min_z,waist_rad=float(fit.x[0]),projected_bbox_fraction=float(np.interp(fit.x[0],ys,fractions)),solver_success=bool(fit.success),nfev=fit.nfev,geometric_candidate=bool(region_error<.001 and zerror<.001 and inactive<.001 and gap>=.005 and min_z>=.746),q=fit.x.tolist(),support_index=int(ref['support_index'])))
  best=min(fits,key=lambda d:d['residual_norm_m']);result=dict(require_projected_bbox_half=require_camera,top_clearance_m=clearance,best=best,starts=fits);results.append(result);print(json.dumps({k:v for k,v in result.items() if k!='starts'}),flush=True)
report=dict(episode=ep.name,actual_frame=t,actual_fk_errors_m=errors,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),contact_region_half_extents_m=region.tolist(),camera_waist_window=window,rows=results,scope='Three-start static bounded IK allowing any actual lowest hand vertex inside original10mm-inset top region, original inactive palm anchor and joint/waist bounds. Optional half-bbox projection is a diagnostic comparison, not a new quality gate. Kinked support selection, local optimization only; failure not global impossibility. Candidate success is NOT forces/COP/friction, all-arm or swept collision, occlusion, continuous causal approach, stable pressing or task proof. No solved q is executed; current fresh collection unchanged.',training_ready=False)
(ep/'TOP_CONTACT_REGION_SCREEN.json').write_text(json.dumps(report,indent=2))
