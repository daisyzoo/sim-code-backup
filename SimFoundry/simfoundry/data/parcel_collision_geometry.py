"""Read actual USD collision-core bounds; visual shells must not define contact."""
import math

def read_parcel_collision_geometry(stage, root_path, expected_size=None):
    from pxr import Usd,UsdGeom,UsdPhysics
    root=stage.GetPrimAtPath(root_path)
    if not root.IsValid():raise ValueError('Missing parcel root')
    colliders=[p for p in Usd.PrimRange(root) if p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False]
    if len(colliders)!=1:raise ValueError(f'Expected one parcel collision core, found {len(colliders)}')
    collider=colliders[0]
    if collider.GetTypeName()!='Cube':raise ValueError('Top contact currently supports analytic Cube core only')
    cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),[UsdGeom.Tokens.default_,UsdGeom.Tokens.render,UsdGeom.Tokens.proxy],useExtentsHint=False,ignoreVisibility=True)
    bounds=cache.ComputeRelativeBound(collider,root).ComputeAlignedBox();low=tuple(bounds.GetMin());high=tuple(bounds.GetMax())
    size=tuple(float(b-a) for a,b in zip(low,high));center=tuple((a+b)/2 for a,b in zip(low,high))
    if not all(math.isfinite(v) and v>0 for v in size) or max(abs(v) for v in center)>1e-6:raise ValueError('Unsupported offset/invalid collision core')
    if expected_size is not None and (len(expected_size)!=3 or max(abs(a-b) for a,b in zip(size,expected_size))>1e-6):raise ValueError('Spawn config and actual collision core disagree')
    return dict(root_path=str(root_path),collider_path=str(collider.GetPath()),primitive_type=collider.GetTypeName(),collision_core_size_xyz=list(size),core_center_local=list(center),measurement='Enabled USD collision prim relative to rigid body root, ignoring visibility; not visual-shell AABB. Read only.')
