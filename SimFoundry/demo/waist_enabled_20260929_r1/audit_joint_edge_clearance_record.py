"""Independent record certificate for final edge/clearance repair.
Uses original edge auditor, independent hand/elbow URDF, all-support-vertex KKT.
Caller MUST bind q/previous/final command and actual parcel pose to raw evidence.
No candidate solver/helper is imported. Not a whole-episode or admission audit.
"""
import numpy as np
from support_vertex_stationarity import certificate
from audit_box_inward_refinement import verify_refinement
from audit_unloaded_wrist_prior_live import near

def verify(*,hand,elbows,coordinate,row,trace,q,previous,command,object_xyz,object_rotation,core_size,lower,upper,limits):
 q,previous,command,object_xyz,rotation,core=(np.asarray(v,float) for v in [q,previous,command,object_xyz,object_rotation,core_size]);old=coordinate['joint_edge_refinement'];side=coordinate['active_side'];direction=-1 if side=='right' else 1;active=[3,4,5] if side=='right' else [0,1,2];inward=.0005 if side=='right' else 0.
 assert old['override'] is True and old['input_selected'] is True and row['mode']=='top_push' and not coordinate.get('region_joint_override') and not coordinate.get('terminal_joint_hold')
 near(q,coordinate['upper_q'],0);near(previous,old['previous_upper_command'],0);near(trace['current'],q,0);near(trace['previous'],previous,0);near(trace['input_command'],old['final_upper_command'],0);near(trace['output_command'],command,0);near(trace['object_xyz'],object_xyz,0);near(trace['object_rotation'],rotation,1e-12);near(trace['core_size'],core,0)
 assert trace['side']==side and trace['inward_requirement_m']==inward
 inp=coordinate['task_inputs'];near(inp['current'],q,0);near(inp['previous'],previous,0);near(inp['lower'],lower,0);near(inp['upper'],upper,0);near(inp['step_limits'],limits,0);assert np.all(np.array(inp['preferred_step'])==0)
 J=np.array(inp['jacobian']);err=np.array(inp['error']);damping=np.array(inp['damping']);assert J.shape==(9,11)
 near(J[:6],coordinate['control_jacobian_world'],0);near(J[6:],np.array(coordinate['contact_normal_tracking']['jacobian'],dtype=np.float32),0)
 errors=[]
 for side_name in ['left','right']:
  goal=row['target_xyz'] if side_name==side else coordinate['inactive_anchor'];point=np.asarray(coordinate['control_point_positions'][side_name],dtype=np.float32);errors.extend(np.clip(np.float32(.72)*(np.array(goal,dtype=np.float32)-point),np.float32(-.035),np.float32(.035)))
 errors.extend(np.array(coordinate['contact_normal_tracking']['error'],dtype=np.float32));near(err,errors,0)
 offset=np.asarray(row['control_offset_local']);near(trace['control_offset_local'],offset,0);h=2e-7
 def point(x):
  T=hand.fk(x,side);return T[:3,3]+T[:3,:3]@offset
 def point_jacobian(x):
  G=np.zeros((3,11))
  for j in range(11):
   delta=np.eye(11)[j]*h;G[:,j]=(point(x+delta)-point(x-delta))/(2*h)
  return point(x),G
 near(point(q),row['observed_support_xyz'],2e-6);local=rotation.T@(np.array(row['rear_cop_centering']['cop_world'])-object_xyz);axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01];assert axes==trace['original_threatened_axes']==old['threatened_axes'];normals=np.array([-np.sign(local[k])*rotation[:,k] for k in axes])
 parent=np.array(old['parent_final_upper_command']);original=np.array(old['final_upper_command'])
 # Certify the original edge command mathematically even though its elbow gap
 # can fail; that failure is precisely the reason for the second joint solve.
 baseline=verify_refinement(old,parent,original,previous,q,J,err,damping,lower,upper,limits,point_jacobian,rotation,local,core,direction,active,inward_enabled=side=='right')
 lo=np.maximum.reduce([lower,q-limits,previous-.055]);hi=np.minimum.reduce([upper,q+limits,previous+.055]);old_feasible=bool(min(elbows.gap(original))>=.005-2e-7 and np.all(original>=lo-2e-7) and np.all(original<=hi+2e-7))
 if not trace['changed']:
  assert trace['reason']=='original_final_guard_passed' and old_feasible;near(command,original,0)
  return dict(passed=True,changed=False,original_edge=baseline)
 assert trace['reason']=='joint_edge_and_clearance' and not old_feasible
 assert np.all(original>=lo-2e-7) and np.all(original<=hi+2e-7) and min(elbows.gap(original))<.005-2e-7
 p,G=point_jacobian(command);motion=p-point(q);values=np.r_[normals@motion-inward,direction*motion[1]];jac=np.vstack([normals@G,direction*G[1]])
 dq=command-q;grad=J.T@(J@dq-err)+damping*damping*dq;cert=certificate(geometry=elbows,x=command,gradient=grad,lower=lo,upper=hi,extra_values=values,extra_jacobian=jac)
 assert cert['passed'],cert
 return dict(passed=True,changed=True,original_edge=baseline,certificate=cert)
