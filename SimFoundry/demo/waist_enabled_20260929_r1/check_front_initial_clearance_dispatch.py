"""Exact new self-clearance dispatch branch with independently checked actual-core commands.
Original full FK/pre/post/final-command code is retained by bound reverse diff.
This checks interface admission, not synthetic full runtime-body geometry.
"""
from pathlib import Path
import sys,json,ast,copy,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_front_initial_stage_self_clearance import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=W/'audit_front_initial_stage_self_clearance.py';tree=ast.parse(source.read_text());function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='audit');loop=next(x for x in ast.walk(function) if isinstance(x,ast.For) and ast.unparse(x.iter)=='coordinates');branch=next(x for x in loop.body if isinstance(x,ast.If) and "verified_unloaded_front_initial_joint_path" in ast.unparse(x.test))
program=ast.Module(body=[ast.For(target=ast.Name(id='c',ctx=ast.Store()),iter=ast.Name(id='coordinates',ctx=ast.Load()),body=[ast.Assign(targets=[ast.Name(id='t',ctx=ast.Store())],value=ast.Subscript(value=ast.Name(id='c',ctx=ast.Load()),slice=ast.Constant(value='step'),ctx=ast.Load())),branch,ast.Raise(exc=ast.Call(func=ast.Name(id='AssertionError',ctx=ast.Load()),args=[ast.Constant(value='wrong dispatch')],keywords=[]),cause=None)],orelse=[])],type_ignores=[]);code=compile(ast.fix_missing_locations(program),str(source),'exec')
data=json.loads((W/'FRONT_INITIAL_ACTUAL_CORE_CHECK.json').read_text());samples=data['records'][:2];assert len(samples)==2 and all(r['independent_first_command']['independent_command_passed'] and r['independent_selection']['passed'] for r in samples)
snapshot=W/'FRONT_INITIAL_CLEARANCE_DISPATCH_INPUT.json';assert not snapshot.exists();snapshot.write_text(json.dumps(dict(scope='Fixed first2 completed actual-core records from ongoing all8 recalculation; not full all8 result.',records=samples,training_ready=False),indent=2));rows=[]
for original in samples:
 event=copy.deepcopy(original['live_first_event']);t=event['context']['step'];q=np.zeros((t+1,11));u=q.copy();q[t]=event['context']['current'];u[t-1]=event['context']['previous_command'];u[t]=event['command']
 c=dict(step=t,controller_kind='verified_unloaded_front_initial_joint_path',front_initial_center_override=event,task_inputs=None,contact_normal_tracking=None)
 for label in ['verified','unverified','wrong_action','wrong_current','wrong_previous','wrong_controller','unexpected_region','unexpected_terminal','unexpected_edge','unexpected_intersection','conflicting_rear']:
  coordinate=copy.deepcopy(c);ev=copy.deepcopy(event);state=q.copy();action=u.copy();front={t:ev};verified={t:ev}
  if label=='unverified':front={};verified={}
  if label=='wrong_action':action[t,0]+=.001
  if label=='wrong_current':state[t,0]+=.001
  if label=='wrong_previous':action[t-1,0]+=.001
  if label=='wrong_controller':coordinate['controller_kind']='verified_unloaded_recontact_joint_path'
  if label=='unexpected_region':coordinate['region_joint_override']=True
  if label=='unexpected_terminal':coordinate['terminal_joint_hold']=True
  if label=='unexpected_edge':coordinate['joint_edge_refinement']=dict(override=True)
  if label=='unexpected_intersection':coordinate['joint_edge_clearance_intersection']={}
  if label=='conflicting_rear':coordinate['recontact_pose_override']=ev
  ns=dict(np=np,near=near,coordinates=[coordinate],q=state,u=action,verified_front_events=front,verified_events=verified,controller_frames=0);accepted=True
  try:exec(code,ns);assert ns['controller_frames']==1
  except (AssertionError,KeyError,ValueError):accepted=False
  assert accepted==(label=='verified'),(original['episode'],label);rows.append(dict(episode=original['episode'],case=label,accepted=accepted))
prep=json.loads((W/'FRONT_INITIAL_STAGE_AUDITS_PREPARATION.json').read_text());entry=next(x for x in prep['adapters'] if Path(x['path'])==source);s=Path(entry['parent']).read_text()
for a,b in prep['global_replacements']:s=s.replace(a,b)
for e in entry['edits']:assert s.count(e['old'])==1;s=s.replace(e['old'],e['new'])
assert s==source.read_text() and sha(source)==entry['sha256'];out=W/'FRONT_INITIAL_CLEARANCE_DISPATCH_CHECK.json';assert not out.exists();out.write_text(json.dumps(dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,original_full_geometry_math_unchanged=True,source_sha256={str(p):sha(p) for p in [Path(__file__),source,snapshot,W/'FRONT_INITIAL_STAGE_AUDITS_PREPARATION.json']},simulation_started=False,training_ready=False),indent=2));print('Exact branch',len(rows),'checks passed; original geometry source unchanged')
