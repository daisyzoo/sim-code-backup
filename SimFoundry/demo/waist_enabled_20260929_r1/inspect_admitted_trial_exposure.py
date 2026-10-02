"""Inspect actual whole-group admitted frames; no conversion or sampler selection."""
from pathlib import Path
import argparse,collections,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent
sys.path.insert(0,str(W))
from prepare_closed_peak_trial_lerobot import build_query_phase_records,make_split
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(admission,out):
 admission=Path(admission).resolve();d=json.loads(admission.read_text())
 assert d['full_group_source_admitted'] is True
 assert d['approver_sha256']==sha(W/'approve_closed_peak_trial_group.py')
 group_review=admission.parent.parent/'GROUP_REVIEWS'/(d['group']+'.json')
 assert d['group_review_sha256']==sha(group_review)
 review=json.loads(group_review.read_text());assert review['full_group_checks_passed']
 for p,h in d['review_sha256'].items():assert sha(p)==h
 for p,h in review['evidence_sha256'].items():assert sha(p)==h
 records=d['records'];assert len(records)==5
 phases=build_query_phase_records(records);rows=[];counts=collections.Counter();by_task={}
 for record,phase in zip(records,phases['records']):
  c=phase['counts'];counts.update(c)
  task=record['task_id'];by_task.setdefault(task,collections.Counter()).update(c)
  rows.append(dict(episode=Path(record['path']).parent.name,task=task,planned_split=record['planned_split'],frames=phase['frames'],counts=c,terminal_fraction=c.get('terminal',0)/phase['frames']))
 total=sum(counts.values());assert total==4*1200+70
 # A real train-only group must not become a full train/validation dataset.
 split_probe=None
 if {r['planned_split'] for r in records}=={'train'}:
  try:make_split(records,set())
  except ValueError as exc:split_probe=dict(rejected=True,error=str(exc))
  else:raise AssertionError('Train-only group incorrectly accepted as global split')
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),group=d['group'],scope=__doc__,rows=rows,total_frames=total,query_counts=dict(counts),uniform_query_fractions={k:v/total for k,v in counts.items()},task_phase_counts=by_task,phase_metadata=phases,train_only_global_split_probe=split_probe,source_sha256={str(admission):sha(admission),str(group_review):sha(group_review),str(W/'prepare_closed_peak_trial_lerobot.py'):sha(W/'prepare_closed_peak_trial_lerobot.py'),str(Path(__file__)):sha(__file__)},dataset_converted=False,sampling_policy_selected=False,training_ready=False)
 with Path(out).open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:result[k] for k in ['group','rows','total_frames','query_counts','uniform_query_fractions','train_only_global_split_probe','dataset_converted','sampling_policy_selected']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('admission');p.add_argument('--out',required=True);a=p.parse_args();main(a.admission,a.out)
