"""Single unissued joint proposal594 using recorded q/u and position Jacobian.
The new normal constraint uses nominal FK: wrist rotation at594 was not archived
in coordinator output because original guard disabled that constraint. Neighbor
actual normal rows and finite differences validate reconstruction tolerance, not
bit-exact unknown runtime rotation. No physical rollout or future response.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';D=W/'front_corridor_lateral_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from task_ik_precision import solve
from front_loaded_z_priority import FrontLoadedZPriority
from joint_transport_runtime import JointTransportRuntime
from recontact_scene import RecontactScene
from simfoundry.data.contact_normal_constraint import contact_normal_constraint
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
n=read(D/'INTEGRATED_NATIVE_BOUNDARY_CHECK.json')
for p,h in n['source_sha256'].items():assert sha(p)==h,p
r=W/'joint_transport_reserve_physical_r1';ep=r/'case_840023/layout_840023_nudge_mailer_to_bin';cs={x['step']:x for x in read(ep/'coordination.json')};fr=read(ep/'frontal_bypass.json');rows={x['step']:x for x in fr['rows']};jr=read(ep/'joint_transport_clearance.json')['rows'][594];ctx=jr['collector_context'];assert jr['step']==594 and not ctx.get('region_joint_override')
with np.load(ep/'raw.npz') as z:q=z['q'][:595,12:23].astype(float);u=z['action'][:595,12:23].astype(float)
np.testing.assert_array_equal(ctx['current'],q[594]);np.testing.assert_array_equal(ctx['previous_command'],u[593]);assert cs[594]['contact_normal_tracking'] is None and not cs[594]['terminal_joint_hold']
assert not fr['plan'].get('rear_joint_edge_command',{}).get('enabled',False)
guard=ClearanceGuard(ROOT,S);scene=RecontactScene(guard,**ctx['scene']);a=copy.deepcopy(cs[594]['task_inputs']);assert np.asarray(a['jacobian']).shape==(6,11)
def clamp(command):
 command=np.asarray(command,np.float32);command[0]=np.clip(command[0],-.98,.98);command=np.clip(command,u[593].astype(np.float32)-np.float32(.055),u[593].astype(np.float32)+np.float32(.055));return np.clip(command,np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32)
old,oldsolve=solve(enabled=True,geometry=guard.geometry,**a);assert oldsolve['accepted'];old=clamp(old);np.testing.assert_allclose(old,u[594],atol=2e-6,rtol=0)
row=dict(n['candidate_row'],step=594);anchor=cs[593]['contact_normal_tracking']['target_local_up'];recovery={x['step']:x for x in read(ep/'front_recontact_center.json')['rows']};assert recovery[593]['old_normal_anchor']==anchor
normal_checks=[]
for t in range(588,594):
 actual=cs[t]['contact_normal_tracking'];assert actual is not None and actual['target_local_up']==anchor
 pose,_,angular=guard.model.fk('left',q[t]);nrm=contact_normal_constraint(pose[:3,:3],angular,anchor);errors={k:float(np.max(abs(np.asarray(nrm[k])-actual[k]))) for k in ['jacobian','error','current_local_up']};assert max(errors.values())<=2e-6;normal_checks.append(dict(step=t,errors=errors))
pose,_,angular=guard.model.fk('left',q[594]);normal=contact_normal_constraint(pose[:3,:3],angular,anchor);h=2e-6;fd=np.column_stack([.15*(guard.model.fk('left',q[594]+np.eye(11)[j]*h)[0][2,:3]-guard.model.fk('left',q[594]-np.eye(11)[j]*h)[0][2,:3])/(2*h) for j in range(11)]);np.testing.assert_allclose(fd,normal['jacobian'],atol=2e-9,rtol=0)
a['error'][:3]=np.clip(np.float32(.72)*(np.asarray(row['target_xyz'],np.float32)-np.asarray(cs[594]['control_point_positions']['left'],np.float32)),np.float32(-.035),np.float32(.035)).tolist();a['jacobian']+=np.asarray(normal['jacobian'],np.float32).tolist();a['error']+=np.asarray(normal['error'],np.float32).tolist()
parent,solve_record=solve(enabled=True,geometry=guard.geometry,**a);assert parent is not None and solve_record['accepted'];parent=clamp(parent);coordinate=copy.deepcopy(cs[594]);coordinate.pop('joint_transport_clearance');coordinate.pop('front_loaded_z_priority');coordinate.update(task_inputs=a,self_clearance_task=solve_record,contact_normal_tracking={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in normal.items()},waist_target_rad=float(parent[0]),front_loaded_z_priority_side='left')
z,zrec=FrontLoadedZPriority(guard).refine(step=594,selected=True,row=row,coordinate=coordinate,current=q[594],previous=u[593],parent_command=parent,target_rotation=scene.rotation,other_xyz=scene.other,other_rotation=Rotation.from_quat(scene.other_quat).as_matrix(),other_size=scene.other_size)
assert not zrec['applied'] and zrec['reason']=='not_top_push';coordinate['front_loaded_z_priority']=zrec
runtime=JointTransportRuntime(guard,ROOT,S,enabled=True);command,record=runtime.refine(step=594,selected=True,side='left',row=row,coordinate=coordinate,scene=scene,current=q[594],previous_q=q[593],previous_command=u[593],parent_command=z,decay=ctx['decay']);final=guard.command(command,q[594],u[593]);assert final['accepted']
elbows=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');gaps=elbows.gap(command);np.testing.assert_allclose(gaps,final['gaps_m'],atol=2e-10,rtol=0);assert min(gaps)>=.005-2e-7 and max(abs(command-u[593]))<=.0550002
bias=q[594]-u[593]-np.asarray(ctx['decay'])*(q[593]-u[593]);prediction=(1-np.asarray(ctx['decay']))*command+np.asarray(ctx['decay'])*q[594]+bias
margins={name:(1000*runtime.paths.margins(v,scene.record())).tolist() for name,v in [('measured',q[594]),('nominal',command),('predicted',prediction)]}
for p in [Path(__file__),ep/'raw.npz',S/'COLLECTOR_PREPARATION.json']:sources[str(p)]=sha(p)
for module in list(sys.modules.values()):
 f=getattr(module,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,step=594,original_emitted_guard_command_reproduced=True,actual_previous_action_used=True,normal_neighbor_checks=normal_checks,normal_fd_max_error=float(np.max(abs(fd-normal['jacobian']))),candidate_waypoint=row['target_xyz'],candidate_command=command.tolist(),new_task_inputs=a,task_solver=solve_record,z_record=zrec,joint_refinement=record,final_guard=final,independent_elbow_gaps_m=gaps.tolist(),margin_labels=runtime.paths.labels,nominal_margin_predictions_mm=margins,source_sha256=sources,nominal_only=True,physical_started=False,full_dynamic_path_verified=False,training_ready=False)
with (D/'SINGLE_UNISSUED_JOINT_PROPOSAL.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,refinement_reason=record['reason'],applied=record['applied'],final_guard=final['accepted'],normal_fd_max_error=report['normal_fd_max_error'],nominal_margin_predictions_mm=margins),indent=2))
