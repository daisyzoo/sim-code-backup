"""All eight closed5N pushes: recorded camera-pose pinhole counterfactual only.
No new RGB, camera, scene, trajectory or admission rule. Boxes ignore occlusion,
lens distortion and model resolution effects; not a hardware recommendation.
"""
from pathlib import Path
import json,hashlib,datetime,itertools,zipfile,math
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;r=w/'precise_interior_groups_r1'
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
# Model input size is taken from the retained local Pi0.5 base configuration.
model_cfg=w.parents[2]/'lerobot/models/pi05_base/config.json'
config=json.loads(model_cfg.read_text());resolution=config['image_resolution'];assert resolution==[224,224]
# Current local policy uses aspect-preserving resize_with_pad; 640x480 ->224x168.
policy=w.parents[2]/'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py'
import ast,torch,torch.nn.functional as F
nodes=ast.parse(policy.read_text());node=next(n for n in nodes.body if isinstance(n,ast.FunctionDef) and n.name=='resize_with_pad_torch');env={'torch':torch,'F':F};exec(compile(ast.Module(body=[node],type_ignores=[]),str(policy),'exec'),env)
fixture=torch.ones(1,480,640,3,dtype=torch.float32);resized=env['resize_with_pad_torch'](fixture,*resolution);assert tuple(resized.shape)==(1,224,224,3)
active=(resized[0,:,:,0]>0);assert int(active.any(1).sum())==168 and int(active.any(0).sum())==224
for episode in results:
 for scenario in episode['scenarios']:
  scenario['model_input_projected_bbox_wh_quantiles_pixels']=(np.array(scenario['target_bbox_wh_quantiles_pixels'])*.35).tolist()
report=dict(scope='Complete closed precise5N eight trajectories; pinhole projection only, no occlusion or new RGB. Model224 input dimensions verified from local base config and actual local resize function. Counterfactual box sizes are estimates, not rendered evidence or classification thresholds.',created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256={str(p):sha(p) for p in [r/'RESULT.json',r/'PROTOCOL.json',Path(__file__),model_cfg,policy]},episodes=results,model_input_hw=resolution,resize_fixture_verified=True,source_rgb_hw=[480,640],resized_content_hw=[168,224],physical_camera_changed=False,new_rgb_rendered=False,training_ready=False)
(w/'PRECISE_FULL8_CAMERA_MODEL_SCALE_SCREEN.json').write_text(json.dumps(report,indent=2))
print('MODEL224_SCALE_SCREEN_COMPLETE',flush=True)
