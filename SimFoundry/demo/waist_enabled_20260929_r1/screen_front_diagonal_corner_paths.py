"""Exact fixed-orientation swept AABB screen of same front corridor corner path."""
from pathlib import Path
import json,hashlib,itertools
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
def min_axis_gap(a,b,obstacle,radii):
 # For fixed extents, max axis separation is max of four affine functions.
 v=b-a;intercept=np.r_[a-obstacle-radii,obstacle-a-radii];slope=np.r_[v,-v];times=[0.,1.]
 for i,j in itertools.combinations(range(4),2):
  if abs(slope[i]-slope[j])>1e-14:
   t=(intercept[j]-intercept[i])/(slope[i]-slope[j])
   if 0<t<1:times.append(t)
 return min(float(np.max(intercept+slope*t)) for t in times)
for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
 ep=w/'rear_core_slice_groups_r1'/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];key='box' if 'push_box' in task else 'mailer';other='mailer' if key=='box' else 'box';direction=plan['direction'];sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
 with np.load(ep/'trace.npz') as z:target=z[key].astype(float);obstacle=z[other].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
 ext={k:abs(rot[k])@(sizes[k]/2) for k in sizes};initial_route=next(c for c in plan['front_route_candidates']['candidates'] if c['route']=='front');fixed_x=initial_route['waypoints_xy'][1][0]-.003;goal_y=plan['front_route_candidates']['goal_y'];results=[]
 states=[dict(step=0,route_stage='front_x')]+[r for r in fr['rows'] if r['route_stage']=='front_x' and r['mode']=='top_push']
 for row in states:
  t=row['step'];a=target[t,:2];obs=obstacle[t,:2];sumr=ext[key][t,:2]+ext[other][t,:2];x=min(fixed_x,obs[0]-sumr[0]-.015);end=np.array([x,goal_y]);corner=np.array([x,obs[1]-direction*(sumr[1]+.015)]);parent=np.array([[*a],[x,a[1]],[*end]]);diagonal=np.array([[*a],[*corner],[*end]])
  if direction*(corner[1]-a[1])<0 or direction*(goal_y-corner[1])<0:continue
  def analyze(path):
   gaps=[min_axis_gap(x,y,obs,sumr) for x,y in zip(path,path[1:])];table=min(float(np.min(path[:,0]-ext[key][t,0]-.28)),float(np.min(.88-path[:,0]-ext[key][t,0])),float(np.min(path[:,1]-ext[key][t,1]+.75)),float(np.min(.75-path[:,1]-ext[key][t,1])))
   return dict(length_mm=float(np.linalg.norm(np.diff(path,axis=0),axis=1).sum()*1000),minimum_axis_gap_mm=min(gaps)*1000,table_margin_mm=table*1000,eligible=bool(min(gaps)>=.012-1e-10 and table>=.005-1e-10),waypoints_xy=path.tolist())
  old=analyze(parent);new=analyze(diagonal);assert new['minimum_axis_gap_mm']>=12-1e-8
  results.append(dict(step=t,parent=old,diagonal=new,static_path_reduction_mm=old['length_mm']-new['length_mm'],available_advance_before_corner_mm=direction*(corner[1]-a[1])*1000))
 report=dict(episode=ep.name,initial=results[0],recorded_front_push_poses_screened=len(results)-1,eligible_diagonal_snapshots=sum(r['diagonal']['eligible'] for r in results),snapshots=results,source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json']});reports.append(report);print(json.dumps({k:v for k,v in report.items() if k not in ['snapshots','source_sha256']}),flush=True)
out=dict(episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Exact four-affine-piece minimum axis separation along fixed-orientation center segments, endpoint table extrema. Same front corridor/goal and12mm parcel clearance/5mm table guard,15mm planned corner buffer. Current measured snapshots only. Does not satisfy old sequential front-clearance state machine or prove hand/arm clearance, IK, evolving orientation, contact dynamics or time-to-success; no controller/physics/data changes.')
p=w/'FRONT_DIAGONAL_CORNER_GEOMETRY_SCREEN.json';assert not p.exists();p.write_text(json.dumps(out,indent=2))
