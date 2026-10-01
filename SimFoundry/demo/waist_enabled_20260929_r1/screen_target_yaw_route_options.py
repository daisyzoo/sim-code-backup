"""Hypothetical target-yaw routes; never apply parcel poses to simulation."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for cid,task in [(840001,'push_box_to_bin'),(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 ep=w/'rear_cop_measured_bounds_groups_r1'/f'case_{cid}/layout_{cid}_{task}';src=json.loads((ep.parent/'provenance.json').read_text())['source_sha256'];name='simfoundry/data/tabletop_route_candidates.py';p=ep.parent/'source_snapshot'/name;assert sha(p)==src[name];spec=importlib.util.spec_from_file_location('yaw_routes',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);key='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1;size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=np.array([.14,.09,.045] if other=='box' else [.15,.145,.04])
 with np.load(ep/'trace.npz') as z:target=z[key][0].astype(float);obstacle=z[other][0].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:initialq=z[key][0].astype(float);oq=z[other][0].astype(float)
 initial=Rotation.from_quat(initialq);yaw0=initial.as_euler('xyz')[2];orr=np.array(m.footprint_radii(osize,oq));rows=[];radius=float(np.linalg.norm(size)/2)
 for yaw in [yaw0,0.,np.pi/2,-np.pi/2]:
  delta=float((yaw-yaw0+np.pi)%(2*np.pi)-np.pi);count=max(2,int(np.ceil(abs(delta)/(np.pi/180)))+1);samples=np.linspace(0,delta,count);step=abs(delta)/(count-1);gaps=[];tables=[]
  for a in samples:
   quat=(Rotation.from_euler('z',a)*initial).as_quat();rad=np.array(m.footprint_radii(size,quat));gaps.append(float(np.max(abs(target[:2]-obstacle[:2])-rad-orr)));tables.append(float(min(target[0]-.28-rad[0],.88-target[0]-rad[0],target[1]+.75-rad[1],.75-target[1]-rad[1])))
  interpolation_bound=radius*step/2;rotation_gap=min(gaps)-interpolation_bound;rotation_table=min(tables)-interpolation_bound;finalq=(Rotation.from_euler('z',delta)*initial).as_quat()
  for margin in [.012,.02]:
   candidates=m.tabletop_route_candidates(target,obstacle,size,osize,finalq,oq,direction,margin=margin);row=dict(requested_world_yaw_rad=float(yaw),yaw_delta_rad=delta,margin_m=margin,initial_center_yaw_sweep_object_separation_lower_bound_m=rotation_gap,initial_center_yaw_sweep_table_margin_lower_bound_m=rotation_table,rotation_geometry_eligible=bool(rotation_gap>=margin and rotation_table>=0),rotation_samples=count,rotation_sample_interpolation_error_bound_m=interpolation_bound,route_result=candidates);rows.append(row)
   if margin==.02:print(ep.name,'yaw',round(yaw*180/np.pi,2),'rotationclear',row['rotation_geometry_eligible'],'routes',[(a['route'],a['object_envelope_eligible'],round(a['target_table_margin_m']*1000,2)) for a in candidates['candidates']],flush=True)
 reports.append(dict(episode=ep.name,initial_target_xyz=target.tolist(),obstacle_xyz=obstacle.tolist(),rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz']},archived_route_sha256=sha(p)))
p=w/'TARGET_YAW_ROUTE_GEOMETRY_SCREEN.json';assert not p.exists();p.write_text(json.dumps(dict(episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,controller_wired=False,physical_started=False,scope='Hypothetical target rotation in place followed by unchanged object-envelope route planner. Rotate initial orientation about world Z, never move simulated objects. Samples plus rigid-vertex angular displacement bound cover only parcel-parcel global-axis separation and table footprint during in-place yaw. No hand/arm reach, one-hand torque/contact, yaw execution, dynamics or training admission claim. Actual expert must physically rotate designated target without other-object drift before such geometry could be used.'),indent=2))
