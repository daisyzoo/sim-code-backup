"""Execute actual collector final hook on all8 recorded streams; no physical rollout."""
from pathlib import Path
import ast,copy,json,sys,hashlib,types
import numpy as np
import torch
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_joint_edge_retry';parent=w/'staged_joint_edge_command';probe=w/'staged_joint_edge_retry_probe';sys.path[:0]=[str(stage),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=stage/'collect_paired_sorting.py';tree=ast.parse(source.read_text());old=ast.parse((parent/'collect_paired_sorting.py').read_text())
class RemoveRetry(ast.NodeTransformer):
 def visit_If(self,n):
  if 'args.rear_joint_edge_analytic_retry' in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[0],ast.Constant) and n.value.args[0].value=='--rear-joint-edge-analytic-retry':return None
  return self.generic_visit(n)
 def visit_Call(self,n):
  if isinstance(n.func,ast.Name) and n.func.id=='refine_record':n.keywords=[x for x in n.keywords if x.arg!='analytic_retry']
  return self.generic_visit(n)
assert ast.dump(RemoveRetry().visit(copy.deepcopy(tree)),include_attributes=False)==ast.dump(old,include_attributes=False)
m=json.loads((parent/'MANIFEST.json').read_text());unchanged=[n for n in m['source_sha256'] if n not in ['collect_paired_sorting.py','joint_edge_command.py','joint_edge_adapter.py']];assert len(unchanged)==13
for n in unchanged:assert sha(stage/n)==m['source_sha256'][n]
for n in ['joint_edge_command.py','joint_edge_adapter.py']:assert sha(stage/n)==sha(probe/n)
expected=json.loads((probe/'ALL_RECORDS_CHECK.json').read_text());assert expected['passed']
for n,h in expected['probe_source_sha256'].items():assert sha(stage/n)==h
hook=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test).startswith('args.rear_joint_edge_command and step > 0'))
loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and hook in n.body);ix=loop.body.index(hook);assert ast.unparse(loop.body[ix-1])=='action = action.astype(np.float32)' and ast.unparse(loop.body[ix+1])=='previous = action.copy()'
code=compile(ast.Module(body=[hook],type_ignores=[]),str(source),'exec');model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');reports=[]
for exp in expected['episodes']:
 ep=w/'joint_edge_groups_r1'/('case_'+exp['episode'].split('_')[1])/exp['episode']
 for n,h in exp['source_sha256'].items():assert sha(ep/n)==h
 fr=json.loads((ep/'frontal_bypass.json').read_text());cs={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};selected=bool(fr['plan'].get('rear_joint_edge_command',{}).get('enabled'));side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if key=='box' else 'mailer'
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].copy()
 rows={r['step']:r for r in exp['rows']};counts=dict(default_identical=0,retry_checked=0,retry_changed=0,front_excluded=0,zero_excluded=0)
 for f in fr['rows']:
  t=f['step'];c=cs[t];parent_cmd=u[t].copy()
  if selected:parent_cmd[12:23]=c['joint_edge_refinement']['parent_final_upper_command']
  base=dict(np=np,step=t,frontal_plan=fr['plan'],frontal_log=[copy.deepcopy(f)],default=np.zeros(23,dtype=np.float32),previous=u[t-1].copy(),robot=types.SimpleNamespace(data=types.SimpleNamespace(joint_pos=types.SimpleNamespace(torch=torch.as_tensor(q[t][None])))),ordered_ids=list(range(23)),env=None,target_actor=actor,target_quat=quat[t].tolist(),parcel_xyz=lambda env,actor,x=xyz[t]:x,region_model=model,side=side)
  for retry in [False,True]:
   log=copy.deepcopy(c);log.pop('joint_edge_refinement',None)
   env=dict(base,args=types.SimpleNamespace(rear_joint_edge_command=True,rear_joint_edge_analytic_retry=retry),action=parent_cmd.copy(),coordination_log=[log]);exec(code,env)
   assert np.array_equal(env['action'][:12],u[t,:12])
   if not retry:
    assert np.array_equal(env['action'],u[t]) and env['coordination_log'][0]==c;counts['default_identical']+=1
   else:
    target=u[t].copy()
    if t in rows:target[12:23]=next(v['command'] for v in rows[t]['variants'] if v['name']=='retry')
    assert np.array_equal(env['action'],target),(ep.name,t)
    counts['retry_checked']+=1;counts['retry_changed']+=int(not np.array_equal(target,u[t]))
    if not selected:assert env['coordination_log'][0]==c;counts['front_excluded']+=1
    else:
     trace=env['coordination_log'][0].pop('joint_edge_refinement');assert env['coordination_log'][0]=={k:v for k,v in c.items() if k!='joint_edge_refinement'};assert np.array_equal(trace['parent_final_upper_command'],parent_cmd[12:23]);assert np.array_equal(trace['previous_upper_command'],u[t-1,12:23]);assert np.array_equal(trace['final_upper_command'],target[12:23])
 for retry in [False,True]:
  env=dict(args=types.SimpleNamespace(rear_joint_edge_command=True,rear_joint_edge_analytic_retry=retry),step=0,frontal_plan={'rear_joint_edge_command':{'enabled':True}},action=np.zeros(23,dtype=np.float32));exec(code,env);assert not np.any(env['action']);counts['zero_excluded']+=1
 reports.append(dict(episode=ep.name,counts=counts));print(ep.name,counts,flush=True)
out=dict(passed=True,default_ast_identical_except_explicit_additions=True,hook_after_original_limits_before_previous=True,unchanged_parent_helpers=unchanged,episodes=reports,source_sha256={n:sha(stage/n) for n in m['source_sha256']},checker_sha256=sha(Path(__file__)),reference_check_sha256=sha(probe/'ALL_RECORDS_CHECK.json'),scope=__doc__,training_ready=False)
(stage/'FINAL_HOOK_CHECK.json').write_text(json.dumps(out,indent=2))
