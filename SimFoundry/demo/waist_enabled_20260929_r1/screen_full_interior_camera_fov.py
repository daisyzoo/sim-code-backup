"""All eight closed5N pushes: recorded camera-pose pinhole counterfactual only.
No new RGB, camera, scene, trajectory or admission rule. Boxes ignore occlusion,
lens distortion and model resolution effects; not a hardware recommendation.
"""
from pathlib import Path
import json,hashlib,datetime,itertools,zipfile,math
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;r=w/'recontact_interior_groups_r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protocol=json.loads((r/'PROTOCOL.json').read_text());assert json.loads((r/'RESULT.json').read_text())['push_total']==8
results=[]
for command in protocol['commands']:
 if command['wait']:continue
 for task in command['tasks']:
  ep=r/f"case_{command['layout_id']}"/f"layout_{command['layout_id']}_{task}"
  target='box' if 'push_box' in task else 'mailer';other='mailer' if target=='box' else 'box'
  quality=json.loads((ep/'quality.json').read_text());assert quality['frames']==1200
  with np.load(ep/'trace.npz') as z:xyz={k:z[k].copy() for k in [target,other]}
  with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in [target,other]}
  with zipfile.ZipFile(ep/'raw.npz') as z,z.open('rgb.npy') as f:
   ver=np.lib.format.read_magic(f);shape,order,dtype=np.lib.format.read_array_header_1_0(f) if ver==(1,0) else np.lib.format.read_array_header_2_0(f)
  assert shape[0]==1200 and shape[1]==3 and not order;h,width=shape[2:];limit=np.array([width,h])
  views=json.loads((ep/'viewer_observer.json').read_text())['frames'];samples=[]
  assert len(views)==240 and [x['pre_action_step'] for x in views]==list(range(0,1200,5))
  for v in views:
   t=v['pre_action_step'];R=Rotation.from_quat(v['policy_camera_quat_ros_xyzw']).as_matrix();pos=np.array(v['policy_camera_position_world']);K=np.array(v['policy_camera_intrinsics']);out={'step':t,'K':K,'objects':{}}
   for obj in [target,other]:
    size=np.array([.14,.09,.045] if obj=='box' else [.15,.145,.04]);corners=np.array(list(itertools.product([-1,1],repeat=3)))*size/2
    local=(corners@rot[obj][t].T+xyz[obj][t]-pos)@R;assert (local[:,2]>0).all()
    px=local@K.T;uv=px[:,:2]/px[:,2:];out['objects'][obj]=(uv.min(0),uv.max(0))
   samples.append(out)
  scenarios=[]
  for scale in [1.,.75,.6,.5,.4,.3]:
   rows=[]
   for sample in samples:
    center=sample['K'][:2,2];entry={'step':sample['step']}
    for obj in [target,other]:
     low,high=sample['objects'][obj];low=center+scale*(low-center);high=center+scale*(high-center);visible=np.maximum(0,np.minimum(high,limit)-np.maximum(low,0));wh=high-low
     entry[obj]={'fraction':float(np.prod(visible)/np.prod(wh)),'bbox_wh_pixels':wh.tolist()}
    rows.append(entry)
   K=samples[0]['K'];scenarios.append(dict(focal_scale=scale,horizontal_fov_deg=math.degrees(2*math.atan(width/(2*K[0,0]*scale))),samples=len(rows),target_outside=sum(x[target]['fraction']==0 for x in rows),both_outside=sum(x[target]['fraction']==0 and x[other]['fraction']==0 for x in rows),target_half=sum(x[target]['fraction']>=.5 for x in rows),both_half=sum(min(x[target]['fraction'],x[other]['fraction'])>=.5 for x in rows),target_bbox_wh_quantiles_pixels=np.quantile([x[target]['bbox_wh_pixels'] for x in rows],[.1,.5,.9],axis=0).tolist()))
  result=dict(episode=ep.name,original_task_passed=quality['passed'],scenarios=scenarios,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','viewer_observer.json','quality.json']});results.append(result)
  print(ep.name,[{k:s[k] for k in ['focal_scale','target_outside','both_half']} for s in scenarios],flush=True)
assert len(results)==8
# Retained four-condition screen is an independent consistency check, not overwritten.
old=json.loads((r/'CAMERA_FOV_SCREEN.json').read_text())
for oldep in old['episodes']:
 new=next(x for x in results if x['episode']==oldep['episode'])
 for before,after in zip(oldep['counterfactual_scales'],new['scenarios']):
  for a,b in [('focal_scale','focal_scale'),('target_outside','target_outside'),('both_outside','both_outside'),('target_at_least_half','target_half'),('both_at_least_half','both_half')]:assert before[a]==after[b],(new['episode'],a,b)
report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256={str(p):sha(p) for p in [r/'RESULT.json',r/'PROTOCOL.json',r/'CAMERA_FOV_SCREEN.json',Path(__file__)]},episodes=results,original_four_condition_consistency_passed=True,physical_camera_changed=False,new_rgb_rendered=False,training_ready=False)
(w/'INTERIOR_FULL8_CAMERA_FOV_SCREEN.json').write_text(json.dumps(report,indent=2))
