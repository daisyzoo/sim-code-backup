"""Pure record adapter for the isolated joint edge/clearance intersection.
Only an existing edge override is eligible. Original pressure, region and task
selection remain outside this adapter; no scene/physics writes occur here.
"""
import numpy as np
from joint_edge_clearance_intersection_candidate import repair

def repair_record(*,guard,row,coordinate,current,previous,command,object_rotation,object_xyz,core_size):
 tr=coordinate.get('joint_edge_refinement')
 if not tr or tr.get('override') is not True:raise ValueError('Existing edge override required')
 if row['mode']!='top_push' or not tr.get('input_selected') or coordinate.get('region_joint_override') or coordinate.get('terminal_joint_hold'):raise ValueError('Original edge eligibility required')
 side=coordinate['active_side'];direction=-1 if side=='right' else 1
 if side not in ['left','right']:raise ValueError('Invalid side')
 q=np.asarray(current,float);prev=np.asarray(previous,float);old=np.asarray(command,float)
 for supplied,stored in [(q,coordinate['upper_q']),(prev,tr['previous_upper_command']),(old,tr['final_upper_command'])]:
  if not np.array_equal(supplied,np.asarray(stored,float)):raise ValueError('Recorded command/input mismatch')
 inp=coordinate['task_inputs'];R=np.asarray(object_rotation,float);xyz=np.asarray(object_xyz,float);core=np.asarray(core_size,float)
 if R.shape!=(3,3) or not np.isfinite(R).all() or not np.allclose(R.T@R,np.eye(3),atol=1e-6) or np.linalg.det(R)<.99999 or xyz.shape!=(3,) or core.shape!=(3,) or not np.isfinite(xyz).all() or not np.isfinite(core).all() or (core<=.02).any():raise ValueError('Invalid actual parcel geometry')
 if not np.array_equal(q,np.asarray(inp['current'])) or not np.array_equal(prev,np.asarray(inp['previous'])) or np.any(np.asarray(inp['preferred_step'])!=0):raise ValueError('Original zero-prior task inputs required')
 local=R.T@(np.asarray(row['rear_cop_centering']['cop_world'])-xyz);axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01]
 if axes!=tr['threatened_axes']:raise ValueError('Original edge selection mismatch')
 normals=np.array([-np.sign(local[k])*R[:,k] for k in axes]);offset=np.asarray(row['control_offset_local'],float)
 if offset.shape!=(3,) or not np.isfinite(offset).all():raise ValueError('Invalid original reference')
 def point(x):
  T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@offset;a,b,c=v;skew=np.array([[0.,-c,b],[c,0.,-a],[-b,a,0.]])
  return T[:3,3]+v,jl-skew@jw
 if np.max(abs(point(q)[0]-row['observed_support_xyz']))>2e-6:raise ValueError('Current reference mismatch')
 x,trace=repair(guard=guard,current=q,previous=prev,command=old,context=dict(jacobian=inp['jacobian'],error=inp['error'],damping=inp['damping'],normals=normals,direction=direction,inward_m=.0005 if side=='right' else 0.,point_and_jacobian=point,parent=tr['parent_final_upper_command']))
 trace.update(input_command=old.tolist(),output_command=None if x is None else x.tolist(),side=side,inward_requirement_m=.0005 if side=='right' else 0.,original_threatened_axes=axes,object_xyz=xyz.tolist(),object_rotation=R.tolist(),core_size=core.tolist(),control_offset_local=offset.tolist(),current=q.tolist(),previous=prev.tolist(),scope='Nominal final-command intersection only; not physical contact or whole-body proof.')
 return x,trace
