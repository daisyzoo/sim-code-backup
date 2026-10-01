"""Execute actual collector extraction/transition AST over synthetic lifecycle traces.
The input episode states/poses originate from four real starts plus declared
plant models. No simulator rollout or training admission is claimed.
"""
from pathlib import Path
import sys,ast,json,types,hashlib,copy
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_pose';sys.path[:0]=[str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_lifecycle import RecontactLifecycle
from simfoundry.data.top_contact_bypass import rotation_xyzw
from simfoundry.data.projected_support_reference import projected_support_reference
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage)
a=ast.parse((stage/'collect_paired_sorting.py').read_text());block=next(n for n in ast.walk(a) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.unloaded_recontact_pose' and any(isinstance(x,ast.Name) and x.id=='recovery_scene' for x in ast.walk(n)))
loop=ast.For(target=ast.Name(id='_fixture_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(value=0)],ctx=ast.Load()),body=[block],orelse=[]);program=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<actual collector recovery block>','exec')
class Tensor:
 def __init__(self,x):self.x=np.asarray(x)
 def __getitem__(self,i):return Tensor(self.x[i])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x
source=w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json';data=json.loads(source.read_text());reports=[];stop_example=None
for case in data['rows']:
 name=case['episode'];cid=int(name.split('_')[1]);ep=w/'unloaded_wrist_prior_groups_r1'/f'case_{cid}'/name;side='right' if 'push_box' in name else 'left';inactive='left' if side=='right' else 'right';fr=json.loads((ep/'frontal_bypass.json').read_text());by_step={r['step']:r for r in fr['rows']};coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};t=case['step'];initial=coords[t];prior_steps=[r['step'] for r in fr['rows'] if r['mode']=='top_cross' and r['recontacts']>0];seedstep=min(prior_steps)
 with np.load(ep/'raw.npz') as z:seed=z['q'][seedstep,12:23].astype(float)
 for plant in case['plants']:
  state=RecontactLifecycle(enabled=True);state.earliest_seed=(seedstep,seed.copy());region=types.SimpleNamespace(center_local=np.array(initial['active_support_reference']['center_local']),active=False,abort_reason=None,causal_decay=np.array(fr['plan']['region_causal_response']['decay']));expert=types.SimpleNamespace(load=types.SimpleNamespace(bias_m=0.),size=np.array(fr['plan']['top_recontact']['contact_size_xyz']));anchors={inactive:list(initial['inactive_anchor'])};normal=initial['contact_normal_tracking']['target_local_up'];log=[];events=0;handovers=0
  for expected in plant['trace']:
   ctx=expected['context'];q=np.array(ctx['current']);poses={side:np.array(ctx['observed_hand_pose']),inactive:np.array(ctx['observed_inactive_hand_pose'])};bodypos=np.array([poses[s][:3,3] for s in ['left','right']],dtype=np.float32);bodyquat=np.array([Rotation.from_matrix(poses[s][:3,:3]).as_quat() for s in ['left','right']],dtype=np.float32);robot=types.SimpleNamespace(data=types.SimpleNamespace(body_pos_w=types.SimpleNamespace(torch=Tensor([bodypos])),body_quat_w=types.SimpleNamespace(torch=Tensor([bodyquat]))));scene=ctx['scene'];row=copy.deepcopy(by_step[t]);row['mode']=ctx['parent_mode'];row['recontacts']=ctx['recontacts'];row['contact_load']['filtered_vertical_load_n']=ctx['filtered_load_n'];row['contact_load']['observed_vertical_load_n']=ctx['observed_load_n'];ref=projected_support_reference(guard.model.vertices[side],poses[side][:3,:3],Rotation.from_quat(scene['target_quat']).as_matrix()[:,2],center_local=region.center_local)
   ns=dict(args=types.SimpleNamespace(unloaded_recontact_pose=True),np=np,rotation_xyzw=rotation_xyzw,waypoint=row,reference=ref,frontal_state=expert,region_approach=region,region_step=None,side=side,clearance_guard=guard,frontal_plan=fr['plan'],target_now=np.array(scene['target_xyz']),other_now=np.array(scene['other_xyz']),tq_now=np.array(scene['target_quat']),oq_now=np.array(scene['other_quat']),target_quat=scene['target_quat'],obstacle_size=scene['other_size'],robot=robot,hands={'left':0,'right':1},recontact_lifecycle=state,step=ctx['step'],load_n=ctx['observed_load_n'],q_region=q,causal_context=dict(previous_q=np.array(ctx['previous_q'])),previous=np.r_[np.zeros(12),ctx['previous_command']],default=np.zeros(23),top_contact_normal_anchor=normal,inactive_anchor=anchors,model_errors={s:dict(position_max_error_m=0.,rotation_max_error=0.) for s in ['left','right']},recontact_log=log,recontact_override=None,clearance_failure=None)
   if stop_example is None:stop_example={k:(v if isinstance(v,types.ModuleType) else copy.deepcopy(v)) for k,v in ns.items()}
   ns['args'].unloaded_recontact_pose=False;before=len(log);exec(program,ns);assert len(log)==before and ns['recontact_override'] is None;ns['args'].unloaded_recontact_pose=True
   exec(program,ns);actual=ns['recontact_override'];assert ns['clearance_failure'] is None and actual is not None;assert actual['kind']==expected['kind'];assert np.max(abs(np.array(actual['command'])-np.array(expected['command'])))<2e-6
   if actual['kind']=='handover':
    assert np.max(abs(np.array(ns['top_contact_normal_anchor'])-np.array(expected['captured_normal_local_up'])))<2e-6;assert np.max(abs(np.array(anchors[inactive])-np.array(expected['captured_inactive_anchor_world'])))<2e-6;assert expert.top_mode=='top_press';handovers+=1
   else:assert expert.top_mode=='top_cross'
   normal=ns['top_contact_normal_anchor'];events+=1
  assert handovers==1;json.dumps(log);reports.append(dict(episode=name,step=t,plant=plant['summary']['plant'],events=events,handovers=handovers))
# Actual collector propagates an explicit active-path stop before command handoff.
ns=stop_example;ns['recontact_lifecycle']=types.SimpleNamespace(active=True,update=lambda **kw:dict(kind='stop',reason='injected_guard_failure',requires_stop=True));exec(program,ns);assert ns['clearance_failure']['phase']=='unloaded_recontact' and ns['recontact_override'] is None
out=dict(passed=True,scope=__doc__,rows=reports,total_events=sum(r['events'] for r in reports),handovers=sum(r['handovers'] for r in reports),stop_propagation_checked=True,source_sha256={str(p):sha(p) for p in [Path(__file__),source,stage/'collect_paired_sorting.py',stage/'recontact_adapter.py',stage/'recontact_lifecycle.py',stage/'recontact_plan.py',stage/'recontact_scene.py',stage/'recontact_tracking.py']},physical_validation=False,training_ready=False)
(stage/'COLLECTOR_ENTRY_CHECK.json').write_text(json.dumps(out,indent=2));print(out['total_events'],out['handovers'],'actual collector events/handovers passed')
