#!/usr/bin/env python3
"""Teacher-forced near/far branch audit at one demonstrated frame; no heldout inputs."""
import argparse,collections,hashlib,json,os
from pathlib import Path
import numpy as np
import torch
from pi05_policy_server import Pi05Server


def main():
    p=argparse.ArgumentParser();p.add_argument('--frame',type=int,required=True);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if not 0 <= a.frame <= 100:raise ValueError('frame must have a full50-action target')
    if a.out.exists():raise FileExistsError(a.out)
    a.out.mkdir(parents=True)
    records=json.loads((a.dataset/'meta/paired_provenance.json').read_text())['records'];split=json.loads((a.dataset/'meta/train_validation_split.json').read_text());stats=json.loads((a.dataset/'meta/train_only_stats.json').read_text())['action'];scale=np.asarray(stats['max'])-np.asarray(stats['min']);scale=np.where(scale>1e-6,scale,1.)
    ix=[*range(13,23),12];groups=collections.defaultdict(list)
    for i,row in enumerate(records):
        if row['task_id']=='wait_no_package':continue
        partition='train' if i in split['train'] else 'validation';path=Path(row['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['hash']
        with np.load(path,allow_pickle=False) as z:
            meta=json.loads(str(z['collect_meta']));item={'record':row,'rgb':z['rgb'][a.frame].transpose(1,2,0).copy(),'q':z['q'][a.frame,ix].copy(),'gt':z['action'][a.frame:a.frame+50,ix].copy(),'distance':'far' if meta['layout']['box_xyz' if row['task_id']=='push_box_to_bin' else 'mailer_xyz'][0]>=.48 else 'near'}
        groups[(partition,row['geometry_group'],row['task_id'])].append(item)
    args=argparse.Namespace(policy_path=a.checkpoint,dataset_root=a.dataset,repo_id='local/paired_spatial_pilot40_20260928',tokenizer_path=Path('/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224'),device='cuda:0',seed=0,num_inference_steps=10)
    server=Pi05Server(args);server.warmup();trials=[];pairs=[];predictions={}
    for (partition,group,task),items in sorted(groups.items()):
        assert len(items)==2 and {x['distance'] for x in items}=={'near','far'}
        assert items[0]['record']['exported_prompt']==items[1]['record']['exported_prompt']
        if a.frame==0:assert np.array_equal(items[0]['q'],items[1]['q'])
        active=slice(0,5) if task=='nudge_mailer_to_bin' else slice(5,10)
        for seed in [0,1,2]:
            outputs=[];correct=[]
            for j,item in enumerate(items):
                torch.manual_seed(seed);np.random.seed(seed)
                pred=server.infer(item['rgb'],item['q'],item['record']['exported_prompt']);other=items[1-j];assert pred.shape[0]>=50
                ec=(pred[:50,active]-item['gt'][:,active])/scale[active];eo=(pred[:50,active]-other['gt'][:,active])/scale[active];mc=float(np.mean(ec**2));mo=float(np.mean(eo**2));ok=mc<mo
                key=f"{partition}_{group}_{task}_{item['distance']}_seed{seed}";predictions[key]=pred;outputs.append(pred);correct.append(ok)
                trials.append({'partition':partition,'group':group,'task':task,'target_distance':item['distance'],'seed':seed,'closer_to_correct_demo_branch':ok,'correct_branch_normalized_mse':mc,'opposite_branch_normalized_mse':mo,'correct_branch_raw_rmse_rad':float(np.sqrt(np.mean((pred[:50,active]-item['gt'][:,active])**2))),'raw_path':item['record']['path'],'raw_sha256':item['record']['hash'],'prediction_key':key})
            pairs.append({'partition':partition,'group':group,'task':task,'seed':seed,'both_image_assignments_choose_correct_branch':all(correct),'predicted50_action_rmse_between_images_rad':float(np.sqrt(np.mean((outputs[0][:50]-outputs[1][:50])**2)))})
        print('BRANCH_AUDIT',partition,group,task,'complete',flush=True)
    summary=[]
    for partition in ['train','validation']:
        for task in ['nudge_mailer_to_bin','push_box_to_bin']:
            for distance in ['near','far']:
                rs=[r for r in trials if r['partition']==partition and r['task']==task and r['target_distance']==distance]
                summary.append({'partition':partition,'task':task,'target_distance':distance,'correct_demo_branch':sum(r['closer_to_correct_demo_branch'] for r in rs),'total':len(rs)})
    out={'frame':a.frame,'checkpoint':str(a.checkpoint.resolve()),'dataset':str(a.dataset.resolve()),'summary':summary,'pairs':pairs,'trials':trials,'method':'Teacher-forced observations: use actual RGB and corresponding11q at the requested demonstration frame. Same flow seed for paired category assignments. Both image and state differ after startup, so this is NOT an image-only counterfactual. Compare next50 actions to paired near/far demonstrations using active-arm range-normalized MSE. No physical rollout or active-server RPC.','limitations':'Nearest-demo branch is an open-loop diagnostic, not task success. Trajectory distance can mix target choice, timing and shape effects. No heldout evaluation inputs used, no training/labels changed.'}
    np.savez_compressed(a.out/'predictions.npz',**predictions);(a.out/'REPORT.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
