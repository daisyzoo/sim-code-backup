"""Original task/pose recheck for already-written episodes; batch may be running."""
from pathlib import Path
import sys,json,hashlib,datetime,numpy as np
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.paired_sorting import audit_rollout
from simfoundry.data.search_reward import terminal_search_scores
run=Path(sys.argv[1]).resolve();rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'quality.json').exists():continue
 provenance=json.loads((ep.parent/'provenance.json').read_text());settings=provenance['args']
 with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  task=str(z['task_id']);key='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if key=='box' else 'box'
  report=audit_rollout(task,z['q'],z['action'],dict(tr),motion_protocol=settings['motion_protocol'],waist_limit_rad=settings['waist_limit_rad'],waist_wait_tolerance_rad=settings['waist_wait_tolerance_rad'])
  saved=json.loads((ep/'quality.json').read_text());_,fit=terminal_search_scores([report],[0 if key=='box' else 1],{k:tr[k][:,None] for k in tr.files},{k:ori[k][:,None] for k in ori.files})
  rows.append(dict(episode=ep.name,path=str(ep),original_task_pose_passed=bool(report['passed'] and saved['passed'] and fit[0]['search_success']),reasons=list(set(report['reasons']+saved['reasons'])),progress_m=report['metrics']['target_final_progress_m'],other_max_xy_m=report['metrics'][other+'_max_xy_m'],pose=fit[0],end_mode=saved['expert_end_mode'],raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
out=dict(completed_conditions=len(rows),passed_conditions=sum(r['original_task_pose_passed'] for r in rows),planned_conditions=len(json.loads((run/'PROTOCOL.json').read_text())['layout_ids'])*2,rows=rows,updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Recomputed original task+pose on completed raw only. Batch status, paired resets, actual visual review and all contact audits separate; no complete-group or training admission.',training_ready=False)
(run/'COMPLETED_CONDITIONS.json').write_text(json.dumps(out,indent=2));print(json.dumps({**{k:v for k,v in out.items() if k not in ('rows','scope')},'rows':[{k:v for k,v in r.items() if k not in ('path','raw_sha256','pose')} for r in rows]},indent=2))
