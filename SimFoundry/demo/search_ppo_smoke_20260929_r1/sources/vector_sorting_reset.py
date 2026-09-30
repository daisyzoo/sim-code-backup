"""Explicit episode-boundary resets for privileged expert-search diagnostics.

Never call during an episode to assist object transport.
"""
import math
import torch

def reset_paired_layouts(env, env_ids, layouts):
    ids=torch.as_tensor(env_ids,dtype=torch.int32,device=env.device)
    if ids.ndim!=1 or len(ids)!=len(layouts) or len(torch.unique(ids))!=len(ids):
        raise ValueError('Expected one layout per distinct environment ID')
    if len(ids)==0 or int(ids.min())<0 or int(ids.max())>=env.num_envs:
        raise ValueError('Invalid environment IDs')
    env.reset(env_ids=ids)
    expected={}
    origins=env.scene.env_origins[ids.long()]
    for key,name in [('box','parcel_box'),('mailer','mailer')]:
        rows=[]
        for layout in layouts:
            xyz=layout[key+'_xyz'];yaw=float(layout.get(key+'_yaw',0.))
            if len(xyz)!=3 or not all(math.isfinite(float(x)) for x in [*xyz,yaw]):
                raise ValueError('Nonfinite or invalid reset pose')
            rows.append([*xyz,0.,0.,math.sin(yaw/2),math.cos(yaw/2)])
        pose=torch.tensor(rows,dtype=torch.float32,device=env.device)
        pose[:,:3]+=origins
        asset=env.scene[name]
        asset.write_root_pose_to_sim_index(root_pose=pose,env_ids=ids)
        asset.write_root_velocity_to_sim_index(root_velocity=torch.zeros((len(ids),6),device=env.device),env_ids=ids)
        expected[key]=pose
    env.scene.write_data_to_sim()
    env.sim.forward()
    return expected
