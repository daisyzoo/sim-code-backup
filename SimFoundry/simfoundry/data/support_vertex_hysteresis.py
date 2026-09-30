"""Diagnostic near-support vertex selection with explicit bounded height error.

Returns a real hull vertex, never an averaged point or physical modification.
The selected point may be above the true supporting plane by the stated bound;
this is not a proof that a parcel lies under the entire hand footprint.
"""
import math
from simfoundry.data.top_contact_bypass import rotation_xyzw, support_mesh


def support_vertex_with_hysteresis(side, hand_quat, parcel_quat, previous=None, max_excess_m=.0002):
    if not math.isfinite(max_excess_m) or not 0<=max_excess_m<=.0005:
        raise ValueError('Support-plane tolerance must be finite in [0,0.0005]m')
    vertices=support_mesh()[side]
    if previous is not None and tuple(previous) not in vertices:
        raise ValueError('Previous support point must be a real mesh vertex')
    rh=rotation_xyzw(hand_quat);rp=rotation_xyzw(parcel_quat)
    normal=tuple(sum(rh[i][k]*rp[i][2] for i in range(3)) for k in range(3))
    heights=[sum(v*n for v,n in zip(vertex,normal)) for vertex in vertices]
    index=min(range(len(vertices)),key=heights.__getitem__);minimum=heights[index]
    if previous is not None and max_excess_m>0:
        previous=tuple(previous);old_index=vertices.index(previous)
        if heights[old_index]-minimum<=max_excess_m:index=old_index
        else:
            candidates=[i for i,h in enumerate(heights) if h-minimum<=max_excess_m*.25]
            index=min(candidates,key=lambda i:sum((a-b)**2 for a,b in zip(vertices[i],previous)))
    point=vertices[index]
    return point,dict(support_plane_excess_m=heights[index]-minimum,max_support_plane_excess_m=max_excess_m,vertex_changed=previous is not None and tuple(previous)!=point,selector='retain actual mesh vertex within bounded support-plane height; otherwise nearest near-minimum vertex')
