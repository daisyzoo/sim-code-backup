"""Single UNISSUED step173 joint proposal on actual history; no rollout.
Use original logged six position Jacobian rows and measured q/u[t-1]. Restore
contact-normal rows from independent FK, retaining actual captured normal anchor.
This normal reconstruction is nominal (runtime wrist quaternion not archived).
Validate against neighboring actual normal records and finite differences; it is
not claimed byte-identical to an unexecuted runtime coordinator invocation.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_midpoint';sys.path[:0]=[str(S),str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
draft=json.loads((S/'DRAFT_CHECK.json').read_text());assert draft['passed']
for p,h in draft['source_sha256'].items():assert sha(p)==h,p
# Execute the exact previously bound fixture preparation, stopping before its
# tests/report writer. This produces actual class updates off/on, not fake history.
p=W/'check_front_corridor_midpoint_draft.py';tree=ast.parse(p.read_text());cut=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='negatives' for t in n.targets));ns={'__file__':str(p),'__name__':'midpoint_joint_fixture'};exec(compile(ast.Module(body=tree.body[:cut],type_ignores=[]),str(p),'exec'),ns)
row=dict(ns['on'],step=173);ep=ns['ep'];t=173
np.testing.assert_array_equal(row['target_xyz'],draft['actual_route_cop_single_step_fixture']['unissued_candidate_waypoint'])
from clearance_runtime import ClearanceGuard
from task_ik_precision import solve
from front_loaded_z_priority import FrontLoadedZPriority
from simfoundry.data.contact_normal_constraint import contact_normal_constraint
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from front_loaded_z_priority_episode_inputs import EpisodeInputs
from audit_front_loaded_z_priority_parent import verify_parent
from audit_front_loaded_z_priority_applied_row import verify_applied
from audit_front_z_priority_rotation_representation_v2 import recorded_rotation,RuntimeGapRepresentation
from front_loaded_z_priority_audit_geometry import sweep
E=EpisodeInputs(ep);guard=ClearanceGuard(ROOT,S);q=E.q[t];prev=E.u[t-1];c=copy.deepcopy(E.coords[t]);a=copy.deepcopy(c['task_inputs']);assert np.array(a['jacobian']).shape==(6,11) and c['contact_normal_tracking'] is None
# Native FK and independent archived FK must agree before any proposal is solved.
M,jl,jw=guard.model.fk('left',q);np.testing.assert_allclose(M,E.hand.fk(q,'left'),atol=2e-12,rtol=0)
anchor=E.capture[t]['old_normal_anchor'];assert anchor==E.coords[t-1]['contact_normal_tracking']['target_local_up']
normal=contact_normal_constraint(M[:3,:3],jw,anchor)
h=2e-6;fd=np.column_stack([.15*(E.hand.fk(q+np.eye(11)[i]*h,'left')[2,:3]-E.hand.fk(q-np.eye(11)[i]*h,'left')[2,:3])/(2*h) for i in range(11)])
np.testing.assert_allclose(normal['jacobian'],fd,atol=2e-9,rtol=0)
neighbor=[]
for i in range(166,173):
    mm,_,jj=guard.model.fk('left',E.q[i]);n=contact_normal_constraint(mm[:3,:3],jj,E.coords[i]['contact_normal_tracking']['target_local_up']);actual=E.coords[i]['contact_normal_tracking']
    errs={k:float(np.max(abs(np.asarray(n[k])-actual[k]))) for k in ['jacobian','error','current_local_up']}
    assert max(errs.values())<=2e-6;neighbor.append(dict(step=i,errors=errs))
# First reproduce the actual guard-lift parent using the unchanged original task.
base,base_record=solve(enabled=True,geometry=guard.geometry,**a);assert base_record['accepted'];np.testing.assert_array_equal(base.astype(np.float32),E.u[t].astype(np.float32))
# Candidate retains position Jacobians/current/previous/bounds/damping, changes
# active Cartesian target, and adds original normal-hold task for top_push.
a['jacobian']=np.vstack([np.asarray(a['jacobian'],np.float32),np.asarray(normal['jacobian'],np.float32)]).tolist()
error=np.asarray(a['error'],np.float32);error[:3]=np.clip(np.float32(.72)*(np.asarray(row['target_xyz'],np.float32)-np.asarray(c['control_point_positions']['left'],np.float32)),np.float32(-.035),np.float32(.035));a['error']=np.r_[error,np.asarray(normal['error'],np.float32)].tolist()
parent,solve_record=solve(enabled=True,geometry=guard.geometry,**a);assert solve_record['accepted']
parent=np.asarray(parent,np.float32);parent[0]=np.clip(parent[0],-.98,.98);parent=np.clip(parent,prev.astype(np.float32)-np.float32(.055),prev.astype(np.float32)+np.float32(.055));parent=np.clip(parent,np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32)
c.pop('front_loaded_z_priority',None);c.update(task_inputs=a,self_clearance_task=solve_record,contact_normal_tracking={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in normal.items()},waist_target_rad=float(parent[0]),front_loaded_z_priority_side='left')
expert=dict(E.experts[t],mode='top_push',target_xyz=row['target_xyz']);parent_proof=verify_parent(coordinate=c,row=row,expert=expert,current=q,previous_actual=prev,parent=parent,side='left',elbows=E.elbows,bounded_solver=E.solver)
with np.load(ep/'parcel_orientation.npz') as z:R=recorded_rotation(z['mailer'][t]);OR=recorded_rotation(z['box'][t])
command,metadata=FrontLoadedZPriority(guard).refine(step=t,selected=True,row=row,coordinate=c,current=q,previous=prev,parent_command=parent,target_rotation=R,other_xyz=E.oxy[t],other_rotation=OR,other_size=E.size)
final=guard.command(command,q,prev);assert final['accepted']
proof=None
if metadata['applied']:
    c['unexecuted_parent_waist_target_rad']=c['waist_target_rad'];c['waist_target_rad']=float(command[0]);c['front_loaded_z_priority']=metadata
    proof=verify_applied(metadata=metadata,coordinate=c,row=row,expert=expert,current=q,previous_actual=prev,output=command,side='left',elbows=E.elbows,bounded_solver=E.solver,hand=E.hand,geometry=RuntimeGapRepresentation(E.geometry),capture_row=E.capture[t],previous_packet=E.packets[t-1],target_xyz=E.xyz[t],target_rotation=R,other_xyz=E.oxy[t],other_rotation=OR,other_size=E.size)
size=np.maximum(E.size,np.nextafter(np.asarray(E.size,np.float32),np.float32(np.inf)).astype(float));paths={s:sweep(E.geometry,E.hand,q,command,s,E.oxy[t],OR,size) for s in ['left','right']};assert all(v['certified'] for v in paths.values())
sources=dict(draft['source_sha256'],**E.sources)
for p in [Path(__file__),S/'DRAFT_CHECK.json',S/'task_ik_precision.py',S/'front_loaded_z_priority.py',W/'audit_front_z_priority_rotation_representation_v2.py']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,step=t,unissued=True,previous_is_actual_raw_action=True,original_guard_lift_command_reproduced=True,normal_finite_difference_error=float(np.max(abs(normal['jacobian']-fd))),neighbor_actual_normal_checks=neighbor,proposal_waypoint=row['target_xyz'],parent_command=parent.tolist(),candidate_command=command.tolist(),original_parent_proof=parent_proof,z_priority=metadata,independent_applied_proof=proof,original_final_guard=final,additional_direct_matrix_non_target_paths=paths,source_sha256=sources,collector_wired=False,physical_started=False,full_robot_dynamic_path_verified=False,training_ready=False)
with (S/'SINGLE_STEP_JOINT_PROPOSAL_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,step=t,unissued=True,z_applied=metadata['applied'],z_reason=metadata['reason'],final_guard=final['accepted'],independent_applied_proof=proof),indent=2))
