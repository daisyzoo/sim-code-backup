import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from simfoundry.data.search_reward import terminal_search_scores
root=Path(sys.argv[1]);rows=[]
for ep in sorted(root.glob('layout_*')):
 if not (ep/'raw.npz').exists():continue
 report=json.loads((ep/'quality.json').read_text())
 with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr:
  q=z['q'];a=z['action'];rgb=z['rgb'];task=0 if 'push_box' in ep.name else 1
  fit=[{'verified':False,'reason':'object orientation was not recorded in historical locked expert path'}]
  if (ep/'parcel_orientation.npz').exists():
   with np.load(ep/'parcel_orientation.npz') as ori:
    _,fit=terminal_search_scores([report],[task],{k:tr[k][:,None] for k in tr.files},{k:ori[k][:,None] for k in ori.files})
  inactive='palm_left' if task==0 else 'palm_right'
  detail=dict(episode=ep.name,quality=report,pose=fit[0],inactive_palm_max_displacement_m=float(np.linalg.norm(tr[inactive]-tr[inactive][0],axis=1).max()))
  times=[0,30,60,90,120,len(q)-1]
  canvas=Image.new('RGB',(960,500))
  for i,t in enumerate(times):
   frame=Image.fromarray(rgb[t].transpose(1,2,0)).resize((320,240));xy=((i%3)*320,(i//3)*250);canvas.paste(frame,xy);ImageDraw.Draw(canvas).text((xy[0],xy[1]+240),f'{t} yaw {q[t,12]:.3f}',fill='white')
  canvas.save(ep/'review_six_frames.jpg');rows.append(detail)
(root/'POSE_AND_MOTION_REVIEW.json').write_text(json.dumps(dict(rows=rows,visual_review='pending_actual_view',training_ready=False),indent=2));print(json.dumps([dict(ep=r['episode'],pose=r['pose'],inactive_drift=r['inactive_palm_max_displacement_m']) for r in rows]))
