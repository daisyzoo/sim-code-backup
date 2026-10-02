"""Bind converter source reviews only after complete original group audit.
Approval here means quality-review metadata; it does not train or claim policy success.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parents[1]))
from prepare_closed_peak_trial_lerobot import checked_sources
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prepare(run,group):
 run=Path(run).resolve();protocol=json.loads((run/'PROTOCOL.json').read_text());cmds=[c for c in protocol['commands'] if c['group_name']==group]
 if len(cmds)!=3 or sum(len(c['tasks']) for c in cmds)!=5 or sum(c['wait'] for c in cmds)!=1:raise ValueError('Unknown or incomplete registered group')
 gp=run/'GROUP_REVIEWS'/(group+'.json')
 if not gp.exists():return dict(ready=False,reason='Complete group review is not yet available',group=group),None
 result=json.loads(gp.read_text())
 if result.get('status')!='complete_group_audited' or result.get('full_group_checks_passed') is not True:
  return dict(ready=False,reason='Original complete group gates did not all pass',group=group),None
 expected={f"layout_{c['layout_id']}_{t}" for c in cmds for t in c['tasks']};rows=result['rows']
 assert len(rows)==5 and {r['episode'] for r in rows}==expected
 assert sha(W/'audit_closed_peak_trial_group.py')==result['auditor_sha256']
 assert all(r['fresh_source_numeric_pose']['passed'] and r['all_control_audits_passed'] and r['frames']==r['requested_frames'] for r in rows)
 for path,h in result['evidence_sha256'].items():assert sha(path)==h,path
 for path,h in protocol['frozen_files_sha256'].items():assert sha(path)==h,path
 roots=[];reviews=[]
 for c in cmds:
  root=run/f"case_{c['layout_id']}";roots.append(root);assert json.loads((root/'STATUS.json').read_text())['status']=='numeric_pass_visual_review_pending'
  assert sha(root/'waist_pilot_contract.json')==result['contract_sha256']==c['contract_sha256']
  episodes={}
  for task in c['tasks']:
   ep=root/f"layout_{c['layout_id']}_{task}";visual=json.loads((ep/'ACTUAL_REVIEW_BINDING.json').read_text());assert sha(ep/'raw.npz')==visual['raw_sha256']
   if c['wait']:assert visual['actual_visual_review']=='completed_actual_view_8RGB'
   else:assert visual['actual_sampled_visual_review']=='completed'
   episodes[str((ep/'raw.npz').relative_to(root))]=visual['raw_sha256']
  reviews.append(dict(approved=True,method='Actual sampled8RGB per episode and4external per push, exact fresh source, original task/pose/wait gates and full independent control/pressure audits; whole category-swap group retained.',episodes=episodes,group=group,group_review_sha256=sha(gp),known_image_limitations=[r['visual'].get('observations',r['visual'].get('finding','')) for r in rows],training_ready=False))
 return dict(ready=True,group=group,source_roots=[str(p) for p in roots],group_review_sha256=sha(gp),scope='Whole group passed; converter pair and global split checks still required.'),(roots,reviews)

def apply_prepared(run, group, report, prepared):
 roots,reviews=prepared;assert report['ready'] and all(not (root/'review.json').exists() for root in roots)
 out=Path(run)/'GROUP_ADMISSIONS';dest=out/(group+'.json');assert not dest.exists()
 serialized_reviews=[json.dumps(review,indent=2,allow_nan=False) for review in reviews]
 written=[];summary_created=False
 try:
  for root,payload in zip(roots,serialized_reviews):
   path=root/'review.json'
   with path.open('x') as f:
    written.append(path);f.write(payload)
  records=checked_sources(roots)
  assert len(records)==5 and {r['waist_pilot_contract_sha256'] for r in records}=={sha(roots[0]/'waist_pilot_contract.json')}
  result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),group=group,full_group_source_admitted=True,records=records,review_sha256={str(p):sha(p) for p in written},group_review_sha256=report['group_review_sha256'],approver_sha256=sha(__file__),global_train_validation_split_checked=False,dataset_converted=False,model_trained=False,training_ready=False)
  # Converter records contain pathlib.Path; serialize completely before opening.
  def encode(value):
   if isinstance(value,Path):return str(value)
   raise TypeError('Unsupported admission metadata type: '+type(value).__name__)
  payload=json.dumps(result,indent=2,default=encode,allow_nan=False)
  out.mkdir(exist_ok=True)
  with dest.open('x') as f:
   summary_created=True;f.write(payload)
 except BaseException:
  if summary_created:dest.unlink()
  for path,payload in zip(written,serialized_reviews):
   assert payload.startswith(path.read_text());path.unlink()
  raise
 return dict(group=group,full_group_source_admitted=True,episodes=len(records),dataset_converted=False,training_ready=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('group');p.add_argument('--apply',action='store_true');a=p.parse_args();report,prepared=prepare(a.run,a.group)
 if not a.apply or not report['ready']:print(json.dumps(report,indent=2));return
 print(json.dumps(apply_prepared(a.run,a.group,report,prepared)))

if __name__=='__main__':main()
