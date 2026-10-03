"""Full old actual trajectories plus explicitly UNISSUED candidate prefix fixture.
No candidate future is taken from old observations after its first changed step.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_front_corridor_midpoint_observations import inspect
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};actual=[]
for run in ['front_initial_physical_r1','front_z_priority_physical_r1']:
 for ep in sorted((W/run).glob('case_*/layout_*')):
  p=ep/'frontal_bypass.json'
  if not p.exists():continue
  log=json.loads(p.read_text());tr=dict(np.load(ep/'trace.npz'));ori=dict(np.load(ep/'parcel_orientation.npz'));count=len(tr['box']);r=inspect(log['rows'],log['plan'],tr,ori,enabled=False,expected_steps=range(1,count));actual.append(dict(run=run,episode=ep.name,rows=count-1,selected=r['selected'],front_rows=r['rows'],guards=r.get('guard_rows',0)))
  for p in [p,ep/'trace.npz',ep/'parcel_orientation.npz']:sources[str(p)]=sha(p)
# Bound fixture produces only first differing candidate Cartesian row. Previous
# observations remain actual, and the fixture ends at that first unissued row.
p=W/'check_front_corridor_midpoint_draft.py';bound=json.loads((W/'staged_front_corridor_midpoint/DRAFT_CHECK.json').read_text())
for name,h in bound['source_sha256'].items():assert sha(name)==h,name
s=ast.parse(p.read_text());cut=next(i for i,n in enumerate(s.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='negatives' for t in n.targets));ns={'__file__':str(p),'__name__':'midpoint_observation_prefix_fixture'};exec(compile(ast.Module(body=s.body[:cut],type_ignores=[]),str(p),'exec'),ns)
ep=ns['ep'];log=json.loads((ep/'frontal_bypass.json').read_text());tr=dict(np.load(ep/'trace.npz'));ori=dict(np.load(ep/'parcel_orientation.npz'));rows=copy.deepcopy([r for r in log['rows'] if r['step']<=173]);plan=copy.deepcopy(log['plan']);plan['front_corridor_midpoint']=dict(enabled=True,phase='front_x_only',preserve_latched_stop=True,preserve_other_guards=True,table_margin_m=.005,original_extra_reserve_m=.003,extra_reserve_may_be_replanned=True,require_axis_and_diagonal_paths=True,training_ready=False,parcel_planning_margin_m=.012)
for row in rows:
 t=row['step'];args=dict(ns['args'],target=tr['mailer'][t],obstacle=tr['box'][t],quat=ori['mailer'][t],other_quat=ori['box'][t],hand_obstacle_gap_m=row['hand_obstacle_gap_m'],route_stage='front_x',prior_stop_reason=None)
 from simfoundry.data.tabletop_route_candidates import footprint_radii
 r=footprint_radii(args['size'],ori['mailer'][t].tolist());o=footprint_radii(args['other_size'],ori['box'][t].tolist());args['original_goal_x']=min(tr['box'][1,0]-footprint_radii(args['other_size'],ori['box'][1].tolist())[0]-footprint_radii(args['size'],ori['mailer'][1].tolist())[0]-.012-.003,tr['box'][t,0]-o[0]-r[0]-.012-.003)
 _,rec=ns['select'](**args);row['front_corridor_midpoint']=rec
 if t<173:assert not rec['changed']
 else:rows[-1]=dict(ns['on'],step=t)
result=inspect(rows,plan,tr,ori,enabled=True,expected_steps=range(1,174));assert result['changed_steps']==[173]
negative=[]
for label,edit in [('goal',lambda rr:rr[-1].__setitem__('route_goal_x',rr[-1]['route_goal_x']+.001)),('stage',lambda rr:rr[-1].__setitem__('route_stage','lateral_y')),('guard_claim',lambda rr:rr[-1].__setitem__('mode','front_guard_lift')),('missing_record',lambda rr:rr[10].pop('front_corridor_midpoint')),('prior_latch_claim',lambda rr:rr[-1]['front_corridor_midpoint'].__setitem__('prior_stop_reason','already_stopped'))]:
 bad=copy.deepcopy(rows);edit(bad)
 try:inspect(bad,plan,tr,ori,enabled=True,expected_steps=range(1,174))
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('accepted corrupted '+label)
sources.update(bound['source_sha256'])
for p in [Path(__file__),W/'audit_front_corridor_midpoint_observations.py',W/'audit_front_corridor_midpoint_record.py']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,actual_trajectory_checks=actual,total_actual_rows=sum(r['rows'] for r in actual),unissued_prefix_fixture=dict(rows=173,last_step_unissued=True,changed_steps=result['changed_steps'],future_after_changed_step_used=False),negative_cases_rejected=negative,source_sha256=sources,source_contract_complete=False,joint_execution_binding_complete=False,training_ready=False)
with (W/'staged_front_corridor_midpoint_integrated/CONTINUOUS_OBSERVATION_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','actual_trajectory_checks','scope']},indent=2))
