"""Offline train-query sampler candidate; never admits data or edits trajectories.

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
