"""Frozen B policy on physically recorded recovery states; no training."""
from pathlib import Path
import sys,json
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run_routing_diagnostics import load_inferencer
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS
out=ROOT/'demo/recovery_protocol_20260928_r1'
checkpoint=Path((ROOT/'demo/paired_zero_ab_experiment_20260924_r1/checkpoint_b.txt').read_text().strip())
infer,_,_=load_inferencer(checkpoint,ROOT.parent/'lerobot/lerobot_sim_paired_zero_pilot32_b_20260924',ROOT.parent/'lerobot/models/paligemma-3b-pt-224','cuda:0',42)
rows=[];ix=[*range(13,23),12]
for force,kind in ((0,'scale'),(80,'bilateral')):
 p=ROOT/f'demo/recovery_{kind}_20260928_f{force}_r1/layout_30001_wait_no_package/raw.npz'
 with np.load(p) as d:
  for t in (0,23,26,35):
   for noise in (0,1,2):
    pred=infer(torch.from_numpy(d['rgb'][t].copy()).float()/255.,d['q'][t,ix],PAIRED_SORTING_PROMPTS['wait_no_package'],noise)
    rows.append({'force_parameter_N':force,'frame':t,'noise_seed':noise,'q_11_rad':d['q'][t,ix].tolist(),'predicted_first_action_rad':pred[0].tolist(),'first10_max_abs_rad':float(abs(pred[:10]).max()),'first10_mae_to_zero_rad':float(abs(pred[:10]).mean()),'shoulder_pitch_first10_mean_rad':pred[:10,[0,5]].mean(0).tolist()})
   print(force,t,flush=True)
(out/'recovery_policy_probes.json').write_text(json.dumps({'checkpoint':str(checkpoint),'rows':rows,'note':'Offline predictions only; zero targets were physically executed and recovered. No closed-loop model improvement claim.'},indent=2))
