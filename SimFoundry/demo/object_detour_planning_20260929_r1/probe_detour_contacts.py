#!/usr/bin/env python3
"""Point IK screening of illustrative contact centers on object detours.
These contact centers are hypotheses, not certified mesh contacts.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from probe_sorting_kinematics import ArmFK
p=argparse.ArgumentParser();p.add_argument('--routes',type=Path,required=True);p.add_argument('--raw-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
models={side:ArmFK(side) for side in ['left','right']};errors=[];hashes={}
for raw in sorted(a.raw_root.glob('case_*/layout_*/raw.npz')):
 hashes[str(raw)]=hashlib.sha256(raw.read_bytes()).hexdigest()
 with np.load(raw) as z,np.load(raw.parent/'trace.npz') as tr:
  for side,start in [('left',13),('right',18)]:
   for frame in [0,30,60,90,120,159]:errors.append(float(np.linalg.norm(models[side].palm(z['q'][frame,start:start+5],z['q'][frame,12])-tr['palm_'+side][frame])))
assert len(errors)==96 and max(errors)<1e-4
routes=json.loads(a.routes.read_text());rng=np.random.default_rng(2026092905);rows=[]
for row in routes['rows']:
 model=models[row['arm']];lo,hi=np.array(model.bounds).T;z=.84 if row['arm']=='left' else .845;direction=1 if row['arm']=='left' else -1
 for lane,path in row['best_by_side'].items():
  if path is None:continue
  start,middle,end=np.array(path['waypoints']);xsign=np.sign(middle[0]-start[0]);goals=[]
  for fraction in [0,.5,1]:
   xy=start+fraction*(middle-start);goals.append((f'x_push_{fraction}',np.array([xy[0]-xsign*.06,xy[1],z])))
  for fraction in [0,.5,1]:
   xy=middle+fraction*(end-middle);goals.append((f'y_push_{fraction}',np.array([xy[0],xy[1]-direction*.06,z])))
  previous=np.zeros(5);points=[]
  for name,goal in goals:
   best=None
   for q0 in [previous,np.zeros(5)]+[rng.uniform(lo,hi) for _ in range(3)]:
    sol=least_squares(lambda q:model.palm(q)-goal,np.clip(q0,lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=300,gtol=1e-9,ftol=1e-9,xtol=1e-9);err=float(np.linalg.norm(sol.fun))
    if best is None or err<best['error_m']:best=dict(name=name,goal=goal.tolist(),q=sol.x.tolist(),error_m=err,palm=model.palm(sol.x).tolist())
   previous=np.array(best['q']);points.append(best)
  result=dict(layout_id=row['layout_id'],target=row['target'],lane=lane,points=points,max_error_m=max(x['error_m'] for x in points));rows.append(result);print(result['layout_id'],result['target'],lane,'max_point_error',result['max_error_m'],flush=True)
a.out.write_text(json.dumps(dict(fk_samples=len(errors),fk_max_error_m=max(errors),raw_hashes=hashes,routes_sha256=hashlib.sha256(a.routes.read_bytes()).hexdigest(),rows=rows,contact_hypothesis='Palm center60mm behind object center along push direction, Z .84/.845; does not establish actual rubber mesh contact. Fixed object yaw assumed in prior planner.',limits='Five-start point IK under URDF limits, no self/table/parcel collision, contact orientation, continuous path, effort or dynamics. Residuals only screen these particular points, not global task feasibility. No demonstrated trajectory or training admission.',training_ready=False,goal_complete=False),indent=2))
