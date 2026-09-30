"""Calibrated geometric image coverage, not segmentation or occlusion proof."""
from pathlib import Path
import json,itertools,ast,sys
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent
source=root.parents[1]/'simfoundry/calibration/sorting_station.py'
module=ast.parse(source.read_text());vals={}
for n in module.body:
 if isinstance(n,ast.Assign):
  for t in n.targets:
   if isinstance(t,ast.Name) and t.id in ['SORTING_D435I_POS','SORTING_D435I_ROT_XYZW']:vals[t.id]=ast.literal_eval(n.value)
Ropt=Rotation.from_quat(vals['SORTING_D435I_ROT_XYZW']).as_matrix();camoff=np.array(vals['SORTING_D435I_POS'])
input_path=Path(sys.argv[1])
paths=([input_path] if (input_path/'quality.json').exists() else
       sorted(p for p in input_path.glob('case_*/layout_*') if (p/'quality.json').exists()))
results=[]
for ep in paths:
 target='box' if 'push_box' in ep.name else 'mailer';half=np.array([.14,.09,.045] if target=='box' else [.15,.145,.04])/2
 corners=np.array(list(itertools.product([-1,1],repeat=3)))*half
 with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  fx,fy,cx,cy=z['intrinsics'];rgb=z['rgb'];q=z['q'];width=rgb.shape[3];height=rgb.shape[2];points=[];rows=[]
  for t,yaw in enumerate(q[:,12]):
   Rz=Rotation.from_euler('z',yaw).as_matrix();camera_position=np.array([.08-.0039635,0,.793+.044])+Rz@camoff;camera_rotation=Rz@Ropt
   world=corners@Rotation.from_quat(ori[target][t]).as_matrix().T+tr[target][t];cam=(world-camera_position)@camera_rotation
   uv=np.c_[fx*cam[:,0]/cam[:,2]+cx,fy*cam[:,1]/cam[:,2]+cy];low=uv.min(0);high=uv.max(0)
   center=(tr[target][t]-camera_position)@camera_rotation;cuv=np.array([fx*center[0]/center[2]+cx,fy*center[1]/center[2]+cy]);visible=bool((cam[:,2]>0).all() and high[0]>=0 and low[0]<width and high[1]>=0 and low[1]<height)
   rows.append(dict(frame=t,center_uv=cuv.tolist(),bbox_min=low.tolist(),bbox_max=high.tolist(),bbox_intersects_image=visible,center_in_image=bool(0<=cuv[0]<width and 0<=cuv[1]<height),actual_yaw_rad=float(yaw)))
  canvas=Image.new('RGB',(960,510));draw=ImageDraw.Draw(canvas)
  for i,t in enumerate([0,60,120,180,240,len(q)-1]):
   im=Image.fromarray(rgb[t].transpose(1,2,0));dd=ImageDraw.Draw(im);r=rows[t];dd.rectangle([*r['bbox_min'],*r['bbox_max']],outline='red',width=3);u,v=r['center_uv'];dd.ellipse([u-4,v-4,u+4,v+4],fill='red')
   xy=((i%3)*320,(i//3)*255);canvas.paste(im.resize((320,240)),xy);draw.text((xy[0],xy[1]+240),str(t)+' projected target box',fill='white')
  canvas.save(ep/'camera_projection_review.jpg')
  results.append(dict(episode=str(ep),frames=len(rows),center_outside_frames=sum(not r['center_in_image'] for r in rows),bbox_completely_outside_frames=sum(not r['bbox_intersects_image'] for r in rows),rows=rows))
(Path(sys.argv[1])/'CAMERA_VISIBILITY_AUDIT.json').write_text(json.dumps(dict(results=results,scope='URDF waist FK + configured ROS optical camera extrinsics + raw intrinsics + recorded object oriented box. Geometric field-of-view estimate only; render overlay must be checked, does not account for occlusion or simulation camera timing.',training_ready=False),indent=2))
for r in results:print(r['episode'],r['center_outside_frames'],r['bbox_completely_outside_frames'])
