"""Quarantined diagnostic I/O and normalization roundtrip, never training approval."""
from pathlib import Path
import sys,os,json,hashlib
import numpy as np
import torch
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parents[2]/'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src'))
os.environ['HF_HUB_OFFLINE']='1'
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.pi05.joint_relative import joint_action_transform
from lerobot.processor.normalize_processor import NormalizerProcessorStep,UnnormalizerProcessorStep
from lerobot.configs.types import PolicyFeature,FeatureType,NormalizationMode
from lerobot.processor.core import TransitionKey
out=root/'waist_transport_diagnostic_r1'
out.mkdir(exist_ok=False)
(out/'NOT_TRAINING_DATA.json').write_text(json.dumps(dict(training_ready=False,purpose='Diagnostic transport only. Source episodes are not approved. Do not use for training, statistics fitting for a real model, or model performance claims.')))
paths=[root/f'coordinated_smoke/layout_61000_{task}/raw.npz' for task in ['push_box_to_bin','nudge_mailer_to_bin']]
ix=[*range(13,23),12];episodes=[]
for p in paths:
 with np.load(p) as z:episodes.append((p,z['q'][:,ix].copy(),z['action'][:,ix].copy(),z['rgb'].copy()))
features={key:dict(dtype='float32',shape=(11,),names=None) for key in ['observation.state','action']}
features['observation.images.color_0']=dict(dtype='video',shape=(480,640,3),names=['height','width','channel'])
ds=LeRobotDataset.create(repo_id='diagnostic/waist_transport',root=out/'transport',fps=15,robot_type='Unitree_G1_23Dof_Arms5_Waist1',features=features,use_videos=True,image_writer_processes=0,image_writer_threads=2)
for p,q,a,rgb in episodes:
 for t in range(len(q)):ds.add_frame({'observation.state':q[t],'action':a[t],'observation.images.color_0':rgb[t].transpose(1,2,0),'task':'DIAGNOSTIC TRANSPORT ONLY '+p.parent.name})
 ds.save_episode()
ds.finalize()
ds=LeRobotDataset('diagnostic/waist_transport',root=out/'transport',video_backend='pyav')
import pyarrow.parquet as pq
import pandas as pd
table=pd.concat([pq.read_table(p).to_pandas() for p in sorted((out/'transport/data').glob('chunk-*/file-*.parquet'))],ignore_index=True)
report=dict(training_ready=False,model_inference_verified=False,episodes=[],video_mae=[],normalization='Actual local processor classes, QUANTILES, diagnostic source statistics only; no training statistics promoted.')
encoded=[];states=[];actions=[]
for i,(p,q,a,rgb) in enumerate(episodes):
 rows=table[table.episode_index==i].sort_values('frame_index');assert rows.frame_index.tolist()==list(range(len(q)))
 np.testing.assert_allclose(np.stack(rows['observation.state']),q,atol=1e-6,rtol=0);np.testing.assert_allclose(np.stack(rows.action),a,atol=1e-6,rtol=0)
 assert np.max(abs(q[0]))<1e-4 and np.max(abs(a[0]))<1e-4
 for t in [0,len(q)//2,len(q)-1]:
  item=ds[int(rows.iloc[t]['index'])];assert item['task']=='DIAGNOSTIC TRANSPORT ONLY '+p.parent.name
  decoded=item['observation.images.color_0'].cpu().numpy()*255;mae=float(abs(decoded-rgb[t]).mean());assert mae<8;report['video_mae'].append(mae)
 aa=torch.from_numpy(np.stack([a[t:t+10] for t in range(len(a)-9)]));qq=torch.from_numpy(q[:len(a)-9]);rr=joint_action_transform(aa,qq)
 np.testing.assert_array_equal(rr[:,:,10],aa[:,:,10]);encoded.append(rr);states.append(qq);actions.append(aa)
 report['episodes'].append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),frames=len(q),waist_state_range=[float(q[:,-1].min()),float(q[:,-1].max())]))
r=torch.cat(encoded);q=torch.cat(states);a=torch.cat(actions)
def stats(x):
 arr=x.reshape(-1,11).numpy();return {k:np.quantile(arr,v,axis=0).astype(np.float32) for k,v in [('q01',.01),('q99',.99)]}
kw=dict(features={'observation.state':PolicyFeature(type=FeatureType.STATE,shape=(11,)),'action':PolicyFeature(type=FeatureType.ACTION,shape=(11,))},norm_map={FeatureType.STATE:NormalizationMode.QUANTILES,FeatureType.ACTION:NormalizationMode.QUANTILES},stats={'observation.state':stats(q),'action':stats(r)})
norm=NormalizerProcessorStep(**kw);unnorm=UnnormalizerProcessorStep(**kw)
t={TransitionKey.OBSERVATION:{'observation.state':q},TransitionKey.ACTION:r}
normalized=norm(t);un=unnorm(normalized)
# Unnormalizer public processor applies actions; observation inverse checked by exact shared method.
qback=unnorm._normalize_observation(normalized[TransitionKey.OBSERVATION],inverse=True)['observation.state']
back=joint_action_transform(un[TransitionKey.ACTION],q,inverse=True)
report['state_roundtrip_max_error']=float(abs(qback-q).max());report['action_roundtrip_max_error']=float(abs(back-a).max());report['waist_roundtrip_max_error']=float(abs(back[:,:,10]-a[:,:,10]).max())
assert max(report[k] for k in ['state_roundtrip_max_error','action_roundtrip_max_error','waist_roundtrip_max_error'])<1e-5
report['limitations']='Real diagnostic raw -> LeRobot parquet/video -> loader -> relative arm10 -> quantile processors -> decoded physical 11D. No learned policy or socket/robot execution here. Collector pilot approval, full new-protocol converter contracts and model inference remain pending.'
(out/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
