"""Execute exact collector hook AST with explicit sensor fixtures, no simulator."""
from pathlib import Path
import sys,types,ast,json,hashlib
import numpy as np
import torch
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_region_handover_continuity';sys.path[:0]=[str(stage),str(repo)]
# Reuse measured-state lifecycle fixture setup and rerun its current-source check.
import check_region_continuity_lifecycle as fixtures
from region_approach_lifecycle import RegionApproachLifecycle
from region_top_contact import TopContactBypassState
from simfoundry.data.projected_support_reference import projected_support_reference
source=(stage/'collect_paired_sorting.py').read_text();tree=ast.parse(source)
hook=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='region_approach is not None and projected_support_context is not None')
override=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and 'region_step.get' in ast.unparse(n.test) and 'joint_override' in ast.unparse(n.test))
compile_hook=compile(ast.Module(body=[hook],type_ignores=[]),str(stage/'collect_paired_sorting.py'),'exec');compile_override=compile(ast.Module(body=[override],type_ignores=[]),str(stage/'collect_paired_sorting.py'),'exec')
model=fixtures.model;side=fixtures.side;t=fixtures.t;target=fixtures.target;other=fixtures.obstacle;target_quat=fixtures.quat;other_quat=fixtures.ori[fixtures.other][t];reports=[]
for mode,q in [('first_eligible',fixtures.qs[t]),('handover',fixtures.q)]:
 q=np.array(q,dtype=np.float32);body=[];rot=[]
 for hand in ['left','right']:
  m,_,_=model.fk(hand,q);body.append(m[:3,3]);rot.append(Rotation.from_matrix(m[:3,:3]).as_quat())
 wrap=lambda x:types.SimpleNamespace(torch=torch.tensor(np.asarray(x)[None],dtype=torch.float32))
 robot=types.SimpleNamespace(data=types.SimpleNamespace(joint_pos=wrap(np.r_[np.zeros(12),q]),body_pos_w=wrap(body),body_quat_w=wrap(rot)))
 state=fixtures.make(TopContactBypassState);state.top_mode='top_cross';g=model.scene_geometry(side,q,target_xyz=target,target_quat=target_quat,other_xyz=other,other_quat=other_quat,other_size=fixtures.other_size);reference=projected_support_reference(g['vertices'],g['hand_rotation'],g['target_rotation'][:,2]);tip=g['hand_xyz']+g['hand_rotation']@reference['reference_local'];waypoint=state.update(tip,target,other,fixtures.plan['target_radius_x'],fixtures.plan['obstacle_radius_x'],tip=tip,quat=target_quat,control_offset_local=reference['reference_local'],load_n=0.,hand_obstacle_gap_m=g['hand_other_gap_m'])
 life=RegionApproachLifecycle();scene={'parcel_box':target if side=='right' else other,'mailer':target if side=='left' else other};inactive='right' if side=='left' else 'left'
 ns=dict(previous=np.r_[np.zeros(12),q.astype(float)],default=np.zeros(23),np=np,robot=robot,hands={'left':0,'right':1},ordered_ids=list(range(23)),region_model=model,region_approach=life,frontal_state=state,reference=reference,projected_support_context={k:v.tolist() for k,v in reference.items() if k in ['reference_local','center_local','lowest_vertex_local','world_normal']},side=side,env=None,parcel_xyz=lambda env,actor:scene[actor],target_actor='parcel_box' if side=='right' else 'mailer',obstacle_actor='mailer' if side=='right' else 'parcel_box',target_quat=target_quat.tolist(),obstacle_quat=other_quat.tolist(),obstacle_size=fixtures.other_size,args=types.SimpleNamespace(waist_limit_rad=1.),U1_JOINT_LIMIT_LO=np.r_[np.zeros(12),fixtures.lo],U1_JOINT_LIMIT_HI=np.r_[np.ones(12),fixtures.hi],inactive_anchor={inactive:fixtures.anchor},top_contact_normal_anchor=None,load_n=0.,waypoint=waypoint,point_kwargs={},region_log=[],step=17)
 exec(compile_hook,ns);result=ns['region_step'];assert result and result['joint_override'];assert bool(result['handover'])==(mode=='handover');assert len(ns['region_log'])==1
 ns.update(action=np.full(23,.123,dtype=float),default=np.zeros(23),coordination_log=[{'waist_target_rad':.123}]);exec(compile_override,ns);assert np.array_equal(ns['action'][12:23],np.array(result['next_q']));assert ns['coordination_log'][-1]['waist_target_rad']==result['next_q'][0]
 if mode=='handover':assert np.array_equal(ns['action'][12:23],q.astype(float));assert ns['frontal_state'].selected_surface_local_xy is not None
 reports.append(dict(fixture=mode,actual_hook_executed=True,handover=result['handover'],joint_override_exact=True,runtime_fk_check=result['runtime_fk_check']))
 if mode=='first_eligible':
  with np.load(fixtures.ep/'raw.npz') as raw:actual_previous=raw['action'][fixtures.t-1].astype(float)
  ns['previous']=actual_previous;ns['region_approach']=RegionApproachLifecycle();ns['region_log']=[]
  exec(compile_hook,ns);pred=ns['region_step'];assert pred is not None and pred['joint_override']
  residual=q.astype(float)-actual_previous[12:23];assert np.max(abs(np.array(pred['causal_tracking_residual_rad'])-residual))<1e-12
  reports.append(dict(fixture='actual_previous_command',current_residual_exact=True,actual_hook_executed=True,joint_override=pred['joint_override']))
 # A 2mm sensor/FK mismatch must stop before proposing a joint override.
 robot.data.body_pos_w.torch[0,0,0]+=.002;ns['region_approach']=RegionApproachLifecycle();ns['projected_support_context']={};
 try:exec(compile_hook,ns)
 except ValueError as e:assert 'differs from observed robot' in str(e)
 else:raise AssertionError('FK mismatch accepted')
 # Disabled hook must leave the existing waypoint/action alone.
 old_action=ns['action'].copy();ns['region_approach']=None;exec(compile_hook,ns);ns['region_step']=None;exec(compile_override,ns);assert np.array_equal(ns['action'],old_action)
report=dict(rows=reports,fk_mismatch_rejected=2,default_off_preserved=2,staged_collector_sha256=hashlib.sha256((stage/'collect_paired_sorting.py').read_bytes()).hexdigest(),scope='Exact staged collect() AST hook and action override executed using explicit torch sensor fixtures generated from independently checked URDF FK; NOT real Isaac dynamics or robot output. Original state default replay and lifecycle checks rerun. No training admission.',training_ready=False)
(stage/'COLLECTOR_WIRING_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
