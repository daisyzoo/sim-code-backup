"""Check actual recorded sampled actions, and reject missing/full or damaged data."""
from pathlib import Path
import json,sys,copy,hashlib,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w));from audit_rear_coupled_execution_live import inspect,replay_record
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[];rejected=0
for run in ['rear_core_slice_groups_r1','front_drive_increment_groups_r1','front_edge_speed_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';result=inspect(ep,True);assert result['passed'],result.get('errors');assert not result['complete_push_coverage'];t=result['records'][0]['step']
  coord=next(r for r in json.loads((ep/'coordination.json').read_text()) if r['step']==t);row=next(r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows'] if r['step']==t);expert=next(r for r in json.loads((ep/'expert_control.json').read_text()) if r['step']==t)
  with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23];prior=z['action'][t-1,12:23];actual=z['action'][t,12:23]
  spec=importlib.util.spec_from_file_location('bounded_check',ep.parent/'source_snapshot/simfoundry/data/bounded_ik.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);side='right' if cid==840001 else 'left'
  for kind in ['actual_action','recorded_q','expert_goal','active_side','jacobian_missing','terminal_override']:
   c=copy.deepcopy(coord);r=copy.deepcopy(row);e=copy.deepcopy(expert);u=actual.copy()
   if kind=='actual_action':u[1]+=.002
   if kind=='recorded_q':c['upper_q'][1]+=.002
   if kind=='expert_goal':e['target_xyz'][1]+=.002
   if kind=='active_side':c['active_side']='left' if side=='right' else 'right'
   if kind=='jacobian_missing':del c['control_jacobian_world']
   if kind=='terminal_override':c['terminal_joint_hold']=True
   try:replay_record(c,r,e,q,prior,u,side,m.bounded_damped_step)
   except (AssertionError,KeyError,ValueError):rejected+=1
   else:raise AssertionError(kind)
  reports.append(dict(run=run,episode=ep.name,**result));print(run,task,result['checked_push_frames'],result['expected_push_frames'],result['maximum_action_error_rad'],flush=True)
p=w/'staged_rear_coupled_progress_probe/EXECUTION_REPLAY_CHECK.json';assert not p.exists();p.write_text(json.dumps(dict(passed=True,episodes=reports,total_sampled_push_frames=sum(x['checked_push_frames'] for x in reports),negative_cases=rejected,auditor_sha256=sha(w/'audit_rear_coupled_execution_live.py'),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Actual sampled historical raw actions, no altered physical or synthetic action data. All six incomplete Jacobian coverage explicitly reported; future collector must record every rear top_push and standard audit require complete coverage.'),indent=2));print('PASSED',sum(x['checked_push_frames'] for x in reports),rejected)
