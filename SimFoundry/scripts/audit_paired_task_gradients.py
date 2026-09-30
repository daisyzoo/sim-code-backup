#!/usr/bin/env python3
"""Read-only paired task gradient cosines using actual training windows/processor."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import torch
from torch.utils.data._utils.collate import default_collate
from pi05_policy_server import Pi05Server
from lerobot.datasets.lerobot_dataset import LeRobotDataset, LeRobotDatasetMetadata
from lerobot.datasets.factory import resolve_delta_timestamps


def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    cfg=json.loads((a.checkpoint/'train_config.json').read_text()); dc=cfg['dataset'];root=Path(dc['root'])
    records=json.loads((root/'meta/paired_provenance.json').read_text())['records'];split=json.loads((root/'meta/train_validation_split.json').read_text());assert dc['episodes']==split['train']
    server=Pi05Server(argparse.Namespace(policy_path=a.checkpoint,dataset_root=root,repo_id=dc['repo_id'],tokenizer_path=Path('/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224'),device='cuda:0',seed=0,num_inference_steps=10))
    policy=server.policy;policy.train();policy.model.gradient_checkpointing_enable()
    params=[(n,p) for n,p in policy.named_parameters() if p.requires_grad]
    assert sum(p.numel() for n,p in params)==693422112
    meta=LeRobotDatasetMetadata(dc['repo_id'],root=str(root))
    ds=LeRobotDataset(dc['repo_id'],root=str(root),episodes=dc['episodes'],delta_timestamps=resolve_delta_timestamps(policy.config,meta),video_backend=dc['video_backend'],tolerance_s=dc['tolerance_s']);ds._ensure_hf_dataset_loaded()
    ep=np.asarray(ds.hf_dataset['episode_index']).reshape(-1);fr=np.asarray(ds.hf_dataset['frame_index']).reshape(-1);lookup={(int(e),int(t)):i for i,(e,t) in enumerate(zip(ep,fr))}
    pairs={}
    for eid in split['train']:
        r=records[eid]
        if r.get('geometry_group') in ['candidate_03_negative','candidate_07_center']:
            assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['hash']
            pairs.setdefault(r['layout_id'],{})[r['task_id']]=eid
    assert len(pairs)==4 and all(len(v)==2 for v in pairs.values())
    rows=[];return_value_missing=[]
    def grad(eid,t,seed):
        policy.zero_grad(set_to_none=True);server.preprocessor.reset()
        batch=server.preprocessor(default_collate([ds[lookup[eid,t]]]))
        torch.manual_seed(seed);np.random.seed(seed)
        with torch.autocast('cuda',dtype=torch.bfloat16): loss,detail=policy(batch)
        loss.backward()
        result={n:p.grad.detach().float().cpu().clone() for n,p in params if p.grad is not None}
        missing=[n for n,p in params if p.grad is None]
        print('NO_GRAD_PARAMETERS',missing,flush=True)
        assert result and all(torch.isfinite(v).all() for v in result.values()), 'Nonfinite/empty native gradients'
        for n,p in params:
            if n not in result: result[n]=torch.zeros(p.shape,dtype=torch.float32)
        return_value_missing.append({'episode':eid,'frame':t,'seed':seed,'parameters':missing})
        return float(loss.detach()),result,detail['loss_per_dim']
    def cosine(g,h,names):
        dot=0.;aa=0.;bb=0.
        for n in names:
            x=g[n].reshape(-1);y=h[n].reshape(-1)
            dot+=float(torch.dot(x,y));aa+=float(torch.dot(x,x));bb+=float(torch.dot(y,y))
        return {'cosine':dot/(aa*bb)**.5 if aa*bb else None,'first_norm':aa**.5,'second_norm':bb**.5,'dot':dot}
    for lid,pair in sorted(pairs.items()):
        first=pair['nudge_mailer_to_bin'];second=pair['push_box_to_bin']
        for t in [0,30,60]:
            for seed in [0,1]:
                l1,g,d1=grad(first,t,seed);l2,h,d2=grad(second,t,seed)
                groups={'all':list(g),'expert':[n for n in g if 'gemma_expert' in n],'action_projection':[n for n in g if 'action_in_proj' in n or 'action_out_proj' in n],'time':[n for n in g if 'time_mlp' in n]}
                row={'layout_id':lid,'geometry_group':records[first]['geometry_group'],'frame':t,'noise_seed':seed,'episodes':[first,second],'raw_sha256':[records[first]['hash'],records[second]['hash']],'loss':[l1,l2],'loss_per_dim':[d1,d2],'gradients':{name:cosine(g,h,ns) for name,ns in groups.items()}}
                del g,h;rows.append(row);print('GRADIENT_PAIR',lid,t,seed,'COS',row['gradients']['all']['cosine'],flush=True)
                (a.out/'PARTIAL.json').write_text(json.dumps(rows,indent=2))
    values=[r['gradients']['all']['cosine'] for r in rows]
    report={'checkpoint':str(a.checkpoint.resolve()),'dataset':str(root),'trainable_parameters':sum(p.numel() for n,p in params),'rows':rows,'no_grad_parameters':return_value_missing,'summary':{'pairs':len(rows),'negative_cosines':sum(x<0 for x in values),'mean_cosine':float(np.mean(values))},'method':'Actual selected training dataset RGB/q/action50/padding and saved preprocessor; native masked flow loss, bf16 autocast, full trainable gradients before clipping; paired tasks use same noise seed at same frame. No optimizer instantiated or parameter update. Two train geometry groups, both category assignments, frames0/30/60, seeds0/1.', 'limitations':'Local instantaneous gradient alignment at a completed checkpoint, not proof of destructive training interference or sufficient data. Different task trajectories have different RGB/q after initial frame; finite sample of correlated pairs. Shared noise is a diagnostic coupling, not production batching. No validation episodes read, no training or rollout success measured.','goal_complete':False}
    (a.out/'REPORT.json').write_text(json.dumps(report,indent=2));print('SUMMARY',report['summary'],flush=True)

if __name__=='__main__': main()
