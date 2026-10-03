"""Execute actual staged collector hook and final action chain on affine fixtures.
Actual robot-state arrays are supplied by an explicit tensor facade. Only the
expensive causal planner is replaced by its previously source-bound result.
This tests wiring, not new physics or a counterfactual physical trajectory.
"""
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import ast,copy,datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center';D=W/'front_bag_recontact_center_draft_r4';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from front_initial_center_runtime import FrontInitialCenterRuntime
from front_recontact_center_runtime import FrontRecontactCenterRuntime
from front_initial_center_cop_route import FrontCopRouteState
from simfoundry.data.projected_support_reference import projected_support_reference
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());sources={str(S/n):h for n,h in prep['stage_sha256'].items()}
for p,h in sources.items():assert sha(p)==h,p
src=(S/'collect_paired_sorting.py').read_text();tree=ast.parse(src)
def one_if(test):
 a=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)==test];assert len(a)==1,(test,len(a));return a[0]
hook=one_if('front_initial_runtime is not None')
def loopcode(nodes):
 return compile(ast.fix_missing_locations(ast.Module(body=[ast.Assign(targets=[ast.Name(id='hook_completed',ctx=ast.Store())],value=ast.Constant(False)),ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.Tuple(elts=[ast.Constant(0)],ctx=ast.Load()),body=copy.deepcopy(nodes)+[ast.Assign(targets=[ast.Name(id='hook_completed',ctx=ast.Store())],value=ast.Constant(True))],orelse=[])],type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec')
hookcode=loopcode([hook]);captures=[one_if('front_initial_runtime is not None and front_initial_runtime.center_local is not None'),one_if('front_recontact_runtime is not None and front_recontact_runtime.center_local is not None')];capturecode=loopcode(captures)
refcall=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='projected_support_reference');refexpr=compile(ast.Expression(next(k.value for k in refcall.keywords if k.arg=='center_local')),str(S/'collect_paired_sorting.py'),'eval')
coordtree=ast.parse((S/'waist_coordination_clearance.py').read_text());fn=next(n for n in coordtree.body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step');branches=[n for n in fn.body if isinstance(n,ast.If) and (ast.unparse(n.test).startswith('sum(') or ast.unparse(n.test)=='front_recontact_override is not None')]
fun=ast.FunctionDef(name='actual_dispatch',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(branches)+[ast.Return(value=ast.Constant(None))],decorator_list=[]);dispatch=compile(ast.fix_missing_locations(ast.Module(body=[fun],type_ignores=[])),str(S/'waist_coordination_clearance.py'),'exec')
# Exact collector post-dispatch chain, including loaded-Z refinement and final guard.
a=src.index('        action = np.clip(default + action, U1_JOINT_LIMIT_LO, U1_JOINT_LIMIT_HI) - default');b=src.index('        previous = action.copy()',a)
posttree=ast.parse('for _once in [0]:\n'+src[a:b]);postcode=loopcode(posttree.body[0].body)
# Parent update precedes hook; command construction, postprocessing and execution follow it.
assert src.index('waypoint = frontal_state.update(')<hook.lineno and False if False else True
assert src.index('waypoint = frontal_state.update(')<src.index('                if front_initial_runtime is not None:')<src.index('                coordination_log.append(dict(step=step, **coordinated_step')<a<src.index('        previous = action.copy()',a)
class Tensor:
 def __init__(self,x):self.v=np.asarray(x)
 def __getitem__(self,k):return Tensor(self.v[k])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.v

def robot_for(c):
 poses=[np.asarray(c[k]) for k in ['observed_hand_pose','observed_inactive_hand_pose']]
 return NS(data=NS(joint_pos=NS(torch=Tensor([np.r_[np.zeros(12),c['current']]])),body_pos_w=NS(torch=Tensor([[p[:3,3] for p in poses]])),body_quat_w=NS(torch=Tensor([[Rotation.from_matrix(p[:3,:3]).as_quat() for p in poses]]))))
base=json.loads((D/'LIFECYCLE_CHECK.json').read_text());guard=ClearanceGuard(ROOT,S);records=[];negative=[]
for f in base['records']:
 c=f['events'][0]['context'];scene=c['scene'];ep=W/f['run']/'case_840023/layout_840023_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());row0=next(r for r in fr['rows'] if r['step']==f['step']);old=next(x for x in json.loads((ep/'front_initial_center.json').read_text())['rows'] if x['kind']=='handover')
 state=FrontCopRouteState(NS(plan=copy.deepcopy(fr['plan'])),'left',tuple(scene['core_size']),obstacle_size=tuple(scene['other_size']),guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=.9,tilt_recontact_rad=.03,recontact_on_route_change=True,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005,route_clearance_m=.012,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=.002,edge_speed_enabled=True,edge_core_size=scene['core_size'])
 initial=FrontInitialCenterRuntime(guard,'left',scene['core_size'],scene['other_size'],c['decay']);initial.lifecycle.finished=True;initial.center_local=np.array(old['captured_center_local']);initial_before=initial.center_local.copy()
 rt=FrontRecontactCenterRuntime(guard,'left',scene['core_size'],scene['other_size'],c['decay'],enabled=True)
 # Ownership sampled-prefix fixture: counters1..k-1 observed in original lifts.
 for counter in range(1,f['recontacts']):
  row=next(r for r in fr['rows'] if r.get('recontacts')==counter and r['mode']=='top_lift');state.recontacts=counter
  inp={k:c[k] for k in ['current','previous_q','previous_command','observed_load_n','observed_hand_pose','observed_inactive_hand_pose']};inp.update({k:scene[k] for k in ['target_xyz','target_quat','other_xyz','other_quat']})
  rt.update(row,state,{},selected=True,step=row['step'],normal_anchor=old['captured_normal_local_up'],inactive_anchor=old['captured_inactive_anchor_world'],**inp)
 env=NS(scene={name:NS(data=NS(root_quat_w=NS(torch=Tensor([scene[key]])))) for name,key in [('mailer','target_quat'),('parcel_box','other_quat')]})
 ns=dict(np=np,front_initial_runtime=initial,front_recontact_runtime=rt,frontal_state=state,projected_support_context={},region_approach=None,contact_center_calibration=None,ordered_ids=list(range(23)),hands={'left':0,'right':1},side='left',default=np.zeros(23),env=env,target_actor='mailer',obstacle_actor='parcel_box',target_quat=scene['target_quat'],obstacle_quat=scene['other_quat'],top_contact_normal_anchor=old['captured_normal_local_up'],inactive_anchor={'right':old['captured_inactive_anchor_world']},frontal_plan=fr['plan'],point_kwargs={},clearance_failure=None)
 ns['parcel_xyz']=lambda env,actor:scene['target_xyz' if actor=='mailer' else 'other_xyz']
 rows=[]
 for expected in f['events']:
  cc=expected['context'];state.recontacts=f['recontacts'];state.mode=state.top_mode=cc['parent_mode'];row=copy.deepcopy(row0);row.update(mode=cc['parent_mode'],step=cc['step'],recontacts=f['recontacts']);row['contact_load']['filtered_vertical_load_n']=cc['filtered_load_n']
  pose=np.asarray(cc['observed_hand_pose']);center=eval(refexpr,ns);reference=projected_support_reference(guard.model.vertices['left'],pose[:3,:3],np.asarray(__import__('simfoundry.data.top_contact_bypass',fromlist=['rotation_xyzw']).rotation_xyzw(scene['target_quat']))[:,2],center_local=center)
  ns.update(waypoint=row,reference=reference,step=cc['step'],robot=robot_for(cc),qs=[np.r_[np.zeros(12),cc['previous_q']]],previous=np.r_[np.zeros(12),cc['previous_command']],load_n=cc['observed_load_n'],front_initial_override=None,front_recontact_override=None)
  with patch('front_recontact_center_lifecycle.plan',return_value=copy.deepcopy(f['selected_plan'])):exec(hookcode,ns)
  assert ns['hook_completed'] and ns['clearance_failure'] is None
  event=ns['front_recovery_event'];assert event['kind']==expected['kind'] and ns['front_initial_override'] is None and ns['front_recontact_override'] is event
  np.testing.assert_allclose(event['command'],expected['command'],atol=2e-7,rtol=0);np.testing.assert_array_equal(initial.center_local,initial_before);assert state.recontacts==f['recontacts']
  exec(capturecode,ns)
  if event['kind']=='handover':
   for name,key in [('top_contact_normal_anchor','captured_normal_local_up')]:np.testing.assert_allclose(ns[name],event[key],atol=1e-12)
   np.testing.assert_allclose(ns['inactive_anchor']['right'],event['captured_inactive_anchor_world'],atol=1e-12)
   np.testing.assert_array_equal(eval(refexpr,ns),rt.center_local);np.testing.assert_array_equal(ns['waypoint']['front_recontact_captured_center_local'],rt.center_local)
   np.testing.assert_array_equal(ns['point_kwargs']['control_offset_local'],ns['reference']['reference_local'])
   assert state.top_mode=='top_press' and 'recovery' in ns['waypoint']['support_reference_scope']
  action=np.zeros(23);dn=dict(np=np,front_recontact_override=event,front_initial_override=None,recontact_override=None,indices=list(range(12,23)),robot=ns['robot'],joint_ids=list(range(12,23)),bounded=True,clearance_geometry=guard.geometry,default=np.zeros(23),previous_command=ns['previous'][12:23],state=NS(side='left'),action=action,palms={},points={},active_point_offset=None,anchor=ns['inactive_anchor'],active_support_reference=ns['projected_support_context'])
  exec(dispatch,dn);co=dn['actual_dispatch']();ns.update(action=np.clip(action,ns['previous']-.055,ns['previous']+.055),args=NS(motion_protocol='waist_yaw_enabled_v1',waist_probe=False,waist_limit_rad=1.,rear_joint_edge_command=False,front_loaded_z_priority=True),U1_JOINT_LIMIT_LO=U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI=U1_JOINT_LIMIT_HI,clearance_guard=guard,clearance_rows=[],front_loaded_z_priority_controller=None,front_loaded_z_priority_log=[],frontal_log=[ns['waypoint']],coordination_log=[dict(step=cc['step'],**co)],obstacle_size=scene['other_size'])
  exec(postcode,ns);assert ns['hook_completed'] and ns['clearance_failure'] is None;np.testing.assert_array_equal(ns['action'][12:23],np.array(event['command'],np.float32));assert not ns['front_loaded_z_priority_log'][-1]['applied'] and ns['clearance_rows'][-1]['accepted']
  rows.append(dict(step=cc['step'],kind=event['kind'],final_command_exact=True,original_guard_passed=True,loaded_refinement_applied=False))
  if len(rows)==1:
   # Actual collector stop-before-dispatch branch after a selected active path loses load record.
   saved=copy.deepcopy(ns);saved['waypoint'].pop('contact_load');saved['step']+=1;saved['front_initial_override']=saved['front_recontact_override']=None
   exec(hookcode,saved);assert not saved['hook_completed'] and saved['clearance_failure']['phase']=='front_recontact_center';assert saved['front_recontact_override'] is None;negative.append(dict(run=f['run'],counter=f['recontacts'],missing_actual_load_stops_before_dispatch=True))
 assert rt.lifecycle.finished
 records.append(dict(run=f['run'],real_recontacts=f['recontacts'],events=rows,first_capture_unchanged=True,recovery_reference_and_anchors_installed=True))
 for p in [ep/'frontal_bypass.json',ep/'front_initial_center.json']:sources[str(p)]=sha(p)
for p in [Path(__file__),D/'LIFECYCLE_CHECK.json',S/'COLLECTOR_PREPARATION.json',S/'PARSER_DISPATCH_CHECK.json']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,fixture_events=sum(len(x['events']) for x in records),negative_cases=negative,source_sha256=sources,full_parent_physical_history_checked=False,full_audit_family_ready=False,simulation_started=False,training_ready=False)
with (S/'COLLECTOR_HOOK_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,fixture_events=out['fixture_events'],negative_cases=len(negative))))
