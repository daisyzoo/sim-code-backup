#!/usr/bin/env python3
"""Exact fixed-yaw swept-footprint check for two-segment object translations.
No physics state is written; returned paths are not executable demonstrations.
"""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,MultiPoint,box
p=argparse.ArgumentParser();p.add_argument('--layouts',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--table-margin',type=float,default=.005);p.add_argument('--clearance',type=float,default=.01);a=p.parse_args()
assert 0 <= a.table_margin <= .02 and 0 <= a.clearance <= .02
a.out.mkdir(exist_ok=False,parents=True)
sizes={'box':(.14,.09),'mailer':(.15,.145)}
table=box(.28,-.75,.88,.75);supported=table.buffer(-a.table_margin,join_style=2)
def footprint(center,yaw,size):
 c,s=math.cos(yaw),math.sin(yaw);return Polygon([(center[0]+c*x-s*y,center[1]+s*x+c*y) for x,y in [(-size[0]/2,-size[1]/2),(size[0]/2,-size[1]/2),(size[0]/2,size[1]/2),(-size[0]/2,size[1]/2)]])
def segment(start,end,yaw,size,obstacle):
 first,last=footprint(start,yaw,size),footprint(end,yaw,size)
 swept=MultiPoint(list(first.exterior.coords)[:-1]+list(last.exterior.coords)[:-1]).convex_hull
 clearance=swept.distance(obstacle);inside=supported.covers(swept)
 return dict(clearance_m=clearance,full_support_with_requested_margin=inside,valid=inside and not swept.intersects(obstacle) and clearance>=a.clearance)
rows=[]
for lid in [66009,66010]:
 path=a.layouts/f'layout_{lid}.json';d=json.loads(path.read_text())
 for obj,sign in [('box',-1),('mailer',1)]:
  other='mailer' if obj=='box' else 'box';start=d[obj+'_xyz'][:2];yaw=d[obj+'_yaw'];obstacle=footprint(d[other+'_xyz'][:2],d[other+'_yaw'],sizes[other]);goal_y=sign*max(.23,sign*start[1]+.18)
  direct=segment(start,[start[0],goal_y],yaw,sizes[obj],obstacle);routes=[]
  for lane in np.arange(.28,.88001,.0005):
   middle=[float(lane),start[1]];end=[float(lane),goal_y];legs=[segment(start,middle,yaw,sizes[obj],obstacle),segment(middle,end,yaw,sizes[obj],obstacle)]
   if all(x['valid'] for x in legs):routes.append(dict(waypoints=[start,middle,end],route_side='front' if lane<d[other+'_xyz'][0] else 'back',first_motion='toward_robot' if lane<start[0] else 'away_from_robot',x_displacement_m=float(lane-start[0]),length_m=abs(lane-start[0])+abs(goal_y-start[1]),min_clearance_m=min(x['clearance_m'] for x in legs)))
  best={side:min([x for x in routes if x['route_side']==side],key=lambda x:x['length_m'],default=None) for side in ['front','back']}
  row=dict(layout_id=lid,target=obj,arm='right' if obj=='box' else 'left',layout_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),direct=direct,best_by_side=best,goal_y=goal_y,yaw=yaw,size=sizes[obj]);rows.append(row);print(lid,obj,{k:None if v is None else round(v['x_displacement_m'],4) for k,v in best.items()},flush=True)
result=dict(rows=rows,table_bounds=[.28,-.75,.88,.75],table_margin_m=a.table_margin,obstacle_clearance_m=a.clearance,lane_grid_m=.0005,method='Convex hull of rectangle footprints at segment endpoints equals continuous swept footprint for a fixed-yaw translation. Both segments checked against the fixed obstacle and inset tabletop. Lane grid may miss narrower routes.',limits='2D object-only geometry. Does not include raised tabletop lips, hand/arm collisions, reachable contact normals, friction, rotation control or dynamics. Neither found nor absent route proves physical feasibility/infeasibility. Not training data.',training_ready=False,goal_complete=False)
(a.out/'ROUTES.json').write_text(json.dumps(result,indent=2))
