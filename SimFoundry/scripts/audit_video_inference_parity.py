#!/usr/bin/env python3
"""Compare raw/decoded RGB on identical state and latent noise; no pipeline edits."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import torch
from pi05_policy_server import Pi05Server
from lerobot.datasets.lerobot_dataset import LeRobotDataset

def main():
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=False,parents=True)
 cfg=json.loads((a.checkpoint/'train_config.json').read_text());dc=cfg['dataset'];root=Path(dc['root']);records=json.loads((root/'meta/paired_provenance.json').read_text())['records'];selected=[i for i,r in enumerate(records) if r.get('geometry_group') in ['candidate_07_center','candidate_14_center']];assert len(selected)==8
 ds=LeRobotDataset(dc['repo_id'],root=str(root),episodes=selected,video_backend=dc['video_backend'],tolerance_s=dc['tolerance_s']);ds._ensure_hf_dataset_loaded();ep=np.asarray(ds.hf_dataset['episode_index']).reshape(-1);fr=np.asarray(ds.hf_dataset['frame_index']).reshape(-1);lookup={(int(e),int(t)):i for i,(e,t) in enumerate(zip(ep,fr))}
 server=Pi05Server(argparse.Namespace(policy_path=a.checkpoint,dataset_root=root,repo_id=dc['repo_id'],tokenizer_path=Path('/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224'),device='cuda:0',seed=0,num_inference_steps=10));server.warmup();rows=[];frames=[];predictions={};ix=[*range(13,23),12]
 for eid in selected:
  record=records[eid];path=Path(record['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==record['hash']
  with np.load(path) as z:q=z['q'][:,ix].copy();rgb=z['rgb'].copy();gt=z['action'][:,ix].copy()
  torch.manual_seed(0);np.random.seed(0);raw_chunks=[];decoded_chunks=[]
  for t in range(0,160,10):
   item=ds[lookup[(eid,t)]];assert np.array_equal(item['observation.state'].numpy(),q[t]);assert item['task']==record['exported_prompt']
   decoded=np.clip(np.rint(item['observation.images.color_0'].numpy()*255),0,255).astype(np.uint8).transpose(1,2,0);raw=rgb[t].transpose(1,2,0);assert raw.shape==decoded.shape
   state=torch.cuda.get_rng_state();raw_pred=server.infer(raw,q[t],record['exported_prompt']);torch.cuda.set_rng_state(state);decoded_pred=server.infer(decoded,q[t],record['exported_prompt']);raw_chunks.append(raw_pred);decoded_chunks.append(decoded_pred)
   frames.append({'episode':eid,'frame':t,'rgb_mae_255':float(np.abs(raw.astype(float)-decoded).mean()),'first10_action_rmse_change_rad':float(np.sqrt(np.mean((raw_pred[:10,:10]-decoded_pred[:10,:10])**2))),'max_first10_action_change_rad':float(np.abs(raw_pred[:10,:10]-decoded_pred[:10,:10]).max())})
  row={'episode':eid,'task':record['task_id'],'group':record['geometry_group'],'raw_hash':record['hash']}
  for label,chunks in [('raw',raw_chunks),('decoded',decoded_chunks)]:
   actions=np.concatenate([c[:10] for c in chunks]);steps=np.abs(np.diff(actions[:,:10],axis=0)).max(1);row[label]={'events':int((steps>.08).sum()),'max_step_rad':float(steps.max()),'action_rmse_rad':float(np.sqrt(np.mean((actions[:,:10]-gt[:,:10])**2)))};predictions[f'e{eid}_{label}']=np.array(chunks)
  rows.append(row);print('VIDEO_PARITY',eid,row['raw'],row['decoded'],flush=True)
 summary={label:{'abrupt_trajectories':sum(r[label]['events']>0 for r in rows),'abrupt_events':sum(r[label]['events'] for r in rows),'mean_action_rmse_rad':float(np.mean([r[label]['action_rmse_rad'] for r in rows]))} for label in ['raw','decoded']}
 np.savez_compressed(a.out/'predictions.npz',**predictions);(a.out/'REPORT.json').write_text(json.dumps({'summary':summary,'rows':rows,'frames':frames,'method':'Actual saved training video backend and LeRobotDataset image retrieval; exactq/prompt verified. For each expert replan RGB, restore sameCUDA RNG between raw and decoded predictions, then continue freshnoise stream. Seed0, eight demonstrations, h10stitch.','limitations':'Teacher-forced and only two geometrygroups, not physical policy evaluation. Tests compression/decoding sensitivity, not complete training-inference equivalence. No live RPC change.','goal_complete':False},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
