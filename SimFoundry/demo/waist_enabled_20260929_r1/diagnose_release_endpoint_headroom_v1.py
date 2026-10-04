"""Recorded-data diagnosis of release threshold versus planning endpoint.
No threshold change, command replay, physics claim, data admission or mode relabel.
"""
from pathlib import Path
import collections,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease
from simfoundry.data.reach_sweep import ready_to_release
from simfoundry.data.query_phases import episode_query_phases
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());rows=[];sources={str(Path(__file__)):sha(Path(__file__))}
for run in ['front_loaded_z_quarter_physical_r2','front_effective_height_physical_r1']:
 for ep in sorted((W/run).glob('case_*/layout_*')):
  if not (ep/'READY_FOR_AUDIT.json').exists() or 'wait_no_package' in ep.name:continue
  fr=read(ep/'frontal_bypass.json');plan=fr['plan'];initial_y=plan['initial_target_xyz'][1];direction=plan['direction'];threshold=max(.205,direction*initial_y+.16);monitor=ConfirmedPositionRelease(initial_y,direction);basic_true=[];margin_true=[];mismatch=[]
  for r in fr['rows']:
   target=r['observed_target'];basic=monitor.observe(target);margin=bool(basic and ready_to_release(initial_y,target[1],direction))
   if basic:basic_true.append(r['step'])
   if margin:margin_true.append(r['step'])
   if margin!=r['terminal_position_confirmed']:mismatch.append(r['step'])
  with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'];u=z['action'];task=str(z['task_id'])
  controls=read(ep/'expert_control.json');error=None
  try:phase=episode_query_phases(task,q,u,controls)
  except ValueError as e:error=str(e);phase=None
  actual=np.asarray([r['observed_target'] for r in fr['rows']]);candidate=plan.get('initial_top_proposal',{});goal=candidate.get('goal_y') if plan.get('initial_top_selected') else None;quality=read(ep/'quality.json')
  row=dict(run=run,episode=ep.name,initial_top_selected=plan.get('initial_top_selected',False),saved_quality_passed=quality['passed'],query_phase_error=error,query_phase_counts=None if phase is None else phase['counts'],last_mode=fr['rows'][-1]['mode'],release_threshold_signed_y_m=threshold,planned_signed_goal_y_m=None if goal is None else direction*goal,planned_headroom_over_release_m=None if goal is None else direction*goal-threshold,final_observed_shortfall_to_release_m=threshold-direction*actual[-1,1],minimum_observed_shortfall_to_release_m=float(threshold-np.max(direction*actual[:,1])),basic_position_stability_true_frames=len(basic_true),margin_position_confirmed_frames=len(margin_true),recorded_monitor_mismatch_steps=mismatch,final_feedback=fr['rows'][-1].get('clearance_feedback'),training_ready=False)
  rows.append(row)
  for n in ['raw.npz','frontal_bypass.json','expert_control.json','quality.json','READY_FOR_AUDIT.json']:sources[str(ep/n)]=sha(ep/n)
for n in ['confirmed_position_release.py','reach_sweep.py','query_phases.py','top_contact_bypass.py','tabletop_route_candidates.py','initial_top_route_candidate.py','initial_top_route.py']:
 p=ROOT/'simfoundry/data'/n;sources[str(p)]=sha(p)
assert len(rows)>=10
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,conclusion='Direct route plans exactly the release boundary with no positive tracking headroom. Where actual target stays below it, original margin monitor cannot release even after original basic position/stability passes. This establishes the stopping-condition issue, not the mechanical cause of tracking error or a safe headroom size. Query-phase failure is distinct from original task/pose quality failure.',next_experiment_option='After current isolated height comparison, consider separately adding planning endpoint headroom with freshly recomputed full obstacle/table/path guards; retain original release and quality thresholds. No candidate installed or approved by this diagnosis.',thresholds_changed=False,physics_started=False,training_ready=False)
p=W/'front_effective_height_physical_r1/RELEASE_ENDPOINT_HEADROOM_DIAGNOSIS_V1.json'
with p.open('x') as f:json.dump(out,f,indent=2)
for r in rows:print(json.dumps({k:r[k] for k in ['run','episode','saved_quality_passed','query_phase_error','planned_headroom_over_release_m','final_observed_shortfall_to_release_m','basic_position_stability_true_frames','margin_position_confirmed_frames','recorded_monitor_mismatch_steps']}))
