"""Fixed measured-state replay through original native joint-command chain.
Not recursive physics, full-prefix replay or dynamic clearance certification.
"""
import copy
import numpy as np
from task_ik_precision import solve
from joint_edge_inward_adapter import refine_record
from joint_edge_clearance_adapter_candidate import repair_record
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI

def replay(*,guard,row,coordinate,current,previous,object_xyz,object_rotation,core_size,original=False):
    c=copy.deepcopy(coordinate);q=np.asarray(current,dtype=np.float32);prev=np.asarray(previous,dtype=np.float32)
    assert not c.get('region_joint_override') and not c.get('terminal_joint_hold')
    assert c['active_side']=='right' and c['contact_bout_yaw_tracking'] is None
    assert c['front_loaded_z_priority']['selected'] is False and c['front_loaded_z_priority']['applied'] is False
    assert c['joint_transport_clearance']['selected'] is False and c['joint_transport_clearance']['applied'] is False
    inp=copy.deepcopy(c['task_inputs']);np.testing.assert_array_equal(inp['current'],q)
    errors=[]
    for side in ['left','right']:
        target=row['target_xyz'] if side=='right' else c['inactive_anchor']
        errors.extend(np.clip(np.float32(.72)*(np.asarray(target,dtype=np.float32)-np.asarray(c['control_point_positions'][side],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
    if original:np.testing.assert_array_equal(errors,inp['error'][:6])
    inp['error'][:6]=errors;inp['previous']=prev.tolist();c['task_inputs']=inp
    command,ik=solve(enabled=True,geometry=guard.geometry,**inp)
    record=dict(ik=ik,task_inputs=inp,accepted=False,training_ready=False)
    if command is None:return None,dict(record,stopped_at='original_task_ik')
    command=np.asarray(command,dtype=np.float32);command[0]=np.clip(command[0],-.98,.98)
    command=np.clip(command,prev-np.float32(.055),prev+np.float32(.055))
    command=np.clip(command,np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32);command[0]=np.clip(command[0],-1.,1.)
    refined,edge=refine_record(enabled=True,row=row,coordinate=c,current=q,previous=prev,parent_command=command,object_xyz=object_xyz,object_rotation=object_rotation,core_size=core_size,model=guard.model,side='right',analytic_retry=True,parent_seed_retry=True)
    c['joint_edge_refinement']=edge;record['edge']=edge;command=refined
    if edge.get('override'):
        fixed,repair=repair_record(guard=guard,row=row,coordinate=c,current=q,previous=prev,command=command,object_rotation=object_rotation,object_xyz=object_xyz,core_size=core_size)
        record['repair']=repair
        if fixed is not None:command=np.asarray(fixed,dtype=np.float32)
        else:assert not guard.command(command,q,prev)['accepted']
    final=guard.command(command,q,prev);record.update(final=final,accepted=final['accepted'],command=command.tolist())
    return (command if final['accepted'] else None),record
