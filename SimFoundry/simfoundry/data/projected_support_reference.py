"""Continuous virtual reference on the real hand supporting plane.

Tangential position defaults to the fixed hand-hull bounding-box center; an explicit calibrated hand-local center may replace it. Normal height
is the exact lowest hull height. This point need not belong to the mesh or hull;
it is NOT a physical contact point. Actual lowest vertices must separately fit
the target face. The Jacobian accounts for the orientation-dependent offset.
"""
import numpy as np


def skew(v):
    x,y,z=v
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def projected_support_reference(vertices, hand_rotation, world_normal, *, center_local=None):
    vertices=np.asarray(vertices,dtype=float);r=np.asarray(hand_rotation,dtype=float)
    n=np.asarray(world_normal,dtype=float)
    if vertices.ndim!=2 or vertices.shape[1]!=3 or len(vertices)<4 or r.shape!=(3,3) or n.shape!=(3,):
        raise ValueError('Invalid supporting geometry dimensions')
    if not all(np.isfinite(x).all() for x in (vertices,r,n)) or abs(np.linalg.norm(n)-1)>1e-6 or not np.allclose(r.T@r,np.eye(3),atol=1e-6) or np.linalg.det(r)<.99999:
        raise ValueError('Invalid supporting geometry orientation')
    center=(vertices.min(axis=0)+vertices.max(axis=0))/2 if center_local is None else np.asarray(center_local,dtype=float)
    if center.shape!=(3,) or not np.isfinite(center).all() or np.any(center<vertices.min(0)-.003) or np.any(center>vertices.max(0)+.003):
        raise ValueError('Invalid measured tangential center')
    local_normal=r.T@n
    h=vertices@local_normal;index=int(h.argmin());v=vertices[index]
    offset=center+local_normal*((v-center)@local_normal)
    return dict(reference_local=offset,center_local=center,lowest_vertex_local=v,
                support_index=index,support_height_local=float(h[index]),world_normal=n)


def projected_support_jacobian(origin_linear_jacobian, angular_jacobian, hand_rotation, reference):
    r=np.asarray(hand_rotation);jl=np.asarray(origin_linear_jacobian);jw=np.asarray(angular_jacobian)
    if jl.shape!=jw.shape or jl.ndim!=2 or jl.shape[0]!=3:raise ValueError('Invalid Jacobian shapes')
    n=reference['world_normal'];normal=np.outer(n,n)
    jc=jl-skew(r@reference['center_local'])@jw
    jv=jl-skew(r@reference['lowest_vertex_local'])@jw
    return (np.eye(3)-normal)@jc+normal@jv
