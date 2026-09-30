#!/usr/bin/env python3
"""Recover final heldout loss after save completed but external artifact logging failed."""
import argparse,json,random
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from pi05_policy_server import Pi05Server
from lerobot.datasets.lerobot_dataset import LeRobotDataset,LeRobotDatasetMetadata
from lerobot.datasets.factory import resolve_delta_timestamps


def main():
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 tc=json.loads((a.checkpoint/'train_config.json').read_text());dc=tc['dataset'];root=Path(dc['root']);split=json.loads((root/'meta/train_validation_split.json').read_text())
 step=json.loads((a.checkpoint.parent/'training_state/training_step.json').read_text())['step'];assert step==14480
 server=Pi05Server(argparse.Namespace(policy_path=a.checkpoint,dataset_root=root,repo_id=dc['repo_id'],tokenizer_path=Path('/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224'),device='cuda:0',seed=0,num_inference_steps=10))
 assert server.policy.config.joint_action_representation=='state_relative_arm10'
 meta=LeRobotDatasetMetadata(dc['repo_id'],root=str(root));ds=LeRobotDataset(dc['repo_id'],root=str(root),episodes=split['validation'],delta_timestamps=resolve_delta_timestamps(server.policy.config,meta),video_backend=dc['video_backend'],tolerance_s=dc['tolerance_s']);ds._ensure_hf_dataset_loaded()
 assert len(ds)==1560 and set(map(int,ds.hf_dataset['episode_index']))==set(split['validation'])
 loader=DataLoader(ds,batch_size=1,shuffle=False,num_workers=0)
 torch.manual_seed(42000);np.random.seed(42000);random.seed(42000);total=0.;count=0
 with torch.no_grad():
  for batch in loader:
   with torch.autocast('cuda',dtype=torch.bfloat16):loss,_=server.policy(server.preprocessor(batch))
   assert torch.isfinite(loss);total+=float(loss.double());count+=1
   if count%200==0:print('VALIDATION_FRAMES',count,flush=True)
 assert count==1560
 result={'step':step,'validation/loss':total/count,'validation/frames':count,'metric_note':'Native stochastic residual flow loss; loaded saved checkpoint recovery run after W&B artifact failed. Same validation order,batch1,bf16 autocast,seed42000; no optimization. Not cross-representation MAE or rollout success.'}
 a.out.write_text(json.dumps(result)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
