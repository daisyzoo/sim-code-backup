#!/usr/bin/env python3
"""Read-only nearest demonstrated-arm-state coverage; not a causal classifier."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--evaluation',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 records=json.loads((a.dataset/'meta/paired_provenance.json').read_text())['records'];split=json.loads((a.dataset/'meta/train_validation_split.json').read_text());stats=json.loads((a.dataset/'meta/train_only_stats.json').read_text())['observation.state'];scale=np.maximum(np.array(stats['q99'][:10])-np.array(stats['q01'][:10]),.01);ix=list(range(13,23));train=[];labels=[];validation=[]
 for eid in split['train']+split['validation']:
  r=records[eid];path=Path(r['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==r['hash']
  with np.load(path) as z:
   q=z['q'][:,ix].copy();meta=json.loads(str(z['collect_meta']));task=r['task_id'];distance='wait' if task=='wait_no_package' else ('far' if meta['layout']['box_xyz' if task=='push_box_to_bin' else 'mailer_xyz'][0]>=.48 else 'near')
  if eid in split['train']:
   train.extend(q);labels.extend([(eid,t,task,distance) for t in range(len(q))])
  else:validation.extend(q[10::10])
 train=np.array(train,dtype=np.float64)/scale;labels=np.array(labels,dtype=object)
 def nearest(q):
  ds=np.mean((train-q/scale)**2,axis=1);idx=int(np.argmin(ds));return float(np.sqrt(ds[idx])),idx,ds
 vd=[nearest(q)[0] for q in validation];threshold=float(np.quantile(vd,.95));rows=[]
 for distribution in ['spatial','original']:
  report=json.loads((a.evaluation/f'EVALUATION_prefix_{distribution}.json').read_text())
  for row in report['rows']:
   if row['task']=='wait_no_package':continue
   path=Path(row['path'])/'raw.npz'
   with np.load(path) as z:q=z['q'][:,ix].copy();meta=json.loads(str(z['collect_meta']))
   task=row['task'];distance='original' if distribution=='original' else ('far' if meta['layout']['box_xyz' if task=='push_box_to_bin' else 'mailer_xyz'][0]>=.48 else 'near')
   for t in range(10,len(q),10):
    d,i,ds=nearest(q[t]);eligible=labels[:,2]==task
    if distribution=='spatial':eligible &= labels[:,3]==distance
    correct=float(np.sqrt(np.min(ds[eligible])));rows.append({'distribution':distribution,'seed':row['seed'],'layout_id':row['layout_id'],'task':task,'distance':distance,'frame':t,'passed':row['passed'],'nearest_normalized_arm_rms':d,'correct_branch_nearest_rms':correct,'nearest_episode':int(labels[i,0]),'nearest_frame':int(labels[i,1]),'nearest_task':str(labels[i,2]),'nearest_distance':str(labels[i,3]),'above_validation95':d>threshold,'nearest_task_matches':labels[i,2]==task,'nearest_full_branch_matches':labels[i,2]==task and (distribution=='original' or labels[i,3]==distance)})
 summary=[]
 for dist in ['spatial','original']:
  for task in ['nudge_mailer_to_bin','push_box_to_bin']:
   rs=[x for x in rows if x['distribution']==dist and x['task']==task];summary.append({'distribution':dist,'task':task,'queries':len(rs),'above_validation95':sum(x['above_validation95'] for x in rs),'median_nearest_normalized_arm_rms':float(np.median([x['nearest_normalized_arm_rms'] for x in rs])),'nearest_task_matches':sum(x['nearest_task_matches'] for x in rs),'nearest_full_branch_matches':sum(x['nearest_full_branch_matches'] for x in rs)})
 a.out.write_text(json.dumps({'summary':summary,'validation_reference_queries':len(vd),'validation_nearest_arm_rms_median':float(np.median(vd)),'validation_nearest_arm_rms95':threshold,'rows':rows,'method':'Nearest10-arm-q demonstrated training state, all phases, normalized by trainingq99-q01 with .01 floor. Query actual replan frames10,20,...; no inference and no change to train data. Waist excluded to avoid over-weighting tiny passive motion.','limitations':'Nearest-state label is not observed model target choice. Threshold is only descriptive, uses one heldout geometry plus wait; correlated frames, no causal proof of data insufficiency. Original-layout branch comparison only checks task, because that geometry is absent from spatial40.','goal_complete':False},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
