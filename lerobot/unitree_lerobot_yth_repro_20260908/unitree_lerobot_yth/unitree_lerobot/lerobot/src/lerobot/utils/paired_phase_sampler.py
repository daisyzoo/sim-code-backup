"""Opt-in train-query sampler; exact task/phase budgets and metadata bindings.

Caller must supply qualified train records, frozen phase labels and explicit
per-task/phase integer query quotas. No defaults imply a recommended exposure.
Returns dataset query indices; action chunks/padding remain dataset-owned.
"""
from collections import defaultdict
import numpy as np
PUSH={'push_box_to_bin','nudge_mailer_to_bin'}
PHASES={'start','active','terminal'}

def _integers(values,name):
 a=np.asarray(values)
 if a.ndim!=1 or a.dtype.kind not in 'iu' or not len(a):raise ValueError('Invalid integer '+name)
 return a.astype(np.int64)

def prepare_strata(episodes,frames,phases,records,train_ids,heldout_ids):
 episodes=_integers(episodes,'episodes');frames=_integers(frames,'frames');phases=np.asarray(phases)
 if phases.ndim!=1 or not len(episodes)==len(frames)==len(phases):raise ValueError('Frame table mismatch')
 if set(episodes)!=set(train_ids) or set(episodes)&set(heldout_ids):raise ValueError('Exact train-only coverage required')
 groups=defaultdict(lambda:defaultdict(dict))
 for eid in sorted(set(episodes)):
  idx=np.flatnonzero(episodes==eid);r=records[int(eid)];task=r['task_id'];group=r['geometry_group']
  if r.get('planned_split')!='train' or not isinstance(group,str) or not group:raise ValueError('Unbound train geometry')
  if task not in PUSH|{'wait_no_package'}:raise ValueError('Unknown task')
  if not np.array_equal(np.sort(frames[idx]),np.arange(len(idx))):raise ValueError('Missing or duplicate frame')
  expected=PHASES if task in PUSH else {'wait'}
  if set(phases[idx])!=expected:raise ValueError('Missing or invalid phase; no silent redistribution')
  for phase in sorted(expected):groups[(task,phase)][group][int(eid)]=idx[phases[idx]==phase]
 return {key:dict(value) for key,value in groups.items()},len(episodes)

