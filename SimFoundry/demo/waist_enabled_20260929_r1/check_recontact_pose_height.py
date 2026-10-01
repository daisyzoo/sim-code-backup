"""Unchanged original height replay plus explicit joint-path log semantics.
Synthetic event sequences cannot establish physical or complete-task success.
"""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_recontact_pose_height import verify_rows
from audit_rear_short_recovery_live import verify_rows as original_verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();results=[]
for ep in sorted((w/'rear_short_recovery_groups_r1').glob('case_*/layout_*')):
 if not (ep/'frontal_bypass.json').exists():continue
 fr=json.loads((ep/'frontal_bypass.json').read_text());controls={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};out=verify_rows(fr['rows'],controls,fr['plan'],True);assert out==original_verify(fr['rows'],controls,fr['plan'],True)
 results.append(dict(episode=ep.name,selected=out['selected'],frames=out['frames'],source_sha256={n:sha(ep/n) for n in ['frontal_bypass.json','expert_control.json']}))
assert len(results)==8
fixture=w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json';data=json.loads(fixture.read_text());paths=[];negative=[]
for case in data['rows']:
 ep=w/'unloaded_wrist_prior_groups_r1'/('case_'+case['episode'].split('_')[1])/case['episode'];fr=json.loads((ep/'frontal_bypass.json').read_text());orig={r['step']:r for r in fr['rows']}
 for plant in case['plants']:
  start=case['step'];rows=copy.deepcopy(fr['rows'][:start-1]);events={};controls={r['step']:dict(target_xyz=r['target_xyz']) for r in rows}
  for event in plant['trace']:
   t=event['context']['step'];row=copy.deepcopy(orig[start]);row['step']=t;row['mode']='top_press' if event['kind']=='handover' else 'top_cross';row['recontact_pose_phase']='measured_handover' if event['kind']=='handover' else 'tracking';row['recontacts']=event['context']['recontacts'];row['observed_support_xyz']=event.get('observed_support_xyz',np.array(event['context']['observed_hand_pose'])[:3,3].tolist());row['contact_load']['applied_z_bias_m']=0.
   if event['kind']=='handover':row['target_xyz']=event['observed_support_xyz']
   rows.append(row);controls[t]=dict(target_xyz=row['target_xyz']);events[t]=event
  out=verify_rows(rows,controls,fr['plan'],True,events);paths.append(dict(episode=case['episode'],start=start,plant=plant['summary']['plant'],events=len(events)))
  # Guard the exception: an executed top_release can never be relabelled a path.
  bad=copy.deepcopy(rows);bad[-1]['mode']='top_release'
  try:verify_rows(bad,controls,fr['plan'],True,events)
  except AssertionError:negative.append('release_cannot_be_joint_path')
  else:raise AssertionError('Release relabel accepted')
out=dict(passed=True,scope=__doc__,parent_replays=results,synthetic_paths=paths,rejected_corruptions=len(negative),fixture_sha256=sha(fixture),source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_recontact_pose_height.py',w/'audit_rear_short_recovery_live.py']},physical_validation=False,training_ready=False)
(w/'staged_recontact_pose/HEIGHT_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(results),len(paths),len(negative),flush=True)
