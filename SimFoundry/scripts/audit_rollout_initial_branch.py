#!/usr/bin/env python3
"""Classify recorded initial predictions against training-only expert prototypes."""
import argparse,json
from pathlib import Path
from collections import defaultdict
import numpy as np


def main():
 p=argparse.ArgumentParser();p.add_argument('--evaluation-root',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 records=json.loads((a.dataset/'meta/paired_provenance.json').read_text())['records'];split=json.loads((a.dataset/'meta/train_validation_split.json').read_text());stats=json.loads((a.dataset/'meta/train_only_stats.json').read_text())['action'];scale=np.asarray(stats['max'])-np.asarray(stats['min']);scale=np.where(scale>1e-6,scale,1.);templates=defaultdict(list);ix=[*range(13,23),12]
 for eid in split['train']:
  row=records[eid]
  if row['task_id']=='wait_no_package':continue
  with np.load(row['path'],allow_pickle=False) as z:
   m=json.loads(str(z['collect_meta']));task=row['task_id'];distance='far' if m['layout']['box_xyz' if task=='push_box_to_bin' else 'mailer_xyz'][0]>=.48 else 'near';templates[(task,distance)].append(z['action'][:50,ix].copy())
 rows=[]
 for log in sorted(a.evaluation_root.glob('prefix_spatial_seed*/*/layout_*/policy_inferences.json')):
  path=log.parent/'raw.npz'
  if not path.exists() or not (log.parent/'quality.json').exists():continue
  with np.load(path,allow_pickle=False) as z:
   task=str(z['task_id']);m=json.loads(str(z['collect_meta']))
  if task=='wait_no_package':continue
  distance='far' if m['layout']['box_xyz' if task=='push_box_to_bin' else 'mailer_xyz'][0]>=.48 else 'near';logs=json.loads(log.read_text());assert logs[0]['step']==0;pred=np.array(logs[0]['actions']);scores=[]
  for (t,d),protos in templates.items():scores.append({'task':t,'distance':d,'min_normalized_mse':min(float(np.mean(((pred[:50]-x)/scale)**2)) for x in protos)})
  scores.sort(key=lambda x:x['min_normalized_mse']);best=scores[0];quality=json.loads((log.parent/'quality.json').read_text());rows.append({'episode':str(log.parent),'seed':int(log.parents[2].name.split('seed')[-1]),'task':task,'distance':distance,'initial_task_match':best['task']==task,'initial_full_branch_match':best['task']==task and best['distance']==distance,'scores':scores,'formal_passed':quality['passed'],'formal_reasons':quality['reasons']})
 summary=[]
 for seed in sorted({x['seed'] for x in rows}):
  rs=[x for x in rows if x['seed']==seed];summary.append({'seed':seed,'completed_pushes':len(rs),'initial_task_match':sum(x['initial_task_match'] for x in rs),'initial_full_branch_match':sum(x['initial_full_branch_match'] for x in rs),'formal_passed':sum(x['formal_passed'] for x in rs)})
 a.out.write_text(json.dumps({'summary':summary,'rows':rows,'method':'Classify recorded step0 predicted50-action chunks by nearest training-only expert prototype among2tasks x near/far; full11-joint range-normalized MSE.','limitations':'Prototype matching is not true object selection or task success. Uses completed development rollouts; not new independent generalization evidence.'},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
