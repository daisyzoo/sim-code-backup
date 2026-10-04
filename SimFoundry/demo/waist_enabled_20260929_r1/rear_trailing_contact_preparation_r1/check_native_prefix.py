"""Native collector lifecycle selection on original history up to first changed action.
Do not consume historical future after the new action. Not simulated physics.
"""
from pathlib import Path
import sys,json,hashlib,datetime,ast,types,copy
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_rear_trailing_contact_v1';T=W/'rear_trailing_contact_candidate_r1';sys.path[:0]=[str(S),str(T),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from trailing_contact_audit import PlanAudit
from audit_box_center_preference_events import EventAudit as ParentEventAudit
from recontact_adapter import apply
class EventAudit(PlanAudit):verify=ParentEventAudit.verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[];out=D/'NATIVE_PREFIX_CHECK.json';assert not out.exists()
def read(p):sources[str(p)]=sha(p);return json.loads(Path(p).read_text())
prep=read(S/'COLLECTOR_PREPARATION.json');prior=read(T/'CHECK.json');parser=read(D/'PARSER_SOURCE_CHECK.json');assert prior['complete'] and parser['passed']
for report in [prep,prior,parser]:
 for p,h in report['source_sha256'].items():assert sha(p)==h,p
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n;sources[str(S/n)]=h
source=(S/'collect_paired_sorting.py').read_text();tree=ast.parse(source);collect=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='collect');init=next(n for n in collect.body if isinstance(n,ast.If) and ast.unparse(n.test)=='args.unloaded_recontact_pose');compiled=compile(ast.Module(body=[init],type_ignores=[]),str(S/'collect_paired_sorting.py'),'exec')
params=read(S/'causal_response_parameters.json');decay=params['tasks']['push_box_to_bin']['decay'];guard=ClearanceGuard(ROOT,S)
def lifecycle(enabled):
 args=types.SimpleNamespace(unloaded_recontact_pose=True,minimum_motion_recontact=True,rear_box_center_preference=True,rear_box_entry_lift=True,recontact_interior_preference=True,rear_box_trailing_preference=enabled)
 ns=dict(args=args,side='right');exec(compiled,ns);return ns['recontact_lifecycle']
def save(complete):
 for mod in list(sys.modules.values()):
  file=getattr(mod,'__file__',None)
  if file:
   p=Path(file).resolve()
   if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
 for p in [Path(__file__),ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=complete,rows=rows,source_sha256=sources,full_physical_stream_audit_pending=True,physical_execution=False,training_ready=False)
 tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2));tmp.replace(out)
for run,limit in [('front_box_recenter_physical_r2',240),('joint_transport_physical_r1',242)]:
 ep=W/run/'case_840023/layout_840023_push_box_to_bin';history=read(ep/'recontact_pose.json')['rows'];sources[str(ep/'raw.npz')]=sha(ep/'raw.npz')
 with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 original=lifecycle(False);candidate=lifecycle(True);count=0;changed=None
 for old in history:
  step=old['step'];assert step<=limit,'Historical future must never be consumed after changed action';ctx=old['context'];scene=RecontactScene(guard,**ctx['scene']);inputs=dict(ctx,scene=scene,decay=decay)
  np.testing.assert_array_equal(q[step],ctx['current']);np.testing.assert_array_equal(q[step-1],ctx['previous_q']);np.testing.assert_array_equal(u[step-1],ctx['previous_command'])
  baseline=original.update(**inputs);event=candidate.update(**inputs)
  assert all(old[k]==v for k,v in baseline.items()),('disabled native differs',run,step)
  if step<limit:
   assert event==baseline,('unintended earlier change',run,step);count+=1;continue
  assert event['kind']=='command' and event['planning']['rear_box_trailing_preference']['enabled'] if 'enabled' in event['planning']['rear_box_trailing_preference'] else event['kind']=='command'
  ref=next(r for r in prior['rows'] if r['run']==run and r['step']==step)
  assert {k:v for k,v in event.items() if k!='recovery_total_ticks'}==ref['event']
  assert not np.array_equal(event['command'],u[step]) and event['recovery_total_ticks']<=240
  audit=EventAudit(ROOT,S,enabled=True);kw={k:inputs[k] for k in ['step','current','previous_q','previous_command','decay','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']};checked=audit.verify(event,**kw,final_command=event['command'],scene=scene.record())
  # Execute original bookkeeping adapter; first changed command must retain tracking without premature capture.
  state=types.SimpleNamespace(command=[1],settled=2,load=types.SimpleNamespace(bias_m=.003),lost_contact_steps=4,top_mode='top_descend',mode='top_descend',mode_step=7,descent_z=.88)
  region=types.SimpleNamespace(center_local=np.array([1.,2.,3.]),active=False);reference=dict(reference_local=np.array([.1,0.,0.]));row=dict(mode=ctx['parent_mode'],contact_load=dict(filtered_vertical_load_n=ctx['filtered_load_n'],applied_z_bias_m=.003,stored_z_bias_m=.003))
  applied,returned=apply(row,state,region,reference,event,object_xyz=scene.target,object_rotation=scene.rotation)
  assert applied['mode']=='top_cross' and returned is reference and state.command is None and state.load.bias_m==0 and state.settled==0 and state.lost_contact_steps==0
  np.testing.assert_array_equal(region.center_local,[1.,2.,3.])
  changed=dict(step=step,event=event,audit=checked,original_adapter_tracking_without_capture=True,original_command=u[step].tolist(),historical_future_consumed=False)
  break
 assert changed is not None
 rows.append(dict(run=run,unchanged_native_prefix_events=count,disabled_native_exact_through_step=limit,first_changed=changed));save(False);print(json.dumps(dict(run=run,prefix=count,first_changed_step=limit)),flush=True)
assert len(rows)==2;save(True);print('COMPLETE_NATIVE_PREFIX_TWO_FIRST_CHANGED_ACTIONS',flush=True)
