"""Execute actual coordinator override AST and actual adapter on lifecycle fixtures.
Recorded starting states feed synthetic plants; this is not physical collection.
Independent handover checks live in LIFECYCLE_CHECK. Full collector context and
independent physical episode audits are still separate required work.
"""
from pathlib import Path
import sys,ast,json,copy,types,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_pose';sys.path[:0]=[str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_adapter import apply
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage)
tree=ast.parse((stage/'waist_coordination_clearance.py').read_text());branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='recontact_override is not None')
f=ast.FunctionDef(name='actual_branch',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[branch,ast.Return(value=ast.Constant(value=None))],decorator_list=[]);program=compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'<actual coordinator command override>','exec')
class Tensor:
 def __init__(self,x):self.x=np.asarray(x)
 def __getitem__(self,i):return Tensor(self.x[i])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x
source=w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json';data=json.loads(source.read_text());counts=dict(events=0,handovers=0,defaults=0);sample=None
for case in data['rows']:
 side='right' if 'push_box' in case['episode'] else 'left';inactive='left' if side=='right' else 'right'
 for plant in case['plants']:
  assert plant['summary']['completed']
  for original in plant['trace']:
   event=json.loads(json.dumps(original));assert event['kind'] in ('command','handover');ctx=event['context'];q=np.array(ctx['current']);q23=np.r_[np.zeros(12),q];default=np.zeros(23);action=np.zeros(23);palms={s:((T:=guard.model.fk(s,q)[0])[:3,3]+T[:3,:3]@np.array([.20,0,.007])).tolist() for s in ['left','right']}
   ns=dict(np=np,recontact_override=event,robot=types.SimpleNamespace(data=types.SimpleNamespace(joint_pos=types.SimpleNamespace(torch=Tensor([q23])))),joint_ids=list(range(12,23)),indices=list(range(12,23)),default=default,action=action,previous_command=np.array(ctx['previous_command']),bounded=True,clearance_geometry=guard.geometry,palms=palms,points=palms,active_point_offset=None,active_support_reference=None,anchor={inactive:palms[inactive]},state=types.SimpleNamespace(side=side))
   exec(program,ns);result=ns['actual_branch']();assert np.array_equal(action[12:23],np.array(event['command'],dtype=np.float32)) and np.array_equal(action[:12],np.zeros(12));assert result['controller_kind']=='verified_unloaded_recontact_joint_path' and result['contact_normal_tracking'] is None and result['task_inputs'] is None
   count_before=action.copy();ns['recontact_override']=None;assert ns['actual_branch']() is None and np.array_equal(action,count_before);counts['defaults']+=1
   # Actual adapter is separate from command emission. It changes expert state,
   # never arrays representing simulator state or object positions.
   expert=types.SimpleNamespace(load=types.SimpleNamespace(bias_m=-.006),sentinel='unchanged');region=types.SimpleNamespace(center_local=np.zeros(3),active=False);row=dict(mode=ctx['parent_mode'],target_xyz=[1.,2.,3.],contact_load=dict(observed_vertical_load_n=0.,filtered_vertical_load_n=ctx['filtered_load_n'],applied_z_bias_m=-.006,stored_z_bias_m=-.006),sentinel='preserved');ref=dict(sentinel='parent_reference');object_rotation=__import__('scipy').spatial.transform.Rotation.from_quat(ctx['scene']['target_quat']).as_matrix();row_before=copy.deepcopy(row)
   if event['kind']=='handover':expert.size=np.array(ctx['scene']['core_size'])
   updated,reference=apply(row,expert,region,ref,event,object_xyz=ctx['scene']['target_xyz'],object_rotation=object_rotation)
   assert row==row_before and updated['sentinel']=='preserved' and expert.sentinel=='unchanged';assert updated['contact_load']['stored_z_bias_m']==0
   if event['kind']=='handover':
    assert updated['mode']=='top_press' and expert.push_x_anchor is None and np.array_equal(region.center_local,event['captured_center_local']) and expert.last_waypoint_xy==tuple(event['observed_support_xyz'][:2]);counts['handovers']+=1
   else:assert updated['mode']=='top_cross' and expert.mode=='top_cross'
   counts['events']+=1
   if sample is None:sample=(ns,event)
negative=[]
for name in ['changed_command','loaded','filtered_load','guard_stop','wrong_mode','unverified_proposal','changed_current','changed_previous','proposal_command']:
 ns,event=sample;ns=ns.copy();event=json.loads(json.dumps(event));ns['recontact_override']=event;ns['action']=np.zeros(23)
 if name=='changed_command':event['command'][5]+=.01
 if name=='loaded':event['context']['observed_load_n']=.001
 if name=='filtered_load':event['context']['filtered_load_n']=.051
 if name=='guard_stop':event['context']['guard_stop']=True
 if name=='wrong_mode':event['context']['parent_mode']='top_push'
 if name=='unverified_proposal':event['proposal']['nominal_scene']['accepted']=False
 if name=='changed_current':event['context']['current'][1]+=.01
 if name=='changed_previous':event['context']['previous_command'][1]+=.01
 if name=='proposal_command':event['proposal']['candidate_command'][2]+=.01
 exec(program,ns);rejected=False
 try:ns['actual_branch']()
 except ValueError:rejected=True
 assert rejected and np.array_equal(ns['action'],np.zeros(23));negative.append(name)
assert counts['handovers']==16 and counts['events']==sum(p['summary']['iterations'] for c in data['rows'] for p in c['plants'])
report=dict(passed=True,scope=__doc__,counts=counts,rejected_corruptions=negative,fixture_sha256=sha(source),source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'waist_coordination_clearance.py',stage/'collect_paired_sorting.py',stage/'recontact_adapter.py',stage/'INTEGRATION_CHECK.json']},physical_validation=False,training_ready=False)
(stage/'COMMAND_ENTRY_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(counts),'negative',len(negative))
