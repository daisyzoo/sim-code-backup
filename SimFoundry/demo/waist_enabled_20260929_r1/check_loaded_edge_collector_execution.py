"""Execute actual new collector override + final guard AST on all58 proposals.
Inputs are original real states/packets, no physics, no executed candidate rollout.
Includes actual invalid-context and infeasible-command loop-break paths. Legacy
clipping/refinement is represented by its recorded final parent command.
"""
from pathlib import Path
import ast,sys,json,hashlib,types,copy,datetime
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_loaded_edge_coverage';sys.path[:0]=[str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);tree=ast.parse((stage/'collect_paired_sorting.py').read_text());loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and any(isinstance(x,ast.Assign) and ast.unparse(x).startswith('action = np.clip(default + action,') for x in n.body));block=next(n for n in loop.body if isinstance(n,ast.If) and 'args.loaded_edge_coverage' in ast.unparse(n.test));final=next(n for n in loop.body if isinstance(n,ast.If) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='final_clearance' for t in x.targets) for x in n.body));body=[block,final,ast.Assign(targets=[ast.Name(id='reached_after_final_guard',ctx=ast.Store())],value=ast.Constant(value=True))];program=compile(ast.fix_missing_locations(ast.Module(body=[ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(value=0)],ctx=ast.Load()),body=body,orelse=[])],type_ignores=[])),'<actual loaded edge final override>','exec')
class Tensor:
 def __init__(self,x):self.x=np.asarray(x)
 def __getitem__(self,i):return Tensor(self.x[i])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x
fixture=stage/'ADAPTER_ACTUAL_CHECK.json';data=json.loads(fixture.read_text());assert data['adapter_checks_passed'];counts=dict(enabled=0,disabled=0,invalid_context_stops=0,infeasible_stops=0);records=[]
for item in data['rows']:
 active=[r for r in item['records'] if r['override']]
 if not active:continue
 en=item['episode'];cid=840001 if 'push_box' in en else 840004;side='right' if cid==840001 else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';ep=w/'recontact_pose_groups_r1'/f'case_{cid}'/en;fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].copy()
 for rec in active:
  t=rec['step'];expected=np.array(rec['trace']['final_upper_command'],dtype=np.float32)
  def setup(enabled):
   return dict(np=np,args=types.SimpleNamespace(loaded_edge_coverage=enabled),step=t,frontal_plan=fr['plan'],default=np.zeros(23,dtype=np.float32),frontal_log=[copy.deepcopy(fs[t-1]),copy.deepcopy(fs[t])],coordination_log=[copy.deepcopy(cs[t])],action=u[t].copy(),previous=u[t-1].copy(),robot=types.SimpleNamespace(data=types.SimpleNamespace(joint_pos=types.SimpleNamespace(torch=Tensor([q[t]])))),ordered_ids=list(range(23)),solved_contact_forces=[copy.deepcopy(packets[t-1])],parcel_xyz=lambda *a:xyz[t],env=None,target_actor=actor,target_quat=quat[t].tolist(),region_model=guard.model,clearance_guard=guard,side=side,loaded_edge_coverage_rows=[],loaded_edge_coverage_failure=None,clearance_rows=[],clearance_failure=None,reached_after_final_guard=False)
  ns=setup(True);exec(program,ns);assert ns['reached_after_final_guard'] and ns['clearance_failure'] is None and len(ns['clearance_rows'])==1 and ns['clearance_rows'][0]['accepted'];assert np.array_equal(ns['action'][12:23],expected) and np.array_equal(ns['action'][:12],u[t,:12]), (en,t,float(np.max(abs(ns['action'][12:23]-expected))),ns['action'][12:23].tolist(),expected.tolist());assert len(ns['loaded_edge_coverage_rows'])==1 and ns['coordination_log'][-1]['loaded_edge_coverage']['override'];counts['enabled']+=1
  ns=setup(False);exec(program,ns);assert ns['reached_after_final_guard'] and ns['clearance_failure'] is None and np.array_equal(ns['action'],u[t]) and not ns['loaded_edge_coverage_rows'];counts['disabled']+=1
  if counts['invalid_context_stops']==0:
   ns=setup(True);ns['solved_contact_forces']=[];exec(program,ns);assert not ns['reached_after_final_guard'] and not ns['clearance_rows'] and ns['clearance_failure']['reason']=='invalid_loaded_edge_context' and ns['loaded_edge_coverage_failure'] is not None;counts['invalid_context_stops']+=1
   class Impossible:
    def constraints(self,x):return np.array([-1.,-1.])
    def jacobian(self,x):return np.zeros((2,11))
   ns=setup(True);ns['clearance_guard']=types.SimpleNamespace(geometry=Impossible(),command=guard.command);exec(program,ns);assert not ns['reached_after_final_guard'] and not ns['clearance_rows'] and ns['clearance_failure']['reason']=='no_verified_nominal_edge_command' and ns['loaded_edge_coverage_rows'][0]['final_upper_command'] is None;counts['infeasible_stops']+=1
  records.append({'episode':en,'step':t,'actual_entry_command_matches_adapter':True,'actual_final_guard_passed':True})
assert counts==dict(enabled=58,disabled=58,invalid_context_stops=1,infeasible_stops=1),counts
sources=[Path(__file__),fixture,stage/'collect_paired_sorting.py',stage/'loaded_edge_coverage_current_contact.py',stage/'loaded_edge_coverage_adapter.py',stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json'];out={'passed':True,'scope':__doc__,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':counts,'records':records,'source_sha256':{str(p):sha(p) for p in sources},'physical_validation':False,'training_ready':False};(stage/'COLLECTOR_EXECUTION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',counts,flush=True)
