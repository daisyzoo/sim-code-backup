"""Read-only push diagnostics; waits are explicitly excluded from projection.

No admission, changed gates, cropping or training distribution is implied.
"""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.query_phases import episode_query_phases
from simfoundry.data.search_reward import terminal_search_scores
run=Path(sys.argv[1]).resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[];camera=[];excluded=[]
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'quality.json').exists():continue
 quality=json.loads((ep/'quality.json').read_text())
 with np.load(ep/'raw.npz') as z:
  task=str(z['task_id']);q=z['q'];action=z['action']
 if task=='wait_no_package':
  excluded.append(dict(episode=ep.name,reason='Empty-table wait; push projection and phase exposure inapplicable'));continue
 assert task in {'push_box_to_bin','nudge_mailer_to_bin'}
 assert len(q)==quality['frames']==1200
 subprocess.run([sys.executable,str(root/'audit_run_camera_visibility.py'),str(ep)],check=True)
 projection=json.loads((ep/'CAMERA_VISIBILITY_AUDIT.json').read_text())
 assert len(projection['results'])==1
 camera.extend(projection['results'])
 with np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  _,fit=terminal_search_scores([quality],[0 if task=='push_box_to_bin' else 1],{k:tr[k][:,None] for k in tr.files},{k:ori[k][:,None] for k in ori.files})
 control=json.loads((ep/'expert_control.json').read_text())
 row=dict(episode=ep.name,task_id=task,raw_sha256=sha(ep/'raw.npz'),task_passed=quality['passed'],task_and_pose_passed=bool(quality['passed'] and fit[0]['search_success']),projection_sheet_sha256=sha(ep/'camera_projection_review.jpg'),actual_projection_review='pending')
 if row['task_and_pose_passed']:
  try:
   phases=episode_query_phases(task,q,action,control)
   release=next((r['step'] for r in control if r['mode'] in {'goal_release','top_release','bypass_release'}),None)
   row.update(phase_counts=phases['counts'],terminal_start=phases['terminal_start'],first_release=release,active_withdrawal_frames=phases['terminal_start']-release if release is not None else None,uniform_frame_terminal_fraction=phases['counts'].get('terminal',0)/len(q),phase_definition=phases['definition'])
  except ValueError as exc:row.update(phase_error=str(exc))
 else:row['phase_diagnosis_skipped']='Original task/pose failed; no train-exposure candidate'
 rows.append(row)
(run/'CAMERA_VISIBILITY_AUDIT.json').write_text(json.dumps(dict(results=camera,excluded=excluded,scope='Completed pushes only. Geometric projection, no occlusion certificate; overlays await actual review.',training_ready=False),indent=2))
subprocess.run([sys.executable,str(root/'audit_visibility_during_work.py'),str(run)],check=True,stdout=subprocess.DEVNULL)
report=dict(rows=rows,excluded=excluded,source_hashes={p.name:sha(p) for p in [Path(__file__),root/'audit_run_camera_visibility.py',root/'audit_visibility_during_work.py',root.parents[1]/'simfoundry/data/query_phases.py']},scope='Diagnostic, not admission. All complete failed pushes retained in visibility analysis; terminal phases measured only for original task/pose passes. Hypothetical uniform-frame exposure, not a claim about a trained sampler. Full raw frames preserved.',training_ready=False)
(run/'PUSH_LEARNING_INPUT_AUDIT.json').write_text(json.dumps(report,indent=2))
print(json.dumps([{k:v for k,v in r.items() if k not in {'raw_sha256','projection_sheet_sha256','phase_definition'}} for r in rows],indent=2))
