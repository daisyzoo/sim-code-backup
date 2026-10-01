"""Actual pre-launch CLI and default-off source equivalence; no simulation.
Checks final override ordering and declared archival sources statically. Actual
new collector action execution/stop propagation still needs its separate test.
"""
from pathlib import Path
import sys,ast,json,hashlib,subprocess,datetime
w=Path(__file__).resolve().parent;stage=w/'staged_loaded_edge_coverage';parent=w/'staged_recontact_pose';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();tree=ast.parse((stage/'collect_paired_sorting.py').read_text());removed=[]
def mentions(node):return any(isinstance(x,ast.Attribute) and isinstance(x.value,ast.Name) and x.value.id=='args' and x.attr=='loaded_edge_coverage' for x in ast.walk(node))
class RemoveNew(ast.NodeTransformer):
 def visit_If(self,node):
  if mentions(node.test):removed.append('branch');return None
  return self.generic_visit(node)
 def visit_Expr(self,node):
  if isinstance(node.value,ast.Call) and node.value.args and isinstance(node.value.args[0],ast.Constant) and node.value.args[0].value=='--loaded-edge-coverage':removed.append('CLI');return None
  return self.generic_visit(node)
old=ast.parse((parent/'collect_paired_sorting.py').read_text());new=RemoveNew().visit(ast.parse((stage/'collect_paired_sorting.py').read_text()));assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False),'disabled source differs beyond declared flag'
base=json.loads((stage/'BASELINE.json').read_text());assert all(sha(parent/n)==h for n,h in base['parent_files_sha256'].items());assert all(sha(stage/n)==h for n,h in base['parent_files_sha256'].items() if n!='collect_paired_sorting.py')
p=json.loads((w/'recontact_pose_groups_r1/PROTOCOL.json').read_text());code="from pathlib import Path\nimport types,sys\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nm=types.ModuleType('__coverage_prelaunch__');sys.modules[m.__name__]=m;ns=m.__dict__;ns['__file__']=str(p)\nexec(compile(s,str(p),'exec'),ns)\na=ns['args'];assert a.horizon==10 and not hasattr(a,'push_assist') and not a.push_force_n and not a.wait_force_n\nprint('PRELAUNCH_OK',a.loaded_edge_coverage)\n"
records=[]
for item in p['commands']:
 for enabled in [False,True]:
  args=item['args']+(['--loaded-edge-coverage'] if enabled else [])+['--out-dir','/tmp/loaded_edge_prelaunch_no_output'];res=subprocess.run([sys.executable,'-c',code,*args],capture_output=True,text=True);assert res.returncode==0 and ('PRELAUNCH_OK '+str(enabled)) in res.stdout,(item['layout_id'],enabled,res.stdout[-1000:],res.stderr[-3000:]);records.append({'layout_id':item['layout_id'],'wait':item['wait'],'enabled':enabled,'passed':True});print(item['layout_id'],enabled,'CLI passed',flush=True)
baseargs=p['commands'][0]['args']+['--loaded-edge-coverage','--out-dir','/tmp/loaded_edge_prelaunch_no_output'];negative=[]
for label,flag in [('no_unloaded_baseline','--unloaded-recontact-pose'),('no_legacy_edge','--rear-joint-edge-command'),('no_analytic_retry','--rear-joint-edge-analytic-retry'),('no_contact_trace','--trace-solved-contact-forces'),('no_final_clearance','--self-clearance-task-ik')]:
 args=[x for x in baseargs if x!=flag];res=subprocess.run([sys.executable,'-c',code,*args],capture_output=True,text=True);assert res.returncode!=0 and 'error:' in res.stderr,(label,res.stderr[-1000:]);negative.append(label)
for label,args in [('policy',baseargs+['--policy-port','8123']),('push_force',baseargs+['--push-force-n','1']),('wait_force',baseargs+['--wait-force-n','1'])]:
 res=subprocess.run([sys.executable,'-c',code,*args],capture_output=True,text=True);assert res.returncode!=0 and 'error:' in res.stderr,(label,res.stderr[-1000:]);negative.append(label)
loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and any(isinstance(x,ast.Assign) and ast.unparse(x).startswith('action = np.clip(default + action,') for x in n.body));ix=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.If) and mentions(n.test));final=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.If) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='final_clearance' for t in x.targets) for x in n.body));previous=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n)=='previous = action.copy()');assert ix<final<previous
newblock=loop.body[ix];assert sum(isinstance(n,ast.Break) for n in ast.walk(newblock))==2
archive_branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and mentions(n.test) and any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and ast.unparse(x.func)=='paths.extend' for x in ast.walk(n)))
for name in ['loaded_edge_coverage_current_contact.py','loaded_edge_coverage_adapter.py']:
 assert (stage/name).exists() and any(isinstance(n,ast.Constant) and n.value==name for n in ast.walk(archive_branch))
assert any(isinstance(n,ast.BinOp) and ast.unparse(n)=='STAGE / name' for n in ast.walk(archive_branch))
sources=[Path(__file__),stage/'collect_paired_sorting.py',parent/'collect_paired_sorting.py',stage/'loaded_edge_coverage_current_contact.py',stage/'loaded_edge_coverage_adapter.py',w/'recontact_pose_groups_r1/PROTOCOL.json',w/'recontact_pose_groups_r1/RESULT.json']
report={'passed':True,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':__doc__,'default_off_ast_exact':True,'removed_branches_and_cli':removed,'positive_cli_checks':records,'negative_cli_checks':negative,'override_before_final_guard_before_actuation':True,'explicit_stop_branches':2,'source_sha256':{str(p):sha(p) for p in sources},'physical_validation':False,'training_ready':False};(stage/'COLLECTOR_CONTRACT_CHECK.json').write_text(json.dumps(report,indent=2));print('PASS',len(records),len(negative),'defaultoff AST exact',flush=True)
