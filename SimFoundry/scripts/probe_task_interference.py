#!/usr/bin/env python3
"""Counterfactual prompts at identical observations; no action execution or data edits."""
import argparse,json,sys
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS
from run_routing_diagnostics import load_inferencer

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 a.out.mkdir(exist_ok=False,parents=True)
 protocol={'hypothesis':'Shared policy may suppress task-conditioned actions; changing prompt alone should change selected arm even on identical observations. Later off-task states are counterfactual diagnostics, not expert targets.', 'layouts':[10,20],'frames':[0,40,90,120],'seeds':[0,1], 'models':['baseline','ordinary'],'no_training':True,'no_reserved_confirmation_layouts':True}
 (a.out/'protocol.json').write_text(json.dumps(protocol,indent=2))
 rows=[];ix=[*range(13,23),12]
 tasks=['push_box_to_bin','nudge_mailer_to_bin'];prompt_tasks=tasks+['wait_no_package']
 for variant,cpfile,ds in [('baseline','paired_zero_ab_experiment_20260924_r1/checkpoint_b.txt','lerobot_sim_paired_zero_pilot32_b_20260924'),('ordinary','recovery_comparison_20260928_r1/checkpoint_ordinary.txt','lerobot_sim_paired_ordinary_pilot40_20260928')]:
  cp=Path((ROOT/'demo'/cpfile).read_text().strip())
  infer,policy,pre=load_inferencer(cp,ROOT.parent/'lerobot'/ds,ROOT.parent/'lerobot/models/paligemma-3b-pt-224','cuda:0',42)
  for lid in protocol['layouts']:
   for task in tasks:
    path=ROOT/'demo/paired_zero_push24_release_20260924_r1'/f'layout_{lid:04d}_{task}/raw.npz'
    with np.load(path) as d:
     q=d['q'][:,ix];gt=d['action'][:,ix];rgb=d['rgb']
     for t in protocol['frames']:
      for seed in protocol['seeds']:
       preds={k:infer(torch.from_numpy(rgb[t].copy()).float()/255.,q[t],PAIRED_SORTING_PROMPTS[k],seed)[:10] for k in prompt_tasks}
       correct=preds[task];other=preds[tasks[1-tasks.index(task)]]
       row={'model':variant,'layout':lid,'source_task':task,'frame':t,'seed':seed,'correct_mae':float(np.abs(correct-gt[t:t+10]).mean()),'swapped_mae_to_source_gt':float(np.abs(other-gt[t:t+10]).mean()),'prompt_delta_mae':float(np.abs(correct-other).mean()),'prompt_delta_max':float(np.abs(correct-other).max()),'predictions':{k:v.tolist() for k,v in preds.items()},'state':q[t].tolist()}
       rows.append(row)
      print(variant,lid,task,t,flush=True)
      (a.out/'results.json').write_text(json.dumps({'protocol':protocol,'rows':rows},indent=2))
  del infer,policy,pre;torch.cuda.empty_cache()
 summary=[]
 for variant in protocol['models']:
  for task in tasks:
   for t in protocol['frames']:
    rs=[r for r in rows if r['model']==variant and r['source_task']==task and r['frame']==t]
    summary.append({'model':variant,'task':task,'frame':t,'n':len(rs),**{k:float(np.mean([r[k] for r in rs])) for k in ['correct_mae','swapped_mae_to_source_gt','prompt_delta_mae','prompt_delta_max']}})
 (a.out/'SUMMARY.json').write_text(json.dumps(summary,indent=2))
 (a.out/'STATUS.json').write_text(json.dumps({'stage':'complete_analysis_pending','forward_calls':len(rows)*3}))
 print('COMPLETE',len(rows)*3,flush=True)
if __name__=='__main__':main()
