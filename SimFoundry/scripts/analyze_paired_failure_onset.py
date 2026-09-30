"""Locate sustained state departure and audit h10 execution from saved arrays."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo/recovery_protocol_20260928_r1'
coverage=json.loads((ROOT/'demo/paired_data_coverage_20260924_r1/coverage.json').read_text())
refs={}
for src in ('paired_zero_push24_release_20260924_r1','paired_zero_wait8_20260924_r2'):
 for p in sorted((ROOT/'demo'/src).glob('layout_*')):
  if int(p.name.split('_')[1]) not in {*range(10,20),*range(10000,10006)}: continue
  task=p.name.split('_',2)[2]
  with np.load(p/'raw.npz') as d: refs.setdefault(task,[]).append(d['q'][:,13:23])
rows=[]
for variant,folder,pattern in [('b','paired_zero_ab_experiment_20260924_r1','b_seed*/rollouts/layout_*'),('c4','paired_c4_experiment_20260924_r1','seed*/rollouts/layout_*')]:
 for p in sorted((ROOT/'demo'/folder).glob(pattern)):
  task=p.name.split('_',2)[2];bank=np.concatenate(refs[task]);d=np.load(p/'raw.npz');q=d['q'];a=d['action'];dist=[];nearest=[]
  for state in q[:,13:23]:
   ds=np.abs(bank-state).max(1);i=int(ds.argmin());dist.append(float(ds[i]));nearest.append(bank[i])
  threshold=max(.01,coverage['tasks'][task]['leave_one_layout_out']['p95_rad'])
  above=np.array(dist)>threshold
  onset=next((t for t in range(len(q)-2) if above[t:t+3].all()),None)
  chunks=json.loads((p/'policy_inferences.json').read_text());bounds=[x['step'] for x in chunks[1:]]
  raw_path=p/'policy_raw_actions.npz';raw=np.load(raw_path)['action'] if raw_path.exists() else a;ids=[*range(13,23),12]
  raw_errors=[];state_errors=[]
  for c in chunks:
   t=c['step'];pred=np.array(c['actions']);n=min(10,len(q)-t)
   raw_errors.append(float(np.abs(raw[t:t+n,ids]-pred[:n]).max()))
   state_errors.append(float(np.abs(q[t,ids]-c['state']).max()))
  jump=(np.flatnonzero(np.abs(np.diff(a[:,12:],axis=0)).max(1)>.08)+1).tolist()
  tr=np.load(p/'trace.npz');quality=json.loads((p/'quality.json').read_text())
  row={'variant':variant,'path':str(p.relative_to(ROOT)),'task':task,'passed':quality['passed'],'threshold_rad':threshold,'onset_frame':onset,'nearest_chunk_boundary_offset':None if onset is None else onset%10,'first_jump_frame':jump[0] if jump else None,'jump_frames':jump,'all_jumps_at_boundaries':all(t in bounds for t in jump),'comparison_source':'raw_requested' if raw_path.exists() else 'applied_action_includes_limits', 'max_raw_chunk_execution_error_rad':max(raw_errors),'max_inference_state_record_error_rad':max(state_errors),'chunk_start_steps_correct': [c['step'] for c in chunks]==list(range(0,len(q),10)), 'distances_rad':dist}
  if onset is not None:
   delta=q[onset,13:23]-nearest[onset];row['onset_state_delta_rad']=delta.tolist();row['dominant_joint_index_10d']=int(abs(delta).argmax())
  if task=='wait_no_package':
   spreads=np.maximum(*[np.linalg.norm(tr[f'palm_{s}']-tr[f'palm_{s}'][0],axis=1) for s in ('left','right')]);hit=np.flatnonzero(spreads>.015)
   row['first_wait_gate_violation_frame']=int(hit[0]) if len(hit) else None
  else:
   side='right' if task=='push_box_to_bin' else 'left';obj='box' if side=='right' else 'mailer';sign=-1 if side=='right' else 1
   progress=sign*(tr[obj][:,1]-tr[obj][0,1]);hit=np.flatnonzero(progress>.005)
   row['first_5mm_progress_frame']=int(hit[0]) if len(hit) else None
   row['final_progress_m']=float(progress[-1]);row['palm_height_at_onset_m']=None if onset is None else float(tr[f'palm_{side}'][onset,2])
  rows.append(row)
assert len(rows)==42
(OUT/'failure_onset.json').write_text(json.dumps(rows,indent=2))
for v in ('b','c4'):
 for task in refs:
  rs=[r for r in rows if r['variant']==v and r['task']==task]
  print(v,task,'onsets',[r['onset_frame'] for r in rs],'joints',[r.get('dominant_joint_index_10d') for r in rs])
print('execution errors',max(r['max_raw_chunk_execution_error_rad'] for r in rows),max(r['max_inference_state_record_error_rad'] for r in rows),'chunk schedule correct',all(r['chunk_start_steps_correct'] for r in rows))
