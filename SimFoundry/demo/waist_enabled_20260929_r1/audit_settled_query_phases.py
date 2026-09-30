"""Development phase exposure diagnosis only; no diagnostic promotion."""
from pathlib import Path
import sys,json,hashlib,numpy as np
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.query_phases import episode_query_phases
from simfoundry.data.search_reward import terminal_search_scores
run=Path(sys.argv[1]);rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'quality.json').exists():continue
 quality=json.loads((ep/'quality.json').read_text());row=dict(episode=ep.name,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest())
 with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  task=str(z['task_id']);_,fit=terminal_search_scores([quality],[0 if task=='push_box_to_bin' else 1],{k:tr[k][:,None] for k in tr.files},{k:ori[k][:,None] for k in ori.files})
  if not quality['passed'] or not fit[0]['search_success']:row.update(phase_diagnosis_skipped=True,reason='Failed original task/pose; not a candidate for train exposure')
  else:
   control=json.loads((ep/'expert_control.json').read_text())
   try:
    phases=episode_query_phases(task,z['q'],z['action'],control);first_release=next((r['step'] for r in control if r['mode'] in ['goal_release','top_release','bypass_release']),None)
    row.update(phase_counts=phases['counts'],terminal_start=phases['terminal_start'],first_release=first_release,active_release_withdrawal_frames=phases['terminal_start']-first_release if first_release is not None else None,definition=phases['definition'])
   except ValueError as exc:row.update(phase_diagnosis_skipped=True,reason=str(exc))
 rows.append(row)
out=dict(rows=rows,labeler_source_sha256=hashlib.sha256((root.parents[1]/'simfoundry/data/query_phases.py').read_bytes()).hexdigest(),scope='Completed development raw only; measures retained activity and settled tail with declared thresholds. No frozen train quota, no metadata conversion and no diagnostic approval.',training_ready=False)
(run/'SETTLED_QUERY_PHASE_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps([{k:v for k,v in r.items() if k not in ['raw_sha256','definition']} for r in rows],indent=2))
