"""Unwired adapter for an original, successfully executed and checked action.
Mutates only state.command Y and matching state.last_waypoint_xy Y for the NEXT
update. Does not rewrite the current row, action, pressure or guard outcome.
Caller must invoke once after original post-action guard, before next update.
"""
import numpy as np
from reconcile_rear_waypoint import reconcile

def apply_post_commit(*,enabled=False,step,side,rear_selected,state,row,coordinate,
                      action,final_guard,post_guard,execution_completed,
                      slip_contact,guard):
 if type(enabled) is not bool or type(rear_selected) is not bool or type(execution_completed) is not bool:raise ValueError('Flags must be bool')
 if not enabled:return None
 if type(step) is not int or step<0:raise ValueError('Invalid action step')
 if side not in ['left','right']:raise ValueError('Invalid active side')
 base=dict(step=step,version='rear_box_post_commit_adapter_draft_v1',applied=False,current_action_changed=False,training_ready=False)
 def unchanged(why):return dict(base,reason=why)
 if not execution_completed:return unchanged('original_action_not_executed')
 for item,phase in [(final_guard,'final_command'),(post_guard,'post')]:
  if item.get('step')!=step or item.get('phase')!=phase:raise ValueError('Stale or mismatched original guard record')
  if type(item.get('accepted')) is not bool:raise ValueError('Missing original guard decision')
  if not item['accepted']:return unchanged('original_'+phase+'_guard_rejected')
 if step==0:return unchanged('first_zero_frame_preserved')
 if side!='right' or not rear_selected:return unchanged('not_rear_box')
 if row is None or row.get('step')!=step or coordinate is None or coordinate.get('step')!=step:raise ValueError('Missing current control record')
 if row['mode']!='top_push':return unchanged('original_mode_guard')
 edge=coordinate.get('joint_edge_refinement')
 if not isinstance(edge,dict):raise ValueError('Missing edge refinement record')
 for key in ['input_selected','override']:
  if type(edge.get(key)) is not bool:raise ValueError('Invalid edge decision')
 if not edge['input_selected'] or not edge['override']:return unchanged('no_applied_edge_refinement')
 if coordinate.get('region_joint_override') or coordinate.get('terminal_joint_hold'):raise ValueError('Conflicting original controller branch')
 if coordinate['active_side']!=side or not row.get('rear_cop_centering',{}).get('override'):raise ValueError('Invalid rear branch binding')
 command=np.asarray(action,dtype=float);current=np.asarray(coordinate['upper_q'],dtype=float);previous=np.asarray(edge['previous_upper_command'],dtype=float)
 if any(x.shape!=(11,) or not np.isfinite(x).all() for x in [command,current,previous]):raise ValueError('Invalid finite11D command context')
 if not np.array_equal(command,np.asarray(final_guard['command'])):raise ValueError('Final guard is for a different action')
 if not np.array_equal(previous,np.asarray(final_guard['previous'])) or not np.array_equal(current,np.asarray(final_guard['current'])):raise ValueError('Final guard current/previous mismatch')
 if not np.array_equal(command,np.asarray(edge['final_upper_command'])):return unchanged('later_original_command_repair_preserved')
 rechecked=guard.command(command,current,previous)
 if not rechecked['accepted']:raise ValueError('Recorded accepted command fails original guard')
 requested=np.asarray(row['target_xyz'],dtype=float)
 if state.mode!=row['mode'] or state.top_mode!=row['mode']:raise ValueError('Route mode mismatch')
 if not np.array_equal(np.asarray(state.command),requested) or not np.array_equal(np.asarray(state.last_waypoint_xy),requested[:2]):raise ValueError('Stale or already reconciled route cursor')
 if not isinstance(slip_contact,dict) or slip_contact.get('valid') is not True:return unchanged('no_valid_measured_contact')
 load=slip_contact['normal_load_n'];offset=np.asarray(row['control_offset_local'],dtype=float)
 if offset.shape!=(3,) or not np.isfinite(offset).all():raise ValueError('Invalid current virtual reference offset')
 T,_,_=guard.model.fk(side,current);actual=T[:3,3]+T[:3,:3]@offset
 if np.max(abs(actual-np.asarray(row['observed_support_xyz'])))>2e-6 or np.max(abs(actual-np.asarray(coordinate['control_point_positions'][side])))>2e-6:raise ValueError('Current FK/reference binding mismatch')
 U,_,_=guard.model.fk(side,command);nominal=U[:3,3]+U[:3,:3]@offset
 suggestion=reconcile(enabled=True,side=side,mode=row['mode'],rear_selected=True,edge_selected=True,edge_override=True,command_accepted=True,requested_xyz=requested,committed_reference_xyz=nominal,normal_load_n=load)
 record=dict(base,reason=suggestion['reason'],suggestion=suggestion,committed_upper_command=command.tolist(),current_upper_q=current.tolist(),previous_upper_command=previous.tolist(),reference_offset_local=offset.tolist(),observed_normal_load_n=float(load),state_before=dict(command=list(state.command),last_waypoint_xy=list(state.last_waypoint_xy)))
 if suggestion['override']:
  state.command=tuple(suggestion['next_state_command_xyz']);state.last_waypoint_xy=tuple(suggestion['next_state_last_waypoint_xy']);record['applied']=True
 record['state_after']=dict(command=list(state.command),last_waypoint_xy=list(state.last_waypoint_xy))
 return record
