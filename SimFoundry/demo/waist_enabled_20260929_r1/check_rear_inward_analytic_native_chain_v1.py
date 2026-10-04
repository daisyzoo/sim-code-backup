"""Execute isolated collector native edge -> intersection -> priority -> transport -> final guard.
Recorded physical history stays fixed. No AppLauncher or action is executed in physics.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,datetime,hashlib,inspect,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_inward_analytic_v1';D=W/'rear_inward_analytic_native_chain_r1';D.mkdir(exist_ok=False)
sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
tree=ast.parse((S/'collect_paired_sorting.py').read_text())
def block(test,contains):return next(n for n in ast.walk(tree) if isinstance(n,ast.If) and test in ast.unparse(n.test) and contains in ast.unparse(n))
edge=block('args.rear_joint_edge_command','refined, refinement');priority=block('args.front_loaded_z_priority','priority_command');transport=block('args.joint_transport_clearance','transport_command');final=block('clearance_guard is not None','final_clearance')
prev=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and ast.unparse(n)=='previous = action.copy()' and n.lineno>final.lineno)
assert edge.lineno<priority.lineno<transport.lineno<final.lineno<prev.lineno
loop=ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(0)],ctx=ast.Load()),body=[edge,priority,transport,final,prev,ast.Assign(targets=[ast.Name(id='reached',ctx=ast.Store())],value=ast.Constant(True))],orelse=[])
program=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<native analytic command chain>','exec')
class Tensor:
 def __init__(self,x):self.x=np.asarray(x);self.torch=self
 def __getitem__(self,k):return Tensor(self.x[k])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x
class InvalidTransport:
 def refine(self,**kw):
  x=np.array(kw['parent_command']).copy();x[0]=10
  return x,dict(applied=True,selected=False,output_command=x.tolist(),synthetic_invalid=True)
guard=ClearanceGuard(ROOT,S);results=[];sources={};negatives=[]
for run,reference in [('front_effective_height_physical_r1','rear_box_analytic_first_chain_probe_r2'),('front_loaded_z_quarter_physical_r2','rear_box_analytic_first_parent_chain_probe_r2')]:
 ep=W/run/'case_840023/layout_840023_push_box_to_bin';fr=read(ep/'frontal_bypass.json');frs={r['step']:r for r in fr['rows']};co=read(ep/'coordination.json');prior=read(W/reference/'RESULT.json');expected={r['step']:r for r in prior['records']};records=[]
 for p,h in prior['source_sha256'].items():assert sha(p)==h,p
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
 with np.load(ep/'trace.npz') as z:xyz=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:quat=z['box'].copy()
 def environment(c,t,enabled,invalid=False):
  c=copy.deepcopy(c);old=c['joint_edge_refinement'];a=u[t].copy();a[12:23]=old['parent_final_upper_command']
  for k in ['joint_edge_refinement','joint_edge_clearance_intersection','front_loaded_z_priority','joint_transport_clearance']:c.pop(k,None)
  return dict(args=NS(rear_joint_edge_command=True,rear_box_inward_correction=True,rear_inward_analytic_first=enabled,rear_joint_edge_analytic_retry=True,rear_joint_edge_parent_seed_retry=True,edge_clearance_intersection=True,front_loaded_z_priority=True,front_loaded_z_quarter=True,joint_transport_clearance=True,joint_transport_effective_quarter_height=True),frontal_plan=copy.deepcopy(fr['plan']),frontal_log=[copy.deepcopy(frs[t])],coordination_log=[c],step=t,side='right',default=np.zeros(23,np.float32),robot=NS(data=NS(joint_pos=Tensor(q[t][None]))),ordered_ids=list(range(23)),previous=u[t-1].copy(),action=a,parcel_xyz=lambda unused,actor:xyz[t].copy(),env=None,target_actor='parcel_box',target_quat=quat[t].copy(),region_model=guard.model,clearance_guard=guard,front_loaded_z_priority_controller=None,joint_transport_controller=InvalidTransport() if invalid else None,front_initial_runtime=None,front_recontact_runtime=None,front_loaded_z_priority_log=[],joint_transport_log=[],qs=[q[t-1].copy()],clearance_rows=[],clearance_failure=None,reached=False,ROOT=ROOT,STAGE=S,np=np)
 for c in co:
  if 'joint_edge_refinement' not in c:continue
  t=c['step']
  assert c['front_loaded_z_priority']['selected'] is False and c['joint_transport_clearance']['selected'] is False
  for enabled in [False,True]:
   e=environment(c,t,enabled);exec(program,e)
   assert e['reached'] and e['clearance_failure'] is None and e['clearance_rows'][-1]['accepted'],(run,t,enabled)
   np.testing.assert_array_equal(e['previous'],e['action']);np.testing.assert_array_equal(e['action'][:12],u[t,:12])
   want=expected[t]['command'] if enabled else u[t,12:23]
   np.testing.assert_array_equal(e['action'][12:23],want)
   record=e['coordination_log'][-1]['joint_edge_refinement']
   if not enabled:assert record==c['joint_edge_refinement'],(run,t,'defaultoff record')
   else:
    assert record['override']==expected[t]['candidate_override'] and record['reason']==expected[t]['candidate_reason']
    if record['override']:assert record['emitted_stationarity']==expected[t]['emitted_stationarity']
   for log in ['front_loaded_z_priority_log','joint_transport_log']:
    assert e[log][-1]['selected'] is False and e[log][-1]['applied'] is False
   module=Path(inspect.getfile(e['refine_record'])).resolve();assert module==S/('joint_edge_inward_analytic_adapter_v1.py' if enabled else 'joint_edge_inward_adapter.py')
   records.append(dict(step=t,enabled=enabled,override=record['override'],final_guard_accepted=True,expected_action_exact=True,defaultoff_record_exact=not enabled))
  if t%100==0:print(json.dumps(dict(run=run,step=t,native_contexts=len(records))),flush=True)
  if t==225:
   e=environment(c,t,True,invalid=True);exec(program,e);assert not e['reached'] and e['clearance_failure']['reason']=='final_override_not_verified';np.testing.assert_array_equal(e['previous'],u[t-1]);negatives.append(dict(run=run,step=t,invalid_final_command_rejected=True,history_not_updated=True))
 results.append(dict(run=run,contexts=len(records),records=records))
 for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json']:sources[str(ep/name)]=sha(ep/name)
 sources[str(W/reference/'RESULT.json')]=sha(W/reference/'RESULT.json')
for p in S.iterdir():
 if p.is_file():sources[str(p)]=sha(p)
sources[str(Path(__file__))]=sha(__file__)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,episodes=results,negative_cases=negatives,native_statement_lines=[n.lineno for n in [edge,priority,transport,final,prev]],source_sha256=sources,physics_started=False,training_ready=False,limitations=['Actual history fixed, no candidate recursive rollout.','Covers two full rear-box streams; priority/transport unselected and verified passthrough here. Front/wait isolation and source/audit rejection consumers remain required.','Original 225 audit failure remains recorded in original physical run.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,native_contexts=sum(r['contexts'] for r in results),negative_cases=len(negatives))),flush=True)
