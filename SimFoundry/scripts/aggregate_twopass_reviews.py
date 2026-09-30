#!/usr/bin/env python3
"""Aggregate existing human/assistant image reviews, never perform image review."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.root.resolve();protocol=json.loads((root/'PROTOCOL.json').read_text());rows=[];sources=[];pending=[]
for group in protocol['groups']:
 for case in group.get('layouts', [{'layout_id': lid} for lid in group.get('layout_ids', [])]):
  lid=case['layout_id'];folder=root/f'review_layout_{lid}';review_path=folder/'visual_review.json'
  if not review_path.exists():pending.append(lid);continue
  review=json.loads(review_path.read_text());assert review['reviewed'] is True
  inventory=json.loads((folder/'inventory.json').read_text());assert len(inventory)==2
  expected={str((root/f'case_{lid}/layout_{lid}_{task}').resolve()) for task in ['push_box_to_bin','nudge_mailer_to_bin']}
  assert {str(Path(row['path']).resolve()) for row in inventory}==expected
  hashes=[]
  for row in inventory:
   ep=Path(row['path']).resolve();digest=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest();assert digest==row['raw_sha256'];quality=json.loads((ep/'quality.json').read_text());assert quality['passed']==row['passed'] and quality['reasons']==row['reasons'];hashes.append(digest)
   frame_ids=review.get('frame_indices')
   if frame_ids is None:
    rr=next(x for x in review['rows'] if x['raw_sha256']==digest);frame_ids=rr['frames']
   assert frame_ids==[0,79,159,239,319]
   rows.append(dict(**row,geometry_group=group['group'],split=group['split'],frame_indices=frame_ids))
  assert len(set(hashes))==2 and set(hashes)==set(review['raw_sha256'])
  sources.append(dict(path=str(review_path),sha256=hashlib.sha256(review_path.read_bytes()).hexdigest()))
assert len({r['raw_sha256'] for r in rows})==len(rows)
complete=not pending
if complete:
 result=json.loads((root/'RESULT.json').read_text());audit=json.loads((root/'FINAL_AUDIT.json').read_text());assert result['complete'] and audit['complete']
 assert {r['raw_sha256'] for r in rows}=={r['raw_sha256'] for r in audit['rows']}
report=dict(reviewed=complete,complete=complete,reviewed_episodes=len(rows),reviewed_unique_frames=5*len(rows),pending_layout_ids=pending,rows=rows,raw_sha256=[r['raw_sha256'] for r in rows],source_reviews=sources,method='Aggregates only existing actual five-keyframe image reviews with freshly verified raw hashes and quality records. Does not inspect images or approve training.',training_ready=False,goal_complete=False)
a.out.write_text(json.dumps(report,indent=2));print('Recorded reviews',len(rows),'episodes,',len(pending),'layouts pending; complete',complete)
