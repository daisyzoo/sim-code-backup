"""Execute actual collector loaded-Z -> joint hook -> final guard -> previous.
Real loaded-Z parent is recomputed. Joint outputs use hash-bound, independently
verified saved-context runtime results; every joint input is checked before the
cached output is returned. This checks wiring, not new dynamics or solver replay.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';D=W/'joint_transport_reserve_preparation_r1';sys.path[:0]=[str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={str(p):sha(p) for p in S.iterdir() if p.suffix in ['.py','.json']}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
tree=ast.parse((S/'collect_paired_sorting.py').read_text())
def find(test,name):
 nodes=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)==test and any(isinstance(z,ast.Name) and z.id==name for z in ast.walk(n))];assert len(nodes)==1;return nodes[0]
loaded=find('args.front_loaded_z_priority','priority_command');inactive=find('args.inactive_transport_clearance','transport_command');joint=find('args.joint_transport_clearance','transport_command');final=find('clearance_guard is not None','final_clearance');loops=[n for n in ast.walk(tree) if isinstance(n,ast.For) and loaded in n.body];assert len(loops)==1;body=loops[0].body;i=body.index(loaded);assert body[i:i+4]==[loaded,inactive,joint,final] and ast.unparse(body[i+4])=='previous = action.copy()'
code=compile(ast.fix_missing_locations(ast.Module(body=[ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.Tuple(elts=[ast.Constant(0)],ctx=ast.Load()),body=copy.deepcopy(body[i:i+5])+[ast.Assign(targets=[ast.Name(id='completed',ctx=ast.Store())],value=ast.Constant(True))],orelse=[])],type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec')
class Tensor:
 def __init__(self,x):self.x=np.asarray(x)
 def __getitem__(self,key):return Tensor(self.x[key])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x.copy()
class BoundCachedJoint:
 def __init__(self,result,context):self.result=result;self.context=context;self.calls=0
 def refine(self,**kw):
  p=self.result['proposal'];assert kw['selected'] is True and kw['step']==self.result['step'] and kw['side']==p['side']
  for key in ['current','previous_q','previous_command','parent_command','decay']:np.testing.assert_array_equal(kw[key],p[key])
  assert kw['scene'].record()==p['scene'];assert kw['coordinate']['task_inputs']==self.context['task_inputs'];assert kw['coordinate']['contact_normal_tracking']==self.context['contact_normal_tracking'];assert kw['coordinate']['front_loaded_z_priority']==self.context['front_loaded_z_priority'];self.calls+=1
  return np.array(self.result['output_command']),copy.deepcopy(self.result)
guard=ClearanceGuard(ROOT,S);rows=[]
for side,t,case,task in [('left',225,840023,'nudge_mailer_to_bin'),('right',808,840020,'push_box_to_bin')]:
 ep=W/('joint_transport_physical_r1' if side=='left' else 'inactive_transport_physical_r1')/f'case_{case}'/f'layout_{case}_{task}';record=read(D/f'CONTEXT_{side}_{t}.json');assert record['certificate']['passed'] and all(v['passed'] for v in record['paths'].values())
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
 with np.load(ep/'trace.npz') as z:xyz={k:z[k].copy() for k in ['box','mailer']}
 with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].copy() for k in ['box','mailer']}
 for name in ['raw.npz','trace.npz','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
 fr=read(ep/'frontal_bypass.json');row={r['step']:r for r in fr['rows']}[t];coordinate={r['step']:r for r in read(ep/'coordination.json')}[t];lz=read(ep/'front_loaded_z_priority.json')['rows'][t];other='mailer' if side=='right' else 'box';sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]};decay=read(S/'causal_response_parameters.json')['tasks'][task]['decay'];actors={'parcel_box':'box','mailer':'mailer'}
 def namespace(enabled=True):
  scene={a:NS(data=NS(root_quat_w=NS(torch=Tensor(quat[k][t][None,:])))) for a,k in actors.items()};action=u[t].copy();action[12:23]=lz['context']['parent_command'];cached=BoundCachedJoint(record,coordinate)
  return dict(np=np,ROOT=ROOT,STAGE=S,args=NS(front_loaded_z_priority=True,inactive_transport_clearance=False,joint_transport_clearance=enabled),clearance_guard=guard,default=np.zeros(23),front_loaded_z_priority_controller=None,front_loaded_z_priority_log=[],inactive_transport_controller=None,inactive_transport_log=[],joint_transport_controller=cached,joint_transport_log=[],front_recontact_runtime=None,front_initial_runtime=NS(center_local=[0,0,0]),frontal_log=[copy.deepcopy(row)],coordination_log=[copy.deepcopy(coordinate)],step=t,side=side,env=NS(scene=scene),parcel_xyz=lambda env,a:xyz[actors[a]][t].copy(),obstacle_size=sizes[other],frontal_plan=fr['plan'],edge_size=np.asarray(fr['plan']['front_initial_center_landing']['actual_core']['collision_core_size_xyz']),parameters=dict(tasks={task:dict(decay=decay)}),task_id=task,robot=NS(data=NS(joint_pos=NS(torch=Tensor(q[t][None,:])))),ordered_ids=np.arange(23),qs=[q[t-1].copy()],previous=u[t-1].copy(),action=action,clearance_rows=[],clearance_failure=None,completed=False)
 ns=namespace();
 if side=='left':
  from joint_transport_parent_coordinate_v1 import parent_coordinate
  ns['coordination_log'][-1]=parent_coordinate(ns['coordination_log'][-1],record['parent_command'],u[t,12:23])
 exec(code,ns);assert ns['completed'] and ns['clearance_failure'] is None and ns['joint_transport_controller'].calls==1
 r=ns['joint_transport_log'][0];np.testing.assert_array_equal(ns['front_loaded_z_priority_log'][0]['output_command'],record['parent_command']);np.testing.assert_array_equal(ns['action'][12:23],record['output_command']);np.testing.assert_array_equal(ns['action'][:12],u[t,:12]);np.testing.assert_array_equal(ns['previous'],ns['action']);assert ns['coordination_log'][-1]['joint_transport_clearance']==r
 assert ns['coordination_log'][-1]['waist_target_rad']==record['output_command'][0];assert abs(ns['coordination_log'][-1]['joint_transport_unexecuted_parent_waist_target_rad']-record['parent_command'][0])<=1e-7
 c=r['collector_context'];np.testing.assert_array_equal(c['current'],q[t,12:23]);np.testing.assert_array_equal(c['previous_q'],q[t-1,12:23]);np.testing.assert_array_equal(c['previous_command'],u[t-1,12:23]);assert c['scene']==record['proposal']['scene']
 disabled=namespace(False);
 if side=='left':disabled['coordination_log'][-1]=parent_coordinate(disabled['coordination_log'][-1],record['parent_command'],u[t,12:23])
 exec(code,disabled);assert disabled['completed'] and not disabled['joint_transport_log'] and disabled['joint_transport_controller'].calls==0;np.testing.assert_array_equal(disabled['action'][12:23],record['parent_command'])
 rows.append(dict(side=side,step=t,passed=True,parent_recomputed=True,joint_cached_context_bound=True,final_action_exact=True,previous_action_exact=True,yaw_log_exact=True,disabled_preserves_parent=True))
 print(json.dumps(rows[-1]),flush=True)
ns=namespace();ns.update(step=0,joint_transport_controller=None,front_initial_runtime=None,frontal_log=[],coordination_log=[],qs=[],previous=np.zeros(23,dtype=np.float32),action=np.zeros(23,dtype=np.float32),robot=NS(data=NS(joint_pos=NS(torch=Tensor(np.zeros((1,23)))))),clearance_rows=[],completed=False)
exec(code,ns);assert ns['completed'] and ns['clearance_rows'][0]['accepted'];np.testing.assert_array_equal(ns['action'],np.zeros(23));assert not ns['joint_transport_log'][0]['applied'] and ns['joint_transport_log'][0]['collector_context']['previous_q'] is None
sources[str(Path(__file__))]=sha(__file__)
sources[str(W/'joint_transport_parent_coordinate_v1.py')]=sha(W/'joint_transport_parent_coordinate_v1.py')
for p,h in sources.items():assert sha(p)==h,p
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,zero_wait_fixture_passed=True,source_sha256=sources,physical_commands_issued=False,training_ready=False)
with (D/'NATIVE_HOOK_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
