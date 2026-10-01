"""Actual RTX images through the retained Pi0.5 resize function, no inference.
Projected object boxes estimate image footprint only, not occlusion/recognition.
"""
from pathlib import Path
import sys,ast,json,hashlib,itertools,math
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image,ImageDraw
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sim=w.parents[2];r=w/'minimum_motion_camera_comparison_r1';run=w/'minimum_motion_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=sim/'lerobot/models/pi05_base/config.json';resolution=json.loads(cfg.read_text())['image_resolution'];assert resolution==[224,224]
policy=sim/'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py';node=next(n for n in ast.parse(policy.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='resize_with_pad_torch');namespace={'torch':torch,'F':F};exec(compile(ast.Module(body=[node],type_ignores=[]),str(policy),'exec'),namespace);resize=namespace['resize_with_pad_torch']
fixture=resize(torch.ones(1,480,640,3),224,224);assert tuple(fixture.shape)==(1,224,224,3);active=fixture[0,:,:,0]>0;assert int(active.any(1).sum())==168 and int(active.any(0).sum())==224
rows=[]
for p in sorted(r.glob('layout_*/REPORT.json')):
 d=json.loads(p.read_text());name=d['episode'];cid=name.split('_')[1];ep=run/f'case_{cid}'/name;target='box' if 'push_box' in name else 'mailer';sheet=Image.new('RGB',(896,496));draw=ImageDraw.Draw(sheet)
 views={x['pre_action_step']:x for x in json.loads((ep/'viewer_observer.json').read_text())['frames']}
 with np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  for col,t in enumerate(d['frames']):
   obs=views[t];C=Rotation.from_quat(obs['policy_camera_quat_ros_xyzw']).as_matrix();pos=np.array(obs['policy_camera_position_world']);K=np.array(obs['policy_camera_intrinsics'])
   for row,scale in enumerate([1.,.4]):
    image=p.parent/f'{t:04d}_focal{scale:g}.png';im=np.asarray(Image.open(image).convert('RGB'));assert im.shape==(480,640,3)
    model=resize(torch.from_numpy(im.copy()).float()[None]/127.5-1.,224,224);out=np.clip(np.round((model[0].numpy()+1.)*127.5),0,255).astype(np.uint8);filename=f'{t:04d}_focal{scale:g}_model224.png';Image.fromarray(out).save(p.parent/filename)
    sheet.paste(Image.fromarray(out),(col*224,row*248));draw.text((col*224,row*248+225),f'{t} focal {scale:g}')
    objects={};newK=K.copy();newK[0,0]*=scale;newK[1,1]*=scale
    for obj,size in [('box',[.14,.09,.045]),('mailer',[.15,.145,.04])]:
     corners=np.array(list(itertools.product([-1,1],repeat=3)))*np.array(size)/2;R=Rotation.from_quat(ori[obj][t]).as_matrix();camera=(corners@R.T+tr[obj][t]-pos)@C;assert (camera[:,2]>0).all();pixels=camera@newK.T;uv=pixels[:,:2]/pixels[:,2,None];low,high=uv.min(0),uv.max(0);wh=high-low;clipped=np.maximum(0,np.minimum(high,[640,480])-np.maximum(low,0))
     objects[obj]=dict(projected_bbox_model224_wh_pixels=(wh*.35).tolist(),clipped_bbox_model224_wh_pixels=(clipped*.35).tolist(),projected_visible_fraction=float(np.prod(clipped)/np.prod(wh)))
    rows.append(dict(episode=name,frame=t,scale=scale,target=target,objects=objects,image_sha256=sha(image),model224_image=filename,model224_sha256=sha(p.parent/filename)))
 sheet.save(p.parent/'MODEL224_COMPARISON.png')
report=dict(scope=__doc__,source_sha256={str(p):sha(p) for p in [Path(__file__),cfg,policy,r/'REPORT.json',run/'PROTOCOL.json']},resize_content_hw=[168,224],model_input_hw=resolution,rows=rows,geometry_ignores_occlusion=True,actual_inference=False,training_ready=False)
(r/'MODEL224_REPORT.json').write_text(json.dumps(report,indent=2))
for scale in [1.,.4]:
 selected=[x for x in rows if x['scale']==scale];print(scale,'samples',len(selected),'outside targets',sum(x['objects'][x['target']]['projected_visible_fraction']==0 for x in selected),'p10 bbox',np.quantile([x['objects'][x['target']]['projected_bbox_model224_wh_pixels'] for x in selected],.1,axis=0).tolist())
