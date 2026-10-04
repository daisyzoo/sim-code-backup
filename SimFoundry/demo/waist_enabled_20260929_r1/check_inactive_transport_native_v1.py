"""Execute actual collector loaded-Z -> transport -> original final guard nodes.
Uses recorded state/object inputs and real candidate solvers/certificates, with
an array-only tensor facade; no simulator and no counterfactual rollout.
"""
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import ast,copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_inactive_transport_v1';D=W/'inactive_transport_clearance_bilateral_draft_r1'
sys.path[:0]=[str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
from inactive_transport_runtime import InactiveTransportRuntime
from recontact_scene import RecontactScene
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=read(S/'COLLECTOR_PREPARATION.json');sources={str(S/n):h for n,h in prep['stage_sha256'].items()}
for p,h in sources.items():assert sha(p)==h,p
parent=Path(prep['parent']);restored=(S/'collect_paired_sorting.py').read_text()
for e in reversed(prep['edits']['collect_paired_sorting.py']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(parent/'collect_paired_sorting.py').read_text()
tree=ast.parse((S/'collect_paired_sorting.py').read_text())
loaded=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_z_priority' and any(isinstance(z,ast.Name) and z.id=='priority_command' for z in ast.walk(n))];assert len(loaded)==1;loaded=loaded[0]
hook=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.inactive_transport_clearance' and any(isinstance(z,ast.Name) and z.id=='transport_command' for z in ast.walk(n))];assert len(hook)==1;hook=hook[0]
final=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='clearance_guard is not None' and any(isinstance(z,ast.Name) and z.id=='final_clearance' for z in ast.walk(n))];assert len(final)==1;final=final[0]
loops=[n for n in ast.walk(tree) if isinstance(n,ast.For) and loaded in n.body];assert len(loops)==1;body=loops[0].body
assert body.index(loaded)+1==body.index(hook) and body.index(hook)+1==body.index(final)
assert ast.unparse(body[body.index(final)+1])=='previous = action.copy()'
code=compile(ast.fix_missing_locations(ast.Module(body=[ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.Tuple(elts=[ast.Constant(0)],ctx=ast.Load()),body=copy.deepcopy([loaded,hook,final,body[body.index(final)+1]])+[ast.Assign(targets=[ast.Name(id='completed',ctx=ast.Store())],value=ast.Constant(True))],orelse=[])],type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec')
class Tensor:
 def __init__(self,x):self.x=np.asarray(x)
 def __getitem__(self,key):return Tensor(self.x[key])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x.copy()
guard=ClearanceGuard(ROOT,S);expected=read(D/'EARLY_CAPTURE_RUNTIME_PROBE.json');rows=[];negative=[];cache={};tested_sides=set()
for rr in expected['records']:
 run,t,side=rr['run'],rr['step'],rr['side'];case=840020 if side=='right' else 840023;task=rr['task'];ep=W/run/f'case_{case}'/f'layout_{case}_{task}'
 if str(ep) not in cache:
  with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
  with np.load(ep/'trace.npz') as z:xyz={k:z[k].copy() for k in ['box','mailer']}
  with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].copy() for k in ['box','mailer']}
  cache[str(ep)]=(q,u,xyz,quat,{r['step']:r for r in read(ep/'frontal_bypass.json')['rows']},{r['step']:r for r in read(ep/'coordination.json')},{r['step']:r for r in read(ep/'front_loaded_z_priority.json')['rows']})
  for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','front_loaded_z_priority.json']:sources[str(ep/name)]=sha(ep/name)
 q,u,xyz,quat,fr,co,lz=cache[str(ep)];target='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]};decay=read(S/'causal_response_parameters.json')['tasks'][task]['decay']
 def namespace(enabled=True):
  actors={'parcel_box':'box','mailer':'mailer'};scene={a:NS(data=NS(root_quat_w=NS(torch=Tensor(quat[k][t][None,:])))) for a,k in actors.items()}
  action=u[t].copy();action[12:23]=lz[t]['context']['parent_command']
  return dict(np=np,ROOT=ROOT,STAGE=S,args=NS(front_loaded_z_priority=True,inactive_transport_clearance=enabled),clearance_guard=guard,default=np.zeros(23),front_loaded_z_priority_controller=None,front_loaded_z_priority_log=[],inactive_transport_controller=None,inactive_transport_log=[],front_recontact_runtime=None,front_initial_runtime=NS(center_local=[0,0,0]),frontal_log=[copy.deepcopy(fr[t])],coordination_log=[copy.deepcopy(co[t])],step=t,side=side,env=NS(scene=scene),parcel_xyz=lambda env,a:xyz[actors[a]][t].copy(),obstacle_size=sizes[other],frontal_plan=dict(region_causal_response=dict(actual_core=dict(collision_core_size_xyz=sizes[target]))),parameters=dict(tasks={task:dict(decay=decay)}),task_id=task,robot=NS(data=NS(joint_pos=NS(torch=Tensor(q[t][None,:])))),ordered_ids=np.arange(23),qs=[q[t-1].copy()],previous=u[t-1].copy(),action=action,clearance_rows=[],clearance_failure=None,completed=False)
 ns=namespace();exec(code,ns);assert ns['completed'] and ns['clearance_failure'] is None
 rec=ns['inactive_transport_log'][0];np.testing.assert_array_equal(ns['front_loaded_z_priority_log'][0]['output_command'],u[t,12:23]);np.testing.assert_array_equal(rec['parent_command'],u[t,12:23]);assert {k:v for k,v in rec.items() if k!='collector_context'}==rr['record']
 np.testing.assert_array_equal(ns['action'][12:23],rr['record']['output_command']);np.testing.assert_array_equal(ns['previous'],ns['action']);np.testing.assert_array_equal(ns['action'][:12],u[t,:12]);assert ns['clearance_rows'][0]['accepted']
 assert ns['coordination_log'][-1]['inactive_transport_clearance']==rec
 context=rec['collector_context'];np.testing.assert_array_equal(context['current'],q[t,12:23]);np.testing.assert_array_equal(context['previous_q'],q[t-1,12:23]);np.testing.assert_array_equal(context['previous_command'],u[t-1,12:23]);assert context['side']==side
 disabled=namespace(False);exec(code,disabled);assert disabled['completed'];np.testing.assert_array_equal(disabled['action'],u[t]);assert not disabled['inactive_transport_log']
 rows.append(dict(run=run,step=t,side=side,applied=rec['applied'],reason=rec['reason'],parent_chain_exact=True,disabled_exact=True,final_guard=True,previous_action_exact=True));print(json.dumps(rows[-1]),flush=True)
 if side not in tested_sides and rec['applied']:
  tested_sides.add(side)
  sc=RecontactScene(guard,side,xyz[target][t],quat[target][t],sizes[target],xyz[other][t],quat[other][t],sizes[other])
  kw=dict(step=t,selected=True,side=side,row=copy.deepcopy(fr[t]),coordinate=copy.deepcopy(co[t]),scene=sc,current=q[t,12:23].copy(),previous_q=q[t-1,12:23].copy(),previous_command=u[t-1,12:23].copy(),parent_command=u[t,12:23].copy(),decay=decay)
  for label in ['disabled','unselected','initial_zero','joint_path','initial_path','unloaded_path','terminal_hold','route_stop','guard_saturated','missing_task','missing_normal','wrong_mode','failed_constraint_certificate','failed_path_certificate','wrong_step','wrong_previous','wrong_current','wrong_scene_side']:
   a=copy.deepcopy({k:v for k,v in kw.items() if k!='scene'});a['scene']=sc;runtime=InactiveTransportRuntime(guard,ROOT,S,enabled=label!='disabled')
   if label=='unselected':a['selected']=False
   elif label=='initial_zero':a['step']=0
   elif label in ['joint_path','initial_path','unloaded_path']:a['coordinate'][{'joint_path':'front_recontact_center_override','initial_path':'front_initial_center_override','unloaded_path':'recontact_pose_override'}[label]]={'kind':'command'}
   elif label=='terminal_hold':a['coordinate']['terminal_joint_hold']={'held':True}
   elif label=='route_stop':a['row']['route_stop_reason']='test_stop'
   elif label=='guard_saturated':a['row']['hand_guard_saturated']=True
   elif label=='missing_task':a['coordinate']['task_inputs']=None
   elif label=='missing_normal':a['coordinate']['contact_normal_tracking']=None
   elif label=='wrong_mode':a['row']['mode']='wait'
   elif label=='wrong_step':a['coordinate']['step']+=1
   elif label=='wrong_previous':a['previous_command'][8]+=.001
   elif label=='wrong_current':a['current'][8]+=.001
   elif label=='wrong_scene_side':a['side']='left' if side=='right' else 'right'
   if label.startswith('wrong_') and label!='wrong_mode':
    try:runtime.refine(**a)
    except ValueError:negative.append(dict(side=side,case=label,rejected=True));continue
    raise AssertionError(label)
   if label=='failed_constraint_certificate':
    with patch('inactive_transport_runtime.verify',return_value=dict(passed=False)):out,r=runtime.refine(**a)
   elif label=='failed_path_certificate':
    with patch('inactive_transport_runtime.certify',return_value=dict(passed=False)):out,r=runtime.refine(**a)
   else:out,r=runtime.refine(**a)
   assert not r['applied'];np.testing.assert_array_equal(out,a['parent_command']);negative.append(dict(side=side,case=label,parent_retained=True,reason=r['reason']))
assert len(rows)==22 and len(negative)==36 and tested_sides=={'left','right'}
# A true zero-action unselected wait exercises the exact final first-frame gate.
ns=namespace();ns.update(step=0,front_initial_runtime=None,frontal_log=[],coordination_log=[],qs=[],previous=np.zeros(23,dtype=np.float32),action=np.zeros(23,dtype=np.float32),robot=NS(data=NS(joint_pos=NS(torch=Tensor(np.zeros((1,23)))))),clearance_rows=[],completed=False)
exec(code,ns);assert ns['completed'] and not ns['inactive_transport_log'][0]['applied'];np.testing.assert_array_equal(ns['action'],np.zeros(23));assert ns['inactive_transport_log'][0]['collector_context']['previous_q'] is None
for p in [Path(__file__),S/'COLLECTOR_PREPARATION.json',S/'PARSER_CHECK.json',D/'EARLY_CAPTURE_RUNTIME_PROBE.json']:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h,p
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=rows,negative_cases=negative,zero_wait_fixture_passed=True,actual_collector_ast_order_verified=True,parent_inverse_exact=True,source_sha256=sources,full_stream_audit_ready=False,physics_started=False,training_ready=False)
with (S/'NATIVE_HOOK_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,contexts=len(rows),negative=len(negative),unissued_proposals=sum(x['applied'] for x in rows),physics=False)))
