"""Offline same-input repeat and historical/current first-image swap using exact server path.
Run only when no training/Isaac evaluation occupies GPU. Predictions are never executed.
"""
from pathlib import Path
import argparse,json,hashlib,sys
from types import SimpleNamespace
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pi05_policy_server import Pi05Server
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();assert not args.out.exists()
checkpoint=Path((ROOT/'demo/paired_zero_ab_experiment_20260924_r1/checkpoint_b.txt').read_text().strip())
server=Pi05Server(SimpleNamespace(seed=0,policy_path=checkpoint,dataset_root=ROOT.parent/'lerobot/lerobot_sim_paired_zero_pilot32_b_20260924',repo_id='local/paired_zero_pilot32_b',tokenizer_path=ROOT.parent/'lerobot/models/paligemma-3b-pt-224',device='cuda:0',num_inference_steps=10))
rows=[];ix=[*range(13,23),12]
for seed in (0,1,2):
 old=ROOT/f'demo/paired_zero_ab_experiment_20260924_r1/b_seed{seed}/rollouts';new=ROOT/f'demo/recovery_comparison_20260928_r1/baseline_seed{seed}/rollouts'
 for folder in sorted(new.glob('layout_*')):
  a=old/folder.name/'raw.npz';b=folder/'raw.npz'
  with np.load(a) as da,np.load(b) as db:
   qa=da['q'][0,ix].copy();qb=db['q'][0,ix].copy();assert np.array_equal(qa,qb)
   images=[da['rgb'][0].transpose(1,2,0).copy(),db['rgb'][0].transpose(1,2,0).copy()];task=str(da['instruction']);assert task==str(db['instruction'])
  pred=[]
  for image in [images[0],images[0],images[1],images[1]]:
   torch.manual_seed(seed);np.random.seed(seed);out=server.infer(image,qa,task);assert np.isfinite(out).all();pred.append(out.copy())
  logged=[np.asarray(json.loads((d/'policy_inferences.json').read_text())[0]['actions'],dtype=np.float32) for d in (a.parent,b.parent)]
  row={'seed':seed,'episode':folder.name,'initial_state_equal':True,'image_mae_255':float(abs(images[0].astype(float)-images[1]).mean()),'same_old_image_repeat_max_rad':float(abs(pred[0]-pred[1]).max()),'same_new_image_repeat_max_rad':float(abs(pred[2]-pred[3]).max()),'image_swap_first10_max_rad':float(abs(pred[0][:10]-pred[2][:10]).max()),'old_log_reproduction_first10_max_rad':float(abs(pred[0][:10]-logged[0][:10]).max()),'new_log_reproduction_first10_max_rad':float(abs(pred[2][:10]-logged[1][:10]).max()),'raw_sha256':[hashlib.sha256(x.read_bytes()).hexdigest() for x in (a,b)]}
  rows.append(row);print(seed,folder.name,'repeat',row['same_new_image_repeat_max_rad'],'swap',row['image_swap_first10_max_rad'],flush=True)
args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps({'checkpoint':str(checkpoint),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rows':rows,'note':'Same checkpoint/state/prompt/noise with real recorded first-image swap. Separates image-conditioned prediction differences from within-process repeat variation. No closed-loop replay, no attribution of entire trajectory difference to images alone, no training or synthetic augmentation.'},indent=2))
