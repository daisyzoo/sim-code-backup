"""Exact projected-shell witness for the observed fixed-orientation front barrier.
The target and obstacle are not moved. Configuration-space polygons describe
hypothetical center translation only. This is neither3D collision certification
nor global infeasibility: changed orientation and rear routes remain possible.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();signs=np.array([[x,y,z] for x in [-1,1] for y in [-1,1] for z in [-1,1]]);results=[];sources={}
for run in ['front_corridor_midpoint_physical_r1','front_drive_1mm_physical_r1']:
 root=W/run;ep=root/'case_840023/layout_840023_nudge_mailer_to_bin';diagnosis=json.loads((root/'BAG_CORRIDOR_ROTATION_LOSS_DIAGNOSTIC.json').read_text());step=diagnosis['first_guard_step'];fr=json.loads((ep/'frontal_bypass.json').read_text());row=next(x for x in fr['rows'] if x['step']==step);assert row['route_stop_reason']=='front_corridor_no_table_margin'
 with np.load(ep/'trace.npz') as z:target=z['mailer'][step].astype(float);obstacle=z['box'][step].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:target_offsets=(signs*np.array([.15,.145,.04])/2)@Rotation.from_quat(z['mailer'][step]).as_matrix().T;other_offsets=(signs*np.array([.14,.09,.045])/2)@Rotation.from_quat(z['box'][step]).as_matrix().T
 ti=int(np.argmax(target_offsets[:,0]));oi=int(np.argmin(other_offsets[:,0]));radius=float(np.max(abs(target_offsets[:,0])));lo=.28+.005+radius;hi=.88-.005-radius;clearance=.012
 cloud=(obstacle[None,None,:2]+other_offsets[:,None,:2]-target_offsets[None,:,:2]).reshape(-1,2);hull=ConvexHull(cloud);polygon=cloud[hull.vertices];vertex=obstacle[:2]+other_offsets[oi,:2]-target_offsets[ti,:2];np.testing.assert_allclose(vertex[0],cloud[:,0].min(),atol=1e-14,rtol=0)
 goal_y=fr['plan']['front_route_candidates']['goal_y'];critical_y=float(vertex[1]);assert target[1]<critical_y<goal_y
 # At this centerY, a real vertex of each projected shell has the same Y.
 hypothetical_center=np.array([lo,critical_y]);target_vertex=hypothetical_center+target_offsets[ti,:2];other_vertex=obstacle[:2]+other_offsets[oi,:2];np.testing.assert_allclose(target_vertex[1],other_vertex[1],atol=1e-14,rtol=0)
 bridge=float(other_vertex[0]-target_vertex[0]);assert 0<bridge<clearance
 np.testing.assert_allclose(bridge-clearance,row['front_corridor_midpoint']['safe_interval_x'][1]-row['front_corridor_midpoint']['safe_interval_x'][0],atol=1e-12,rtol=0)
 intersections=[]
 for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
  if abs(b[1]-a[1])<1e-14:
   if abs(a[1]-critical_y)<1e-12:intersections.extend([float(a[0]),float(b[0])])
  else:
   fraction=(critical_y-a[1])/(b[1]-a[1])
   if -1e-12<=fraction<=1+1e-12:intersections.append(float(a[0]+np.clip(fraction,0,1)*(b[0]-a[0])))
 assert len(intersections)>=2;left,right=min(intersections),max(intersections);np.testing.assert_allclose(left,vertex[0],atol=1e-12,rtol=0)
 # This whole center-X interval lies within12mm of a horizontal polygon
 # slice, so is forbidden under the original projected-shell12mm clearance.
 forbidden=[left-clearance,right+clearance];assert forbidden[0]<lo<forbidden[1]
 result=dict(run=run,observed_step=step,observed_target_center=target.tolist(),fixed_target_yaw_deg=float(Rotation.from_matrix(Rotation.from_quat(np.load(ep/'parcel_orientation.npz')['mailer'][step]).as_matrix()).as_euler('xyz',degrees=True)[2]),required_clearance_m=clearance,required_table_margin_m=.005,admissible_center_x=[lo,hi],critical_crossing_y=critical_y,task_goal_y=goal_y,configuration_polygon_xy=polygon.tolist(),horizontal_slice_x=[left,right],guaranteed_forbidden_center_x_at_critical_y=forbidden,projected_vertex_witness=dict(target_vertex_index=ti,obstacle_vertex_index=oi,target_vertex_xy=target_vertex.tolist(),obstacle_vertex_xy=other_vertex.tolist(),gap_upper_bound_m=bridge,clearance_deficit_m=clearance-bridge),front_translation_at_current_orientation_certifiably_blocked=True,rear_route_or_orientation_change_not_ruled_out=True)
 results.append(result)
 for p in [root/'BAG_CORRIDOR_ROTATION_LOSS_DIAGNOSTIC.json',ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'raw.npz']:sources[str(p)]=sha(p)
sources[str(Path(__file__))]=sha(__file__);out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=results,source_sha256=sources,physics_changed=False,quality_thresholds_changed=False,training_ready=False)
with (W/'front_drive_1mm_physical_r1/FRONT_BAG_FIXED_YAW_BARRIER.json').open('x') as f:json.dump(out,f,indent=2)
print([dict(run=x['run'],step=x['observed_step'],critical_y=x['critical_crossing_y'],gap_mm=x['projected_vertex_witness']['gap_upper_bound_m']*1000,deficit_mm=x['projected_vertex_witness']['clearance_deficit_m']*1000) for x in results])
