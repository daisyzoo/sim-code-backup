#!/usr/bin/env python3
"""Fixed-image/noise small-state sensitivity; diagnostic only, no training changes."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import torch
from pi05_policy_server import Pi05Server

def main():
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=False,parents=True)
 records=json.loads((a.dataset/'meta/paired_provenance.json').read_text())['records'];split=json.loads((a.dataset/'meta/train_validation_split.json').read_text());stats=json.loads((a.dataset/'meta/train_only_stats.json').read_text())['action'];scale=np.maximum(np.array(stats['max'])-np.array(stats['min']),1e-6);scale[-1]=1
 selected=[(i,r) for i,r in enumerate(records) if r.get('geometry_group') in ['candidate_07_center','candidate_14_center']];assert len(selected)==8
 ix=[*range(13,23),12];items=[]
 for eid,r in selected:
  path=Path(r['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==r['hash']
  with np.load(path) as z:
   meta=json.loads(str(z['collect_meta']));dist='far' if meta['layout']['box_xyz' if r['task_id']=='push_box_to_bin' else 'mailer_xyz'][0]>=.48 else 'near'
   for t in [10,30,60]:items.append({'episode':eid,'group':r['geometry_group'],'partition':'train' if eid in split['train'] else 'validation','frame':t,'task':r['task_id'],'distance':dist,'prompt':r['exported_prompt'],'q':z['q'][t,ix].copy(),'rgb':z['rgb'][t].transpose(1,2,0).copy(),'gt':z['action'][t:t+50,ix].copy(),'raw_hash':r['hash']})
 server=Pi05Server(argparse.Namespace(policy_path=a.checkpoint,dataset_root=a.dataset,repo_id='local/paired_spatial_pilot40_20260928',tokenizer_path=Path('/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224'),device='cuda:0',seed=0,num_inference_steps=10));server.warmup();rows=[];predictions={}
 for it in items:
  rng=np.random.default_rng(81000+it['episode']*100+it['frame']);variants={'original':it['q'].copy(),'waist_zero':it['q'].copy(),'waist_sign_flip':it['q'].copy(),'arm_noise_005':it['q'].copy(),'waist_noise_0005':it['q'].copy()};variants['waist_zero'][-1]=0;variants['waist_sign_flip'][-1]*=-1;variants['arm_noise_005'][:10]+=np.clip(rng.normal(0,.005,10),-.01,.01);variants['waist_noise_0005'][-1]+=.0005
  base=None
  for variant,q in variants.items():
   torch.manual_seed(0);np.random.seed(0);pred=server.infer(it['rgb'],q,it['prompt']);base=pred if base is None else base
   scores=sorted((float(np.mean(((pred[:50]-other['gt'])/scale)**2)),other['task'],other['distance']) for other in items if other['group']==it['group'] and other['frame']==it['frame'])
   key=f"e{it['episode']}_t{it['frame']}_{variant}";predictions[key]=pred
   rows.append({k:it[k] for k in ['episode','group','partition','frame','task','distance','raw_hash']}|{'variant':variant,'max_q_perturbation_rad':float(np.max(np.abs(q-it['q']))),'first10_action_rmse_change_rad':float(np.sqrt(np.mean((pred[:10,:10]-base[:10,:10])**2))),'first10_max_action_change_rad':float(np.max(np.abs(pred[:10,:10]-base[:10,:10]))),'nearest_task':scores[0][1],'nearest_distance':scores[0][2],'task_match':scores[0][1]==it['task'],'branch_match':scores[0][1:]==(it['task'],it['distance']),'prediction_key':key})
  print('STATE_SENSITIVITY',it['episode'],it['frame'],'done',flush=True)
 summary=[]
 for variant in variants:
  rs=[x for x in rows if x['variant']==variant];summary.append({'variant':variant,'total':len(rs),'task_matches':sum(x['task_match'] for x in rs),'branch_matches':sum(x['branch_match'] for x in rs),'max_first10_action_change_rad':max(x['first10_max_action_change_rad'] for x in rs),'mean_first10_rmse_change_rad':float(np.mean([x['first10_action_rmse_change_rad'] for x in rs]))})
 np.savez_compressed(a.out/'predictions.npz',**predictions);(a.out/'REPORT.json').write_text(json.dumps({'checkpoint':str(a.checkpoint),'summary':summary,'rows':rows,'method':'Same demonstrated RGB and prompt, seed0 reset eachquery. Perturb only state; four expertbranches at same phase used as trajectory-distance proxy. Independent inference process, no live-server change.','limitations':'Synthetic state/image inconsistency, not physical recovery or success. Only two geometrygroups and one seed. No adoption of state masking/noise or training changes.','goal_complete':False},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
