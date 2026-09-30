"""Physical-radian nearest-state coverage audit; excludes held-out layouts."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo/paired_data_coverage_20260924_r1'
OUT.mkdir(exist_ok=True)
refs={}
for source in ('paired_zero_push24_release_20260924_r1','paired_zero_wait8_20260924_r2'):
 for p in sorted((ROOT/'demo'/source).glob('layout_*')):
  layout=int(p.name.split('_')[1]);task=p.name.split('_',2)[2]
  if layout not in {*range(10,20),*range(10000,10006)}:continue
  with np.load(p/'raw.npz') as d:q=d['q'][:,13:23];a=d['action'][:,13:23]
  refs.setdefault(task,[]).append((p.name,q,a))
def nearest(q,bank):
 return np.concatenate([np.abs(q[i:i+32,None]-bank[None]).max(2).min(1) for i in range(0,len(q),32)])
def summary(x):return {'median_rad':float(np.median(x)),'p95_rad':float(np.quantile(x,.95)),'max_rad':float(np.max(x))}
report={'method':'Nearest training state L-infinity distance across 10 arm joints, physical radians. Expert reference is leave-one-layout-out; model reference uses only training layouts. No success causality inferred.','tasks':{},'model_rollouts':[]}
for task,episodes in refs.items():
 loo=np.concatenate([nearest(q,np.concatenate([q2 for n2,q2,a2 in episodes if n2!=n])) for n,q,a in episodes])
 allq=np.concatenate([q for n,q,a in episodes]);alla=np.concatenate([a for n,q,a in episodes])
 report['tasks'][task]={'episodes':len(episodes),'frames':len(allq),'leave_one_layout_out':summary(loo),'q_joint_range_rad':np.ptp(allq,axis=0).tolist(),'action_abs_max_rad':float(abs(alla).max()),'near_static_action_transition_fraction':float(np.mean(np.concatenate([np.abs(np.diff(a,axis=0)).max(1)<.001 for n,q,a in episodes]))),'between_episode_same_time_q_max_rad':float(max(np.abs(q-episodes[0][1]).max() for n,q,a in episodes))}
 for variant,root,pattern in [('b','paired_zero_ab_experiment_20260924_r1','b_seed*/rollouts/layout_*'),('c4','paired_c4_experiment_20260924_r1','seed*/rollouts/layout_*')]:
  for p in sorted((ROOT/'demo'/root).glob(pattern)):
   if not p.name.endswith(task):continue
   with np.load(p/'raw.npz') as d:q=d['q'][:,13:23]
   dist=nearest(q,allq);quality=json.loads((p/'quality.json').read_text())
   report['model_rollouts'].append({'variant':variant,'path':str(p.relative_to(ROOT)), 'task':task,'passed':quality['passed'],**summary(dist),'fraction_above_expert_loo_p95':float(np.mean(dist>np.quantile(loo,.95)))})
(OUT/'coverage.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['tasks'],indent=2))
for v in ('b','c4'):
 for task in refs:
  rows=[r for r in report['model_rollouts'] if r['variant']==v and r['task']==task]
  print(v,task,'rollout median distance range',min(r['median_rad'] for r in rows),max(r['median_rad'] for r in rows))
