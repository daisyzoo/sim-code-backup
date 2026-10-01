"""Read-only initial in-place world-yaw rotation then original axis-aligned route.
Keeps original visual envelopes, 20mm planning clearance and 5mm table margin.
AABB separation only, no robot/contact/path execution or global infeasibility proof.
Rotation continuously certified between samples by radius-based Lipschitz margins.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.calibration.sorting_station import PARCEL_BOX_SIZE,MAILER_SIZE_XYH
from simfoundry.data.tabletop_route_candidates import tabletop_route_candidates,footprint_radii
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[];angles=np.arange(-90.,91.,1.)
for cid in [840000,840001,840004,840005]:
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ep=w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}';key='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1;size=np.array(PARCEL_BOX_SIZE if key=='box' else MAILER_SIZE_XYH);osize=np.array(MAILER_SIZE_XYH if key=='box' else PARCEL_BOX_SIZE)
  with np.load(ep/'trace.npz') as z:target=z[key][0].astype(float);obstacle=z[other][0].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:q=z[key][0].astype(float);oq=z[other][0].astype(float)
  r0=Rotation.from_quat(q);other_r=np.array(footprint_radii(osize,oq));radius=np.linalg.norm(size)/2;solutions=[]
  for angle in angles:
   samples=np.linspace(0,np.deg2rad(angle),max(1,int(abs(angle)*2))+1);rot_quats=[(Rotation.from_rotvec([0,0,a])*r0).as_quat() for a in samples];radii=np.array([footprint_radii(size,v) for v in rot_quats]);table=np.min(np.c_[target[0]-radii[:,0]-.28,.88-target[0]-radii[:,0],target[1]-radii[:,1]+.75,.75-target[1]-radii[:,1]],axis=1);separation=np.max(abs(target[:2]-obstacle[:2])-radii-other_r,axis=1)
   # Every intermediate orientation lies within half a sampling interval of a sample.
   # Each projected envelope radius is radius-Lipschitz under yaw.
   bound=radius*(abs(samples[1]-samples[0])/2 if len(samples)>1 else 0.)
   safe=bool(table.min()-bound>=.005 and separation.min()-bound>=.020)
   report=tabletop_route_candidates(target,obstacle,size,osize,rot_quats[-1],oq,direction,margin=.020)
   for route in report['candidates']:
    if safe and route['object_envelope_eligible'] and route['target_table_margin_m']>=.005:
     solutions.append(dict(rotation_deg=float(angle),route=route['route'],rotation_certified_table_margin_m=float(table.min()-bound),rotation_certified_object_gap_m=float(separation.min()-bound),rotation_lipschitz_allowance_m=float(bound),max_depth_x_m=max(v[0] for v in route['waypoints_xy']),**{k:v for k,v in route.items() if k!='route'}))
  best=min(solutions,key=lambda r:(r['max_depth_x_m'],r['object_path_length_m'],abs(r['rotation_deg']))) if solutions else None
  fronts=[r for r in solutions if r['route']=='front'];leastrot=min(fronts,key=lambda r:abs(r['rotation_deg'])) if fronts else None
  base=tabletop_route_candidates(target,obstacle,size,osize,q,oq,direction,margin=.020)
  row=dict(episode=ep.name,initial_target_xyz=target.tolist(),initial_other_xyz=obstacle.tolist(),baseline=base,feasible_candidate_count=len(solutions),best_depth=best,least_rotation_front=leastrot,all_candidates=solutions,source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json']});rows.append(row)
  print(ep.name,'solutions',len(solutions),'best',None if best is None else (best['route'],best['rotation_deg'],round(best['max_depth_x_m'],6)),'least_front_rotation',None if leastrot is None else leastrot['rotation_deg'],flush=True)
out=dict(scope=__doc__,rows=rows,checker_sha256=sha(Path(__file__)),source_sha256={str(p.relative_to(repo)):sha(p) for p in [repo/'simfoundry/data/tabletop_route_candidates.py',repo/'simfoundry/calibration/sorting_station.py']},training_ready=False,controller_wired=False,robot_feasibility_checked=False)
(w/'ROTATED_OBJECT_ROUTE_SCREEN_20MM.json').write_text(json.dumps(out,indent=2))
