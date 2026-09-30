"""Opt-in early-prefix sampling; keeps each episode's exact per-epoch draw count."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Sampler

PUSH_TASKS={'push_box_to_bin','nudge_mailer_to_bin'}


def prefix_weights(episodes, frames, records, train_ids, validation_ids, prefix_frames, prefix_weight):
    episodes=np.asarray(episodes,dtype=np.int64).reshape(-1);frames=np.asarray(frames,dtype=np.int64).reshape(-1)
    if len(episodes)!=len(frames) or not len(episodes):raise ValueError('Invalid frame table')
    if set(episodes)!=set(train_ids) or set(episodes)&set(validation_ids):raise ValueError('Sampler must contain exactly training episodes, no validation')
    if isinstance(prefix_frames,bool) or not isinstance(prefix_frames,(int,np.integer)) or not 1<=prefix_frames<=20 or not np.isfinite(prefix_weight) or not 1<=prefix_weight<=32:raise ValueError('Invalid prefix parameters')
    weights=np.ones(len(episodes),dtype=np.float64);rows=[]
    for eid in sorted(set(episodes)):
        idx=np.flatnonzero(episodes==eid);n=len(idx)
        if not np.array_equal(np.sort(frames[idx]),np.arange(n)):raise ValueError('Missing or duplicate episode frames')
        task=records[int(eid)]['task_id']
        if task not in PUSH_TASKS|{'wait_no_package'}:raise ValueError('Unregistered task')
        if task in PUSH_TASKS:
            if n<prefix_frames:raise ValueError('Prefix longer than episode')
            weights[idx[frames[idx]<prefix_frames]]=prefix_weight
            weights[idx]*=n/weights[idx].sum()
        rows.append({'episode_index':int(eid),'task_id':task,'frames':n,'weight_sum':float(weights[idx].sum()),'prefix_weight_sum':float(weights[idx[frames[idx]<prefix_frames]].sum())})
    return weights,rows


class EpisodePrefixSampler(Sampler):
    """Resample inside push episodes, then shuffle; keep episode/task mass exact."""
    def __init__(self, episodes, weights, seed):
        episodes=np.asarray(episodes,dtype=np.int64).reshape(-1);weights=np.asarray(weights,dtype=np.float64)
        if not len(episodes) or weights.ndim!=1 or len(episodes)!=len(weights) or not np.isfinite(weights).all() or (weights<=0).any():raise ValueError('Invalid weights')
        self.length=len(episodes);self.generator=torch.Generator().manual_seed(int(seed));self.groups=[]
        for eid in sorted(set(episodes)):
            idx=np.flatnonzero(episodes==eid);local=weights[idx]
            self.groups.append((torch.as_tensor(idx,dtype=torch.long),torch.as_tensor(local,dtype=torch.double),bool(np.ptp(local)>0)))

    def __len__(self):return self.length

    def __iter__(self):
        draws=[]
        for idx,weights,weighted in self.groups:
            if weighted:draws.append(idx[torch.multinomial(weights,len(idx),replacement=True,generator=self.generator)])
            else:draws.append(idx)  # Waits/unweighted controls retain every original frame once.
        values=torch.cat(draws);order=torch.randperm(len(values),generator=self.generator)
        return iter(values[order].tolist())


def build_prefix_sampler(dataset, policy_path, seed):
    path=Path(policy_path);policy=json.loads(path.read_text());root=Path(dataset.root).resolve()
    if policy.get('version')!=1 or policy.get('approved_for_training') is not True:raise ValueError('Prefix policy not activated')
    if policy.get('strategy')!='balanced_episode_prefix' or Path(policy['dataset_root']).resolve()!=root or policy['seed']!=seed:raise ValueError('Prefix policy configuration mismatch')
    for name,digest in policy['metadata_sha256'].items():
        if name not in {'paired_provenance.json','train_validation_split.json','train_only_stats.json'}:raise ValueError('Unexpected metadata binding')
        if hashlib.sha256((root/'meta'/name).read_bytes()).hexdigest()!=digest:raise ValueError('Dataset metadata changed')
    if set(policy['metadata_sha256'])!={'paired_provenance.json','train_validation_split.json','train_only_stats.json'}:raise ValueError('Incomplete metadata binding')
    records=json.loads((root/'meta/paired_provenance.json').read_text())['records'];split=json.loads((root/'meta/train_validation_split.json').read_text())
    episodes=np.asarray(dataset.hf_dataset['episode_index'],dtype=np.int64).reshape(-1);frames=np.asarray(dataset.hf_dataset['frame_index'],dtype=np.int64).reshape(-1)
    weights,rows=prefix_weights(episodes,frames,records,split['train'],split['validation'],policy['prefix_frames'],policy['prefix_weight'])
    if len(weights)!=len(dataset) or len(weights)!=policy['expected_training_frames']:raise ValueError('Training frame budget changed')
    preview=np.asarray(list(EpisodePrefixSampler(episodes,weights,seed)))
    for row in rows:
        eid=row['episode_index'];selected=preview[episodes[preview]==eid];assert len(selected)==row['frames']
        row['first_epoch_prefix_draws']=int((frames[selected]<policy['prefix_frames']).sum())
        row['first_epoch_draws']=len(selected)
    report={'passed':True,'policy':policy,'policy_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'training_frames':len(weights),'preserves_exact_episode_and_task_draw_counts':True,'validation_episodes_sampled':[],'per_episode':rows,'note':'Only within-episode frame exposure changes. Original observations, actions, prompts, splits and normalization remain unchanged.'}
    return EpisodePrefixSampler(episodes,weights,seed),report
