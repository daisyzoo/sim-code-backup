#!/usr/bin/env python3
"""Read-only fixed-observation replay: fresh noise versus reduced or zero latent-noise amplitude."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import torch
from unittest.mock import patch
from pi05_policy_server import Pi05Server


def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--episodes',type=Path,nargs='+',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    a.out.mkdir(parents=True)
    server=Pi05Server(argparse.Namespace(policy_path=a.checkpoint,dataset_root=a.dataset,repo_id='local/paired_spatial_pilot40_20260928',tokenizer_path=Path('/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224'),device='cuda:0',seed=a.seed,num_inference_steps=10));server.warmup();rows=[];predictions={}
    for directory in a.episodes:
        logs=json.loads((directory/'policy_inferences.json').read_text())
        with np.load(directory/'raw.npz',allow_pickle=False) as z:rgb=z['rgb'].copy();meta=json.loads(str(z['collect_meta']))
        assert meta['expert']=='pi05_h10' and meta['policy_action_step_cap']==0 and [r['step'] for r in logs]==list(range(0,len(rgb),10))
        variants={};fresh_error=0.
        for mode in ['fresh','scaled_noise_half','zero_noise']:
            torch.manual_seed(a.seed);np.random.seed(a.seed);chunks=[]
            for row in logs:
                original_randn=torch.randn;noise_calls=[];scale={'fresh':1.,'scaled_noise_half':.5,'zero_noise':0.}[mode]
                def noise_override(*args,**kwargs):
                    assert tuple(args[0])==tuple(server.noise_shape)
                    noise_calls.append(1)
                    return original_randn(*args,**kwargs)*scale
                with patch.object(torch,'randn',side_effect=noise_override):
                    pred=server.infer(rgb[row['step']].transpose(1,2,0),np.asarray(row['state'],dtype=np.float32),row['prompt'])
                assert len(noise_calls)==1
                chunks.append(pred)
                if mode=='fresh':fresh_error=max(fresh_error,float(np.max(np.abs(pred-np.asarray(row['actions'])))))
            assert fresh_error<1e-4,f'Reproduction mismatch {fresh_error}; do not infer a noise effect'
            stitched=np.concatenate([x[:10] for x in chunks],axis=0)[:len(rgb)];diff=np.abs(np.diff(stitched[:,:10],axis=0)).max(axis=1);frames=np.flatnonzero(diff>.08)+1;variants[mode]={'max_action_step_rad':float(diff.max()),'abrupt_frames':frames.tolist(),'boundary_events':int((frames%10==0).sum()),'events':len(frames)};predictions[directory.name+'_'+mode]=np.stack(chunks)
        rows.append({'episode':str(directory.resolve()),'raw_sha256':hashlib.sha256((directory/'raw.npz').read_bytes()).hexdigest(),'logged_predictions_sha256':hashlib.sha256((directory/'policy_inferences.json').read_bytes()).hexdigest(),'fresh_reproduction_max_abs_error_rad':fresh_error,'variants':variants});print(json.dumps(rows[-1]),flush=True)
    np.savez_compressed(a.out/'predictions.npz',**predictions);(a.out/'REPORT.json').write_text(json.dumps({'checkpoint':str(a.checkpoint.resolve()),'seed':a.seed,'rows':rows,'method':'Same recorded observations and prompt, same model. Fresh-noise outputs must reproduce recorded50-step chunks to1e-4rad. Alternative scales each fresh Gaussian draw by0.5 or0; RNG sequence preserved. Only this independent diagnostic process patches the noise draw, asserting exactly one call per prediction. Stitch first10 with no clipping/smoothing.','limitations':['Open-loop replay on observations from the fresh-noise physical rollout; alternative-noise policy would visit other states.','Reduced-noise priors differ from the training prior; they can bias trajectories or damage visual/task conditioning. Requires independent branch and physical validation before adoption.','Auxiliary diagnosis only; current physical evaluation remains unchanged.','Selected development failures, not independent final evaluation.'],'physical_policy_changed':False,'goal_complete':False},indent=2))
if __name__=='__main__':main()
