"""Execute actual final collector hook over four real streams; default AST identity."""
from pathlib import Path
import ast,copy,json,sys,hashlib,types
import numpy as np
import torch
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_joint_edge_command';sys.path[:0]=[str(stage),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=stage/'collect_paired_sorting.py';tree=ast.parse(source.read_text());parent=ast.parse((w/'staged_rear_joint_xy/collect_paired_sorting.py').read_text())
class RemoveAdditions(ast.NodeTransformer):
 def visit_If(self,node):
  if 'args.rear_joint_edge_command' in ast.unparse(node.test):return None
  return self.generic_visit(node)
 def visit_Expr(self,node):
  if isinstance(node.value,ast.Call) and node.value.args and isinstance(node.value.args[0],ast.Constant) and node.value.args[0].value=='--rear-joint-edge-command':return None
  return self.generic_visit(node)
 def visit_List(self,node):
  node.elts=[x for x in node.elts if not isinstance(x,ast.Constant) or x.value not in ['joint_edge_command.py','joint_edge_adapter.py']];return self.generic_visit(node)
assert ast.dump(RemoveAdditions().visit(copy.deepcopy(tree)),include_attributes=False)==ast.dump(parent,include_attributes=False)
hook=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test).startswith('args.rear_joint_edge_command and step > 0'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and any(x is hook for x in ast.walk(n)))
loop=next(n for n in ast.walk(fn) if isinstance(n,ast.For) and hook in n.body);ix=loop.body.index(hook)
assert ast.unparse(loop.body[ix-1])=='action = action.astype(np.float32)' and ast.unparse(loop.body[ix+1])=='previous = action.copy()'
code=compile(ast.Module(body=[hook],type_ignores=[]),str(source),'exec');r=w/'rear_joint_xy_groups_r1';probe=json.loads((w/'JOINT_EDGE_COMMAND_PROBE_CHECK.json').read_text());model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');counts=dict(default_identical=0,enabled_parent_preserved=0,enabled_changed=0,front_excluded=0,zero_excluded=0);reports=[]
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin'),(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
 ep=r/f'case_{cid}'/f'layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());coords={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};selected=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'));side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if key=='box' else 'mailer'
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
 with np.load(ep/'trace.npz') as z:obj=z[key].copy()
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].copy()
 expected={x['step']:x['result'] for x in next(x for x in probe['episodes'] if x['episode']==ep.name)['rows']};trace=[]
 for f in fr['rows']:
  t=f['step'];plan=copy.deepcopy(fr['plan'])
  if selected:plan['rear_joint_edge_command']={'enabled':True}
  base=dict(np=np,step=t,frontal_plan=plan,coordination_log=[copy.deepcopy(coords[t])],frontal_log=[copy.deepcopy(f)],default=np.zeros(23,dtype=np.float32),previous=u[t-1].copy(),robot=types.SimpleNamespace(data=types.SimpleNamespace(joint_pos=types.SimpleNamespace(torch=torch.as_tensor(q[t][None])))),ordered_ids=list(range(23)),env=None,target_actor=actor,target_quat=quat[t].tolist(),parcel_xyz=lambda env,actor,obj=obj,t=t:obj[t],region_model=model,side=side)
  off=dict(base,args=types.SimpleNamespace(rear_joint_edge_command=False),action=u[t].copy(),coordination_log=[copy.deepcopy(coords[t])]);exec(code,off);assert np.array_equal(off['action'],u[t]) and off['coordination_log'][0]==coords[t];counts['default_identical']+=1
  on=dict(base,args=types.SimpleNamespace(rear_joint_edge_command=True),action=u[t].copy(),coordination_log=[copy.deepcopy(coords[t])]);exec(code,on)
  assert np.array_equal(on['action'][:12],u[t,:12])
  if not selected:
   assert np.array_equal(on['action'],u[t]) and on['coordination_log'][0]==coords[t];counts['front_excluded']+=1;continue
  record=on['coordination_log'][0].pop('joint_edge_refinement');assert on['coordination_log'][0]==coords[t]
  assert np.array_equal(record['parent_final_upper_command'],u[t,12:23]) and np.array_equal(record['previous_upper_command'],u[t-1,12:23]) and np.array_equal(record['final_upper_command'],on['action'][12:23])
  if record['override']:
   assert expected[t]['override'];assert np.max(abs(on['action'][12:23]-expected[t]['command']))<1.2e-7,(ep.name,t,float(np.max(abs(on['action'][12:23]-expected[t]['command']))),record,expected[t]);counts['enabled_changed']+=1
  else:assert np.array_equal(on['action'],u[t]);counts['enabled_parent_preserved']+=1
  trace.append(dict(step=t,refinement=record))
 # Actual zero-step guard must bypass missing controller records even on selected route.
 zero=dict(args=types.SimpleNamespace(rear_joint_edge_command=True),step=0,frontal_plan={'rear_joint_edge_command':{'enabled':True}},action=np.zeros(23,dtype=np.float32));exec(code,zero);assert np.max(abs(zero['action']))==0;counts['zero_excluded']+=1
 reports.append(dict(episode=ep.name,selected=selected,trace=trace,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json','trace.npz','parcel_orientation.npz']}))
out=dict(passed=True,default_collector_ast_identical_except_explicit_additions=True,actual_final_hook_after_original_float32_bounds_before_previous_update=True,counts=counts,episodes=reports,collector_sha256=sha(source),adapter_sha256=sha(stage/'joint_edge_adapter.py'),helper_sha256=sha(stage/'joint_edge_command.py'),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Actual collector final hook AST on four complete real recorded streams. Parent raw actions used as original final commands; measured q and previous actual commands unchanged. Real helper outputs checked against independent probe; disabled/front/first zero identity and preserved parent controller records. No recursively changed state/action history or physical success proof.')
(stage/'FINAL_HOOK_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='episodes'},indent=2))
