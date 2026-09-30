#!/usr/bin/env python3
"""Controlled probes on expert observations and recorded empty-table failures."""
import argparse,json,os,sys
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS
from run_routing_diagnostics import load_inferencer


def main():
 p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);p.add_argument('--checkpoint',type=Path);args=p.parse_args()
 args.out_dir.mkdir(parents=True,exist_ok=False)
 checkpoint=args.checkpoint or Path((args.experiment/'checkpoint_b.txt').read_text().strip())
 dataset=ROOT.parent/'lerobot/lerobot_sim_paired_zero_pilot32_b_20260924'
 infer,_,_=load_inferencer(checkpoint,dataset,ROOT.parent/'lerobot/models/paligemma-3b-pt-224','cuda:0',42)
 ix=[*range(13,23),12];rows=[]
 for lid in (10,20,10000,10006):
  tasks=['wait_no_package'] if lid>=10000 else ['push_box_to_bin','nudge_mailer_to_bin']
  source=ROOT/'demo'/('paired_zero_wait8_20260924_r2' if lid>=10000 else 'paired_zero_push24_release_20260924_r1')
  for task in tasks:
   with np.load(source/f'layout_{lid:04d}_{task}/raw.npz') as d:
    q=d['q'][:,ix];gt=d['action'][:,ix];rgb=d['rgb']
    for t in ([0,35,60] if lid>=10000 else [0,40,60,90,120]):
     for seed in (0,1,2):
      pred=infer(torch.from_numpy(rgb[t].copy()).float()/255.,q[t],PAIRED_SORTING_PROMPTS[task],seed)
      n=min(10,len(q)-t);err=pred[:n]-gt[t:t+n]
      rows.append({'kind':'expert_observation','split':'train' if lid in (10,10000) else 'validation','layout':lid,'task':task,'t':t,'seed':seed,'first10_mae_rad':float(np.abs(err).mean()),'first10_max_error_rad':float(np.abs(err).max()),'pred_first':pred[0].tolist(),'gt_first':gt[t].tolist()})
     print('expert',lid,task,t,flush=True)
 for rollout_seed in (0,1,2):
  path=args.experiment/f'b_seed{rollout_seed}/rollouts/layout_20000_wait_no_package/raw.npz'
  with np.load(path) as d:
   q=d['q'][:,ix];rgb=d['rgb']
   # Same noise in each 2x2 comparison isolates state vs image conditioning.
   for image_t in (0,60):
    for state_t in (0,60):
     for noise in (0,1,2):
      pred=infer(torch.from_numpy(rgb[image_t].copy()).float()/255.,q[state_t],PAIRED_SORTING_PROMPTS['wait_no_package'],noise)
      rows.append({'kind':'wait_state_image_probe','rollout_seed':rollout_seed,'image_t':image_t,'state_t':state_t,'noise_seed':noise,'pred_first10_max_abs_rad':float(np.abs(pred[:10]).max()),'pred_first10_mean_abs_rad':float(np.abs(pred[:10]).mean()),'state_max_abs_rad':float(np.abs(q[state_t]).max()),'pred_first':pred[0].tolist()})
  print('wait_probe',rollout_seed,flush=True)
 result={'checkpoint':str(checkpoint),'rows':rows,'note':'Diagnostic probes, not closed-loop success evidence. No data or model modification.'}
 (args.out_dir/'probes.json').write_text(json.dumps(result,indent=2))
 print('COMPLETE',len(rows),flush=True)

if __name__=='__main__':main()