def draw_queries(strata,quotas,*,seed,epoch):
 if set(quotas)!=set(strata):raise ValueError('Quotas must cover every task/phase exactly')
 if any(type(v) is not int or v<=0 for v in quotas.values()):raise ValueError('Positive integer quotas required')
 if type(seed) is not int or type(epoch) is not int or min(seed,epoch)<0:raise ValueError('Nonnegative integer seed/epoch required')
 rng=np.random.default_rng(np.random.SeedSequence([seed,epoch]));draws=[];report=[]
 def balanced(keys,n):
  # Random remainder allocation, counts within each allocation differ by <=1.
  keys=list(keys);order=rng.permutation(len(keys));return {k:n//len(keys)+int(i in order[:n%len(keys)]) for i,k in enumerate(keys)}
 for key in sorted(strata):
  groups=strata[key]
  for group,n in balanced(sorted(groups),quotas[key]).items():
   for eid,count in balanced(sorted(groups[group]),n).items():
    idx=groups[group][eid];draws.extend(rng.choice(idx,size=count,replace=True).tolist())
    report.append(dict(task=key[0],phase=key[1],geometry_group=group,episode=int(eid),queries=count,available_frames=len(idx)))
 draws=np.asarray(draws,dtype=np.int64);rng.shuffle(draws)
 return draws,report


import hashlib
import json
from pathlib import Path
from torch.utils.data import Sampler


class TaskPhaseSampler(Sampler):
    def __init__(self,strata,quotas,seed):
        self.strata,self.quotas,self.seed,self.epoch=strata,quotas,seed,0
    def __len__(self):return sum(self.quotas.values())
    def set_epoch(self,epoch):
        if type(epoch) is not int or epoch<0:raise ValueError('Invalid sampler epoch')
        self.epoch=epoch
    def __iter__(self):
        indices,_=draw_queries(self.strata,self.quotas,seed=self.seed,epoch=self.epoch)
        self.epoch+=1
        return iter(indices.tolist())


def _expand_phase_record(record):
    labels=[];n=record['frames']
    if type(n) is not int or n<=0:raise ValueError('Invalid phase frame count')
    for run in record['runs']:
        if (type(run['start']) is not int or type(run['end']) is not int or run['start']!=len(labels)
                or not run['start']<run['end']<=n or run['phase'] not in PHASES|{'wait'}):
            raise ValueError('Invalid phase run alignment')
        labels.extend([run['phase']]*(run['end']-run['start']))
    from collections import Counter
    if len(labels)!=n or dict(Counter(labels))!=record['counts']:raise ValueError('Phase counts/coverage mismatch')
    return np.asarray(labels)


def build_phase_sampler(dataset,policy_path,seed):
    path=Path(policy_path);policy=json.loads(path.read_text());root=Path(dataset.root).resolve()
    if (policy.get('approved_for_training') is not True or policy.get('strategy')!='task_phase_geometry_balanced'
            or Path(policy['dataset_root']).resolve()!=root or policy['seed']!=seed):
        raise ValueError('Unapproved or mismatched phase sampling policy')
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    if policy['sampler_source_sha256']!=sha(__file__):raise ValueError('Phase sampler source changed')
    names={'paired_provenance.json','train_validation_split.json','train_only_stats.json','episode_query_phases.json'}
    if set(policy['metadata_sha256'])!=names:raise ValueError('Incomplete phase dataset binding')
    for name,digest in policy['metadata_sha256'].items():
        if sha(root/'meta'/name)!=digest:raise ValueError('Phase metadata changed: '+name)
    provenance=json.loads((root/'meta/paired_provenance.json').read_text());records=provenance['records']
    split=json.loads((root/'meta/train_validation_split.json').read_text());stats=json.loads((root/'meta/train_only_stats.json').read_text())
    if set(stats['episode_indices'])!=set(split['train']):raise ValueError('Normalization does not use exact train split')
    phases=json.loads((root/'meta/episode_query_phases.json').read_text())
    if phases['labeler_source_sha256']!=policy['phase_labeler_source_sha256']:raise ValueError('Phase labeler version mismatch')
    by_id={r['episode_index']:r for r in phases['records']}
    if len(by_id)!=len(phases['records']) or set(by_id)!=set(range(len(records))):raise ValueError('Incomplete or duplicate phase episode mapping')
    episodes=np.asarray(dataset.hf_dataset['episode_index']).reshape(-1);frames=np.asarray(dataset.hf_dataset['frame_index']).reshape(-1)
    episodes=_integers(episodes,'episodes');frames=_integers(frames,'frames')
    if len(episodes)!=len(dataset) or len(episodes)!=policy['expected_training_frames']:raise ValueError('Train frame count changed')
    if set(episodes)!=set(split['train']) or set(episodes)&set(split['validation']):raise ValueError('Phase sampler must be train-only')
    table=np.empty(len(episodes),dtype='<U8');normalized={}
    for eid in sorted(set(episodes)):
        record=records[int(eid)];phase=by_id[int(eid)]
        if (record.get('motion_protocol')!='waist_yaw_enabled_v1' or not record.get('waist_pilot_contract_sha256')
                or phase['raw_sha256']!=record['hash'] or phase['task_id']!=record['task_id']
                or phase['definition']!=policy['phase_definition']):
            raise ValueError('Phase/raw/task/protocol definition mismatch')
        local=_expand_phase_record(phase);idx=np.flatnonzero(episodes==eid)
        if len(local)!=len(idx) or not np.array_equal(np.sort(frames[idx]),np.arange(len(idx))):raise ValueError('Phase/frame alignment changed')
        table[idx]=local[frames[idx]]
        normalized[int(eid)]=dict(record,geometry_group=record.get('geometry_group',record.get('wait_geometry_group')))
    strata,_=prepare_strata(episodes,frames,table,normalized,split['train'],split['validation'])
    quotas={(r['task_id'],r['phase']):r['queries'] for r in policy['quotas']}
    if len(quotas)!=len(policy['quotas']):raise ValueError('Duplicate phase quota')
    preview,exposure=draw_queries(strata,quotas,seed=seed,epoch=0)
    if len(preview)!=policy['queries_per_epoch']:raise ValueError('Query budget changed')
    report=dict(passed=True,policy=policy,policy_sha256=sha(path),training_frames=len(episodes),queries_per_epoch=len(preview),first_epoch_exposure=exposure,validation_episodes_sampled=[],full_original_frames_retained=True,note='Exact declared task/phase query mass; geometry/episode counts balanced within each stratum. Action chunks, observations and train-only normalization unchanged.')
    return TaskPhaseSampler(strata,quotas,seed),report
