"""Read-only leading-edge margin of the measured loaded hand/parcel contact patch."""
import math
from simfoundry.data.top_contact_bypass import rotation_xyzw
from simfoundry.data.top_push_contact_geometry import forward_edge_distance


def loaded_forward_margin(packet,side,actor,target_xyz,target_quat,size,direction):
    if len(target_xyz)!=3 or not all(math.isfinite(x) for x in target_xyz):raise ValueError('Invalid target position')
    forward_edge_distance((0.,0.,0.),target_quat,size,direction)
    r=rotation_xyzw(target_quat);points=[];weights=[];margins=[];net_world=[0.,0.,0.]
    for c in (packet or {}).get('parcel_contacts',[]):
        shapes=c['shapes'];slots=[i for i,s in enumerate(shapes) if '/'+actor+'/' in s]
        if len(slots)!=1 or not any(side+'_wrist' in s for s in shapes):continue
        if any(len(c[k])!=3 or not all(math.isfinite(v) for v in c[k]) for k in ('force_world_N','position_world')):raise ValueError('Invalid measured contact')
        sign=1 if slots[0]==1 else -1
        for i in range(3):net_world[i]+=sign*float(c['force_world_N'][i])
        normal_load=-sign*sum(c['force_world_N'][i]*r[i][2] for i in range(3))
        if normal_load<=.05:continue
        local=tuple(sum((c['position_world'][i]-target_xyz[i])*r[i][k] for i in range(3)) for k in range(3))
        points.append(local);weights.append(normal_load);margins.append(forward_edge_distance(local,target_quat,size,direction))
    total=sum(weights)
    if not weights:return dict(force_on_target_world_n=net_world,valid=False,normal_load_n=0.,weighted_forward_edge_distance_m=None,min_sample_forward_edge_distance_m=None,contact_count=0)
    center=tuple(sum(w*p[k] for w,p in zip(weights,points))/total for k in range(3))
    return dict(force_on_target_world_n=net_world,valid=True,normal_load_n=float(total),weighted_contact_local=[float(v) for v in center],weighted_forward_edge_distance_m=float(forward_edge_distance(center,target_quat,size,direction)),min_sample_forward_edge_distance_m=float(min(margins)),contact_count=len(weights))
