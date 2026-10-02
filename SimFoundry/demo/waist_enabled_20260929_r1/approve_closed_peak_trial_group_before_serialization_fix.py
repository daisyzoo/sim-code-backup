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

def main():
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('group');p.add_argument('--apply',action='store_true');a=p.parse_args();report,prepared=prepare(a.run,a.group)
 if not a.apply or not report['ready']:print(json.dumps(report,indent=2));return
 roots,reviews=prepared;assert all(not (root/'review.json').exists() for root in roots)
 written=[]
 try:
  for root,review in zip(roots,reviews):
   path=root/'review.json'
   with path.open('x') as f:json.dump(review,f,indent=2)
   written.append(path)
  records=checked_sources(roots)
  assert len(records)==5 and {r['waist_pilot_contract_sha256'] for r in records}=={sha(roots[0]/'waist_pilot_contract.json')}
 except BaseException:
  for path,review in zip(written,reviews):
   assert json.loads(path.read_text())==review;path.unlink()
  raise
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),group=a.group,full_group_source_admitted=True,records=records,review_sha256={str(p):sha(p) for p in written},group_review_sha256=report['group_review_sha256'],approver_sha256=sha(__file__),global_train_validation_split_checked=False,dataset_converted=False,model_trained=False,training_ready=False)
 out=Path(a.run)/'GROUP_ADMISSIONS';out.mkdir(exist_ok=True)
 with (out/(a.group+'.json')).open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(group=a.group,full_group_source_admitted=True,episodes=len(records),dataset_converted=False,training_ready=False)))

if __name__=='__main__':main()
