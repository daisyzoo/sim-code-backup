"""Static yaw-sensitivity of nominal front/rear corridors; no control changes."""
from pathlib import Path
import json,math,hashlib
import numpy as np
root=Path(__file__).resolve().parent;rows=[]
angles=np.linspace(-math.pi/2,math.pi/2,36001)
for identifier in range(62000,62016):
 p=root/f'development_layouts/{identifier}.json';d=json.loads(p.read_text())
 for key,size,other,osize in [('mailer',(.15,.145),'box',(.14,.09)),('box',(.14,.09),'mailer',(.15,.145))]:
  ox=d[other+'_xyz'][0];oyaw=d[other+'_yaw'];other_radius=(abs(math.cos(oyaw))*osize[0]+abs(math.sin(oyaw))*osize[1])/2
  radius=(np.abs(np.cos(angles))*size[0]+np.abs(np.sin(angles))*size[1])/2
  # Original clearance12mm, lead3mm, original tableguard5mm; flat yaw only.
  front_margin=ox-other_radius-2*radius-.012-.003-.28
  rear_margin=.88-(ox+other_radius+2*radius+.012+.003)
  initial_yaw=d[key+'_yaw'];i=int(np.argmin(abs(angles-initial_yaw)));ok=front_margin>=.005;lo=hi=i
  if ok[i]:
   while lo>0 and ok[lo-1]:lo-=1
   while hi<len(ok)-1 and ok[hi+1]:hi+=1
  rows.append(dict(layout_id=identifier,target=key,initial_yaw_deg=math.degrees(initial_yaw),front_initial_planned_margin_m=float(front_margin[i]),front_local_allowed_yaw_interval_deg=[float(np.degrees(angles[lo])),float(np.degrees(angles[hi]))] if ok[i] else None,front_positive_yaw_reserve_deg=float(np.degrees(angles[hi]-initial_yaw)) if ok[i] else None,worst_flat_yaw_front_margin_m=float(front_margin.min()),worst_flat_yaw_rear_margin_m=float(rear_margin.min()),rear_all_flat_yaw_table_margin_pass=bool(rear_margin.min()>=.005),layout_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
out=dict(rows=rows,angular_grid_deg=.005,scope='Static target flat-yaw envelope, other at frozen yaw. Includes nominal12mm parcel gap and3mm extra lead, compares original5mm table margin. Does not include route-X latch, actual trajectory, reachability, hand/arm geometry or physics; not a replacement route or quality proof. Complete32developmentconditions only, no heldout.',training_ready=False)
(root/'YAW_CORRIDOR_RESERVE.json').write_text(json.dumps(out,indent=2));print(json.dumps([r for r in rows if r['layout_id'] in (62008,62013)],indent=2))
