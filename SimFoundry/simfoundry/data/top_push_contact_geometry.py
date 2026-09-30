"""Direction-aware contact geometry for the unchanged parcel collision core."""
import math
from simfoundry.data.top_contact_bypass import rotation_xyzw,top_corner_local


def top_trailing_corner_local(quat,size,direction,inset=.01):
    """Closest major front face, trailing corner along commanded world Y.

    Latch the returned local coordinate for a contact cycle. This avoids choosing
    the leading corner just because it is marginally closer in world X. It does
    not prove dynamic stability, hand-footprint overlap, or IK feasibility.
    """
    if direction not in (-1,1):raise ValueError('World Y direction must be -1 or 1')
    top_corner_local(quat,size,inset) # Same strict size/inset/quaternion checks.
    r=rotation_xyzw(quat);front=max((0,1),key=lambda i:abs(r[0][i]));other=1-front
    local=[0.,0.,size[2]/2]
    local[front]=(-1 if r[0][front]>=0 else 1)*(size[front]/2-inset)
    local[other]=(-1 if direction*r[1][other]>=0 else 1)*(size[other]/2-inset)
    return tuple(local)


def forward_edge_distance(local_point,quat,size,direction):
    """Distance along projected commanded world Y until an XY core edge.

    Signed: negative means already beyond a forward edge. For diagnosis; tilted
    parcel poses need full dynamics and are not certified by this 2-D distance.
    """
    if direction not in (-1,1) or len(local_point)!=3 or len(size)!=3 or not all(math.isfinite(v) for v in [*local_point,*size]) or min(size)<=0:raise ValueError('Invalid directional margin geometry')
    r=rotation_xyzw(quat);components=[direction*r[1][i] for i in (0,1)]
    bounds=[(size[i]/2-(1 if d>0 else -1)*local_point[i])/abs(d) for i,d in enumerate(components) if abs(d)>1e-8]
    if not bounds:raise ValueError('World Y has no projection on parcel XY')
    return min(bounds)


def top_front_contact_local(quat,size,direction,forward_margin_m=.025,edge_inset_m=.01):
    """Minimize world X subject to true XY edge and forward travel margins."""
    if direction not in (-1,1) or not math.isfinite(forward_margin_m) or forward_margin_m<=0:raise ValueError('Invalid forward contact margin')
    top_corner_local(quat,size,edge_inset_m)
    r=rotation_xyzw(quat);local=[]
    for i in (0,1):
        half=size[i]/2;advance=direction*r[1][i]*forward_margin_m
        low=max(-half+edge_inset_m,-half-min(advance,0.))
        high=min(half-edge_inset_m,half-max(advance,0.))
        if low>high:raise ValueError('No contact point satisfies requested margins')
        local.append(low if r[0][i]>=0 else high)
    return (*local,size[2]/2)


def shift_top_contact_rearward(local,quat,size,direction,forward_margin_m,requested_shift_m,edge_inset_m=.01):
    """Move a latched top point along projected +worldX, within its same margins.

    Requested shift is capped to available rectangle travel; actual worldX
    displacement is no greater than requested. This is contact geometry only.
    """
    if not math.isfinite(requested_shift_m) or not 0<=requested_shift_m<=.03:raise ValueError('Rear contact shift must be0..30mm')
    top_front_contact_local(quat,size,direction,forward_margin_m,edge_inset_m)
    if len(local)!=3 or not all(math.isfinite(v) for v in local) or abs(local[2]-size[2]/2)>1e-8:raise ValueError('Invalid initial top point')
    r=rotation_xyzw(quat);amount=requested_shift_m
    for i in (0,1):
        half=size[i]/2;advance=direction*r[1][i]*forward_margin_m
        low=max(-half+edge_inset_m,-half-min(advance,0.));high=min(half-edge_inset_m,half-max(advance,0.))
        if not low-1e-8<=local[i]<=high+1e-8:raise ValueError('Initial point violates contact margins')
        vector=r[0][i]
        if abs(vector)>1e-12:amount=min(amount,max(0.,((high if vector>0 else low)-local[i])/vector))
    return (local[0]+amount*r[0][0],local[1]+amount*r[0][1],local[2])
