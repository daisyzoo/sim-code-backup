#!/usr/bin/env python3
"""Teacher-forced h10 chunk continuity on selected training/validation demonstrations."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import torch
from pi05_policy_server import Pi05Server


def main():
 p=argparse.ArgumentParser();p.add_argument('--inference-steps',type=int,default=10);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--groups',nargs='+',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 a.out.mkdir(parents=True);records=json.loads((a.dataset/'meta/paired_provenance.json').read_text())['records'];split=json.loads((a.dataset/'meta/train_validation_split.json').read_text());selected=[(i,x) for i,x in enumerate(records) if x.get('geometry_group') in a.groups];assert len(selected)==4*len(a.groups)
 server=Pi05Server(argparse.Namespace(policy_path=a.checkpoint,dataset_root=a.dataset,repo_id=json.loads((a.checkpoint/'train_config.json').read_text())['dataset']['repo_id'],tokenizer_path=Path('/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224'),device='cuda:0',seed=0,num_inference_steps=a.inference_steps));server.warmup();rows=[];predictions={};ix=[*range(13,23),12]
 for eid,row in selected:
  path=Path(row['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['hash']
  with np.load(path,allow_pickle=False) as z:rgb=z['rgb'].copy();q=z['q'][:,ix].copy();gt=z['action'][:,ix].copy()
  assert len(gt)==160
  for seed in [0,1,2]:
   torch.manual_seed(seed);np.random.seed(seed);chunks=[]
   for t in range(0,len(gt),10):chunks.append(server.infer(rgb[t].transpose(1,2,0),q[t],row['exported_prompt']))
   stitched=np.concatenate([c[:10] for c in chunks]);dif=np.abs(np.diff(stitched[:,:10],axis=0));steps=dif.max(axis=1);events=[]
   for idx in np.flatnonzero(steps>.08):
    j=int(dif[idx].argmax());t=int(idx+1);events.append({'frame':t,'joint11_index':j,'step_rad':float(steps[idx]),'at_chunk_boundary':t%10==0,'predicted_previous_rad':float(stitched[t-1,j]),'predicted_next_rad':float(stitched[t,j]),'expert_previous_rad':float(gt[t-1,j]),'expert_next_rad':float(gt[t,j])})
   key=f'episode{eid}_seed{seed}';predictions[key]=np.stack(chunks);rows.append({'episode_index':eid,'partition':'train' if eid in split['train'] else 'validation','group':row['geometry_group'],'layout_id':row['layout_id'],'task':row['task_id'],'seed':seed,'raw_sha256':row['hash'],'max_action_step_rad':float(steps.max()),'expert_max_action_step_rad':float(np.abs(np.diff(gt,axis=0)).max()),'action_rmse_rad':float(np.sqrt(np.mean((stitched-gt)**2))),'events':events,'prediction_key':key})
  print('DEMONSTRATION_REPLAN',eid,row['geometry_group'],row['task_id'],'complete',flush=True)
 summary=[]
 for part in ['train','validation']:
  for task in ['nudge_mailer_to_bin','push_box_to_bin']:
   rs=[x for x in rows if x['partition']==part and x['task']==task];es=[e for x in rs for e in x['events']];summary.append({'partition':part,'task':task,'total':len(rs),'trajectories_with_abrupt_step':sum(bool(x['events']) for x in rs),'events':len(es),'boundary_events':sum(x['at_chunk_boundary'] for x in es),'mean_action_rmse_rad':float(np.mean([x['action_rmse_rad'] for x in rs]))})
 np.savez_compressed(a.out/'predictions.npz',**predictions);(a.out/'REPORT.json').write_text(json.dumps({'checkpoint':str(a.checkpoint.resolve()),'dataset':str(a.dataset.resolve()),'num_inference_steps':a.inference_steps,'groups':a.groups,'summary':summary,'rows':rows,'method':'Use demonstrated RGB+q at every10th frame; fresh noise per query, reset each episode/seed. Concatenate first10 unfiltered predictions; compare to demonstrated actions and unchanged>.08rad threshold.','limitations':'Teacher-forced open-loop observation replay, not physical rollout or success. Selected2 geometry groups, correlated seeds. Tests continuity under demonstrated states, not closed-loop recovery.','goal_complete':False},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
