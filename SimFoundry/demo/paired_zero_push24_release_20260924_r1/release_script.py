from pathlib import Path
import sys,json,hashlib,shutil
sys.path.insert(0,'SimFoundry')
from simfoundry.data.schema import load_episode
from simfoundry.data.paired_sorting import audit_rollout,audit_pair
import numpy as np
source=Path('SimFoundry/demo/paired_zero_pilot32_20260924_r1')
out=Path('SimFoundry/demo/paired_zero_push24_release_20260924_r1')
assert not out.exists()
review=json.loads((source/'review.json').read_text())
paths=[];results=[]
for lid in range(10,22):
 eps=[];reports=[]
 for task in ('push_box_to_bin','nudge_mailer_to_bin'):
  path=source/f'layout_{lid:04d}_{task}/raw.npz'
  assert review['episodes'][str(path.relative_to(source))]==hashlib.sha256(path.read_bytes()).hexdigest()
  ep=load_episode(path)
  with np.load(path.parent/'trace.npz') as tr:report=audit_rollout(task,ep.q,ep.action,dict(tr))
  assert report['passed'] and json.loads((path.parent/'quality.json').read_text())['passed']
  eps.append(ep);reports.append(report);paths.append(path)
 pair=audit_pair(*eps);assert pair['passed']
 results.append({'layout':eps[0].collect_meta['layout'],'episodes':reports,'pair':pair})
assert len(paths)==24
out.mkdir()
for path in paths:shutil.copytree(path.parent,out/path.parent.name)
shutil.copytree(source/'source_snapshot',out/'source_snapshot')
provenance=json.loads((source/'provenance.json').read_text())
provenance['release_scope']={'layouts':12,'wait_episodes':0,'layout_start':10}
provenance['release']={'source':str(source.resolve()),'reason':'Original batch stopped on independent wait workspace-check bug. All 12 previously completed push pairs preserved unchanged, individually reaudited; no failed push removed or rerun. Failed wait is not released.',
 'source_status':json.loads((source/'STATUS.json').read_text()),'original_args_unchanged':True,
 'release_audit_sha256':hashlib.sha256(Path('SimFoundry/simfoundry/data/paired_sorting.py').read_bytes()).hexdigest()}
(out/'provenance.json').write_text(json.dumps(provenance,indent=2))
(out/'manifest.json').write_text(json.dumps(results,indent=2))
review['approved']=True;review['scope']='All 24 pushing trajectories only; complete 12 original pairs, no failed wait.'
(out/'review.json').write_text(json.dumps(review,indent=2))
(out/'STATUS.json').write_text(json.dumps({'training_ready':False,'status':'numeric_pass_visual_review_pending','note':'Visual review approved; exported dataset audit still required.'},indent=2))
shutil.copy2(__file__,out/'release_script.py')
print('Released all 24 push trajectories after reauditing, no raw changes:',out)
