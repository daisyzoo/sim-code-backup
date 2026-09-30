"""Offline raw vs training-decoded validation images under identical policy inputs.
Uses exact server inference; no images synthesized, no actions executed, no retraining.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse,json,sys,hashlib
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parent;sys.path.insert(0,str(ROOT/'scripts'))
from pi05_policy_server import Pi05Server
from lerobot.datasets.lerobot_dataset import LeRobotDataset
import pandas as pd
import pyarrow.parquet as pq
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();assert not args.out.exists()
variant='ordinary';dataset=WS/'lerobot/lerobot_sim_paired_ordinary_pilot40_20260928';repo='local/paired_ordinary_pilot40_20260928';checkpoint=Path((ROOT/'demo/recovery_comparison_20260928_r1/checkpoint_ordinary.txt').read_text().strip())
recs=json.loads((dataset/'meta/paired_provenance.json').read_text())['records'];validation=json.loads((dataset/'meta/train_validation_split.json').read_text())['validation'];table=pd.concat([pq.read_table(p).to_pandas() for p in sorted((dataset/'data').glob('chunk-*/file-*.parquet'))],ignore_index=True)
ds=LeRobotDataset(repo,root=dataset,video_backend='pyav')
server=Pi05Server(SimpleNamespace(seed=0,policy_path=checkpoint,dataset_root=dataset,repo_id=repo,tokenizer_path=WS/'lerobot/models/paligemma-3b-pt-224',device='cuda:0',num_inference_steps=10))
rows=[];ix=[*range(13,23),12]
for i in validation:
 rec=recs[i];path=WS/rec['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==rec['hash'];episode_rows=table[table.episode_index==i].sort_values('frame_index')
 with np.load(path) as d:
  for frame in (0,25,60):
   item=ds[int(episode_rows.iloc[frame]['index'])];assert item['task']==rec['exported_prompt']
   raw=d['rgb'][frame].transpose(1,2,0).copy();decoded=item['observation.images.color_0'].cpu().numpy()
   if decoded.shape[0]==3:decoded=decoded.transpose(1,2,0)
   decoded=np.rint(decoded*255 if decoded.max()<=1.5 else decoded).clip(0,255).astype(np.uint8)
   state=d['q'][frame,ix].copy();target=d['action'][frame:frame+10][:,ix].copy();assert target.shape==(10,11)
   for seed in (0,1,2):
    predictions=[]
    for image in (raw,decoded):
     torch.manual_seed(seed);np.random.seed(seed);predictions.append(server.infer(image,state,rec['exported_prompt'])[:10])
    a,b=predictions;rows.append({'layout':rec['layout_id'],'task':rec['task_id'],'frame':frame,'noise_seed':seed,'pixel_mae_255':float(abs(raw.astype(float)-decoded).mean()),'raw_vs_decoded_first10_max_rad':float(abs(a-b).max()),'raw_vs_decoded_first10_mae_rad':float(abs(a-b).mean()),'raw_first10_mae_to_teacher_rad':float(abs(a-target).mean()),'decoded_first10_mae_to_teacher_rad':float(abs(b-target).mean())})
   print(rec['layout_id'],rec['task_id'],frame,flush=True)
args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps({'checkpoint':str(checkpoint),'dataset':str(dataset),'rows':rows,'method':'6 held-out episodes x3 fixed frames x3 flow-noise seeds x2 exact image encodings. State/prompt/noise fixed within pair; physical11action dimensions, first10 predictions. Teacher-error comparison is offline, not closed-loop success. No hyperparameters or data changed.','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
