"""Actual staged parser and independent front-recovery command branch checks.
Execute extracted, unmodified coordinator branch on source-bound synthetic
recovery events; check both precise_task_ik settings and original final guard.
No physics, model training, or full trajectory admissibility claim.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,json,datetime,hashlib,sys,copy,contextlib,io,inspect
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center';A=W/'staged_front_drive_1mm';D=W/'front_bag_recontact_center_draft_r4';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from clearance_runtime import ClearanceGuard
from front_recontact_center_runtime import FrontRecontactCenterRuntime
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());sources={str(S/'COLLECTOR_PREPARATION.json'):sha(S/'COLLECTOR_PREPARATION.json')}
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h;sources[str(S/n)]=h
src=(S/'collect_paired_sorting.py').read_text();back=src
for e in reversed(prep['collector_edits']):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(A/'collect_paired_sorting.py').read_text();coord=(S/'waist_coordination_clearance.py').read_text();e=prep['coordination_edits'];assert coord.replace(e['added_branch'],'',1).replace(e['signature_new'],e['signature_old'],1)==(A/'waist_coordination_clearance.py').read_text()
for module in ['front_recontact_center_runtime','front_recontact_center_lifecycle','front_recontact_center_lifecycle_static','front_recontact_center_selection','front_recontact_center_adapter','front_recontact_center_tracking']:assert Path(inspect.getfile(sys.modules[module])).parent==S
parent_path=W/'front_corridor_midpoint_physical_r1/PROTOCOL.json';plan=json.loads(parent_path.read_text())['plan'];parser_rows=[]
for item in plan['commands']:
 args=item['args'];old,_=parser_namespace(A/'collect_paired_sorting.py',args,full=True);off,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);assert off.pop('front_recontact_center_landing') is False and off==old
 on,_=parser_namespace(S/'collect_paired_sorting.py',args+['--front-recontact-center-landing'],full=True);assert on.pop('front_recontact_center_landing') is True and on==old;parser_rows.append(dict(layout=item['layout_id'],off_exact=True,on_only_new_flag=True))
negative_parser=[];base=list(plan['commands'][0]['args'])+['--front-recontact-center-landing']
for name in ['--front-initial-center-landing','--front-loaded-z-priority','--front-corridor-midpoint-replan','--self-clearance-task-ik','--expert-top-projected-support','--peak-load-bias-guard']:
 args=[x for x in base if x!=name]
 try:
  with contextlib.redirect_stderr(io.StringIO()):parser_namespace(S/'collect_paired_sorting.py',args,full=True)
 except (ValueError,SystemExit):negative_parser.append(name)
 else:raise AssertionError('missing prerequisite accepted '+name)
args=list(base);args[args.index('--front-cop-drive-step-m')+1]='.001'
try:
 with contextlib.redirect_stderr(io.StringIO()):parser_namespace(S/'collect_paired_sorting.py',args,full=True)
except (ValueError,SystemExit):negative_parser.append('wrong_front_increment')
else:raise AssertionError('1mm mixed with2mm candidate')
tree=ast.parse(coord);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step');branch=next(n for n in fn.body if isinstance(n,ast.If) and ast.unparse(n.test)=='front_recontact_override is not None');conflict=next(n for n in fn.body if isinstance(n,ast.If) and ast.unparse(n.test).startswith('sum('));function=ast.FunctionDef(name='run_actual_branch',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[conflict,branch,ast.Return(value=ast.Constant(None))],decorator_list=[]);code=compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(S/'waist_coordination_clearance.py'),'exec')
class Tensor:
 def __init__(self,v):self.v=np.asarray(v)
 def __getitem__(self,i):return Tensor(self.v[i])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.v
fixture=json.loads((D/'LIFECYCLE_CHECK.json').read_text());guard=ClearanceGuard(ROOT,S);records=[];sample=None
for r in fixture['records']:
 for original in [r['events'][0],r['events'][-1]]:
  event=copy.deepcopy(original);event['real_recontact_index']=r['recontacts'];q=np.asarray(event['context']['current']);prev=np.asarray(event['context']['previous_command']);robot=SimpleNamespace(data=SimpleNamespace(joint_pos=SimpleNamespace(torch=Tensor([np.r_[np.zeros(12),q]]))))
  for precise in [False,True]:
   action=np.zeros(23);ns=dict(np=np,front_recontact_override=event,front_initial_override=None,recontact_override=None,indices=list(range(12,23)),robot=robot,joint_ids=list(range(12,23)),bounded=True,clearance_geometry=guard.geometry,default=np.zeros(23),previous_command=prev,state=SimpleNamespace(side='left'),action=action,palms={},points={},active_point_offset=None,anchor={'right':[.2,-.3,.89]},active_support_reference=None,precise_task_ik=precise)
   exec(code,ns);out=ns['run_actual_branch']();assert out['controller_kind']=='verified_unloaded_front_recontact_joint_path' and out['front_recontact_center_override'] is event;np.testing.assert_array_equal(action[12:23],np.asarray(event['command'],np.float32));assert np.all(action[:12]==0)
   # Exact original slew/global bounds/waist range and guard for this already
   # admitted unloaded command; later loaded refinements require integration.
   from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
   action=np.clip(action,np.r_[np.zeros(12),prev]-.055,np.r_[np.zeros(12),prev]+.055);action=np.clip(action,U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI);action[12]=np.clip(action[12],-1.,1.);action=action.astype(np.float32);np.testing.assert_array_equal(action[12:23],np.asarray(event['command'],np.float32));assert guard.command(action[12:23],q,prev)['accepted']
   records.append(dict(run=r['run'],recontacts=r['recontacts'],event_kind=event['kind'],precise_task_ik=precise,exact_command_and_final_guard=True))
   if sample is None:sample=ns
negative=[]
for label in ['conflict','zero_counter','wrong_counter_binding','wrong_side','loaded','previous_mismatch','command_mismatch','geometry_rejected']:
 ns={k:v for k,v in sample.items() if k!='run_actual_branch'};ns['action']=np.zeros(23);ns['front_recontact_override']=copy.deepcopy(sample['front_recontact_override']);event=ns['front_recontact_override'];ns['previous_command']=np.asarray(ns['previous_command']).copy();ns['state']=SimpleNamespace(side='left')
 if label=='conflict':ns['front_initial_override']=event
 if label=='zero_counter':event['context']['recontacts']=0
 if label=='wrong_counter_binding':event['real_recontact_index']+=1
 if label=='wrong_side':ns['state'].side='right'
 if label=='loaded':event['context']['observed_load_n']=.1
 if label=='previous_mismatch':ns['previous_command'][0]+=.001
 if label=='command_mismatch':event['command'][0]+=.001
 if label=='geometry_rejected':event['proposal']['predicted_scene']['accepted']=False
 exec(code,ns)
 try:ns['run_actual_branch']()
 except ValueError:negative.append(label)
 else:raise AssertionError('bad override accepted '+label)
 assert np.all(ns['action']==0)
# Extract actual priority expression to verify recovery capture wins and remains
# available to loaded-height refinement even if first-capture fallback occurred.
ct=ast.parse(src);refcall=next(n for n in ast.walk(ct) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='projected_support_reference');center=next(k.value for k in refcall.keywords if k.arg=='center_local');expr=compile(ast.Expression(center),str(S/'collect_paired_sorting.py'),'eval');v=np.array([1.,2.,3.]);oldv=np.array([4.,5.,6.]);assert eval(expr,dict(front_recontact_runtime=SimpleNamespace(center_local=v),front_initial_runtime=SimpleNamespace(center_local=oldv),region_approach=None,contact_center_calibration=None)) is v
for p in [Path(__file__),parent_path,D/'LIFECYCLE_CHECK.json']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parser_configurations=parser_rows,negative_parser_checks=negative_parser,dispatch_fixtures=records,negative_dispatch_checks=negative,actual_reference_selection_expression_checked=True,parent_inverse_restore=True,stage_module_import_paths_verified=True,source_sha256=sources,full_collector_hook_checked=False,full_audit_family_ready=False,simulation_started=False,training_ready=False)
with (S/'PARSER_DISPATCH_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,parser_conditions=len(parser_rows),negative_parser=len(negative_parser),dispatch_fixtures=len(records),negative_dispatch=len(negative))))
