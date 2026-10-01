"""Independent rotated visual envelopes at the first initial-top guard."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw
p=Path(sys.argv[1]).resolve();fr=json.loads((p/'frontal_bypass.json').read_text())['rows'];first=next(r for r in fr if r.get('route_stop_reason'));t=first['step'];key='mailer' if 'nudge_mailer' in p.name else 'box';other='box' if key=='mailer' else 'mailer';size=np.array([.15,.145,.04] if key=='mailer' else [.14,.09,.045]);other_size=np.array([.14,.09,.045] if key=='mailer' else [.15,.145,.04]);frames=sorted(set([0,max(0,t-185),max(0,t-105),max(0,t-55),t-1,t,min(t+75,1199),1199]));rows=[]
with np.load(p/'trace.npz') as tr,np.load(p/'parcel_orientation.npz') as ori:
 initial_x=float(tr[key][0,0]);away=-1 if initial_x<tr[other][0,0] else 1
 for f in frames:
  target=tr[key][f].astype(float);obstacle=tr[other][f].astype(float);rot=Rotation.from_quat(ori[key][f]).as_matrix();other_rot=Rotation.from_quat(ori[other][f]).as_matrix();r=np.abs(rot)@size/2;ro=np.abs(other_rot)@other_size/2;boundary=obstacle[0]+away*(r[0]+ro[0]+.024);goal=min(initial_x,boundary) if away<0 else max(initial_x,boundary);margin=min(goal-r[0]-.28,.88-goal-r[0]);actualmargin=min(target[0]-r[0]-.28,.88-target[0]-r[0]);xgap=away*(target[0]-obstacle[0])-r[0]-ro[0]
  feasible_maxgap=obstacle[0]-ro[0]-(.28+2*r[0]+.005) if away<0 else .88-2*r[0]-.005-obstacle[0]-ro[0]
  rows.append(dict(frame=f,yaw_rad=float(math.atan2(rot[1,0],rot[0,0])),target_half_extents=r.tolist(),actual_x_table_margin_m=float(actualmargin),actual_x_object_gap_m=float(xgap),planned_x_24mm=float(goal),planned_table_margin_m=float(margin),max_feasible_xgap_at_5mm_table_margin_m=float(feasible_maxgap),target=target.tolist()))
 assert rows[frames.index(t)]['planned_table_margin_m']<.005
with np.load(p/'raw.npz') as z:
 rgb=z['rgb'];canvas=Image.new('RGB',(1280,530));d=ImageDraw.Draw(canvas)
 for i,f in enumerate(frames):
  canvas.paste(Image.fromarray(rgb[f].transpose(1,2,0)).resize((320,240)),(i%4*320,i//4*265));d.text((i%4*320,i//4*265+242),f'frame {f}')
 canvas.save(p/'CORRIDOR_GUARD_EVENT_REVIEW.jpg')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();result=dict(first_guard=first,independent_geometry=rows,raw_sha256=sha(p/'raw.npz'),image_sha256=sha(p/'CORRIDOR_GUARD_EVENT_REVIEW.jpg'),sampled_rgb_frames=frames,actual_visual_review='pending',scope='Independent scipy rotation/AABB recomputation. Prospective24mm X corridor becomes too narrow as target rotates; actual current position may still meet table/object gates. No proof that a smaller/adaptive margin or orientation control succeeds; original gates unchanged.',training_ready=False);(p/'CORRIDOR_GUARD_DIAGNOSIS.json').write_text(json.dumps(result,indent=2));print(json.dumps(rows,indent=2))
