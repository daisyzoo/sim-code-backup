"""Default-off AST parity, actual CLI/source branches and18 recorded routing.
Recorded planning fixtures test routing without claiming fresh solver calls.
Two additional uncached planner calls cover actual preferred/fallback branches.
This is simulator-free and does not validate actual measured handover or physics.
"""
from pathlib import Path
import ast,copy,sys,json,hashlib,types
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_interior';parent=w/'staged_recontact_pose';sys.path[:0]=[str(stage),str(w),str(repo)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Strip(ast.NodeTransformer):
 def visit_If(self,n):
  if any(isinstance(x,ast.Attribute) and x.attr=='recontact_interior_preference' or isinstance(x,ast.Name) and x.id=='prefer_interior' for x in ast.walk(n.test)):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and n.value.args:
   arg=n.value.args[0]
   if isinstance(arg,ast.Constant) and arg.value=='--recontact-interior-preference':return None
   if ast.unparse(arg)=="STAGE / 'recontact_plan_original.py'":return None
  return self.generic_visit(n)
 def visit_Assign(self,n):
  if any(isinstance(x,ast.Attribute) and x.attr=='prefer_interior' for t in n.targets for x in ast.walk(t)):return None
  return self.generic_visit(n)
 def visit_Call(self,n):
  n.keywords=[x for x in n.keywords if x.arg!='prefer_interior'];return self.generic_visit(n)
 def visit_arguments(self,n):
  for i in reversed(range(len(n.kwonlyargs))):
   if n.kwonlyargs[i].arg=='prefer_interior':assert isinstance(n.kw_defaults[i],ast.Constant) and n.kw_defaults[i].value is False;n.kwonlyargs.pop(i);n.kw_defaults.pop(i)
  return self.generic_visit(n)
for name in ['collect_paired_sorting.py','recontact_lifecycle.py']:
 before=ast.parse((parent/name).read_text());after=ast.parse((stage/name).read_text());assert ast.dump(before,include_attributes=False)==ast.dump(Strip().visit(copy.deepcopy(after)),include_attributes=False),name
assert sha(parent/'recontact_plan.py')==sha(stage/'recontact_plan_original.py')
for p in parent.glob('*.py'):
 if p.name not in ['collect_paired_sorting.py','recontact_lifecycle.py','recontact_plan.py']:assert sha(p)==sha(stage/p.name),p.name
assert (stage/'recontact_plan_deeper.py').read_text()==(w/'staged_recontact_deeper_probe/recontact_plan_deeper.py').read_text()
tree=ast.parse((stage/'collect_paired_sorting.py').read_text());branch=next(n for n in tree.body if isinstance(n,ast.If) and ast.unparse(n.test)=='args.recontact_interior_preference and (not args.unloaded_recontact_pose)')
class Parser:
 def error(self,message):raise ValueError(message)
for enabled,unloaded in [(False,False),(False,True),(True,False),(True,True)]:
 rejected=False
 try:exec(compile(ast.Module(body=[branch],type_ignores=[]),'actual CLI guard','exec'),dict(args=types.SimpleNamespace(recontact_interior_preference=enabled,unloaded_recontact_pose=unloaded),parser=Parser()))
 except ValueError:rejected=True
 assert rejected==(enabled and not unloaded)
source_branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.unloaded_recontact_pose' and any(isinstance(x,ast.Constant) and x.value=='recontact_plan_original.py' for x in ast.walk(n)))
for enabled in [False,True]:
 ns=dict(args=types.SimpleNamespace(unloaded_recontact_pose=True,recontact_interior_preference=enabled),paths=[],STAGE=stage);exec(compile(ast.Module(body=[source_branch],type_ignores=[]),'actual archive branch','exec'),ns);assert stage/'recontact_plan_original.py' in ns['paths'];assert (stage/'recontact_plan_deeper.py' in ns['paths'])==enabled
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
import recontact_plan as wrapper
import recontact_plan_deeper as deeper
probe=w/'staged_recontact_deeper_probe/DEEPER_ENDPOINT_SCREEN.json';screen=json.loads(probe.read_text());assert len(screen['records'])==18
for path,h in screen['source_sha256'].items():assert sha(path)==h,path
guard=ClearanceGuard(repo,stage);original=wrapper.original_plan;deepfn=deeper.plan;rows=[];uncached=[]
try:
 for row in screen['records']:
  old,deep=[x['plan'] for x in row['variants']];scene=RecontactScene(guard,**old['scene']);q=np.array(old['start']);step=row['step']
  wrapper.original_plan=lambda *a,_old=old,**kw:_old
  deeper.plan=lambda *a,_deep=deep,**kw:_deep
  assert wrapper.plan(scene,q,step=step) is old
  new=wrapper.plan(scene,q,step=step,prefer_interior=True);info=new['interior_preference'];use_deep=bool(deep['accepted'] and row['variants'][1]['all_interpolated_waypoints_passed']);assert info['selected']==('preferred' if use_deep else 'original_fallback');expected=deep if use_deep else old
  assert new['accepted']==expected['accepted'];assert np.array_equal(new['endpoint'],expected['endpoint'])
  rows.append(dict(episode=row['episode'],step=step,selected=info['selected'],default_off_identity=True))
finally:wrapper.original_plan=original;deeper.plan=deepfn
for value in [1,None,'yes']:
 try:wrapper.plan(None,None,step=1,prefer_interior=value)
 except ValueError:pass
 else:raise AssertionError('Nonboolean enabled accepted')
for name in ['layout_840001_push_box_to_bin','layout_840004_nudge_mailer_to_bin']:
 row=next(r for r in screen['records'] if r['episode']==name);old=row['variants'][0]['plan'];scene=RecontactScene(guard,**old['scene']);q=np.array(old['start']);step=row['step'];new=wrapper.plan(scene,q,step=step,earlier_seed=(step,q),prefer_interior=True);expected=next(r for r in rows if r['episode']==name and r['step']==step)['selected'];assert new['interior_preference']['selected']==expected
 source_plan=row['variants'][1 if expected=='preferred' else 0]['plan'];assert np.max(abs(np.array(new['endpoint'])-source_plan['endpoint']))<1e-7
 uncached.append(dict(episode=name,step=step,selected=expected,accepted=new['accepted'],endpoint_exact_within1e7=True));print('uncached',uncached[-1],flush=True)
out=dict(passed=True,scope=__doc__,default_off_ast_exact=True,unchanged_original_math_files=True,cli_cases=4,source_archival_verified=True,recorded_routing=rows,uncached_planner_calls=uncached,collector_connected=True,physical_validation=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),probe,*stage.glob('*.py')]});(stage/'CONTRACT_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS18recorded2uncached',flush=True)
