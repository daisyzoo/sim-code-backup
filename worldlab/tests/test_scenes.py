from pathlib import Path
import sys
import math
import json
import pytest
from pxr import Usd,UsdGeom,UsdPhysics,UsdShade,Sdf
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from worldlab.scenes import load_scene,resolve_scene
from worldlab.scene_tour import tour_pose


@pytest.mark.parametrize('scene',['hallway1_elegant','hallway1_modern','hallway2','hallway2_blend'])
def test_scene_dependencies_units_static_colliders_and_closed_tour(scene):
    cfg,path,manifest=resolve_scene(scene)
    stage=Usd.Stage.Open(str(path))
    assert str(UsdGeom.GetStageUpAxis(stage))=='Z'
    assert UsdGeom.GetStageMetersPerUnit(stage)==1
    assert stage.GetEndTimeCode()>stage.GetStartTimeCode()
    assert stage.GetPrimAtPath('/World/Environment')
    assert len(manifest['collision_paths'])>=1
    for path in manifest['collision_paths']:
        prim=stage.GetPrimAtPath(path)
        assert prim.IsA(UsdGeom.Mesh)
        assert UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get()
        assert UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()=='none'
        assert not prim.HasAPI(UsdPhysics.RigidBodyAPI)
    route=cfg['tour'];a=tour_pose(route,0);b=tour_pose(route,1)
    assert math.dist(a[0],b[0])<1e-8 and math.dist(a[1],b[1])<1e-8
    for i in range(101):
        eye,target=tour_pose(route,i/100)
        assert all(math.isfinite(x) for x in eye+target)
        assert abs(math.dist(eye,target)-1)<1e-8


def test_mesh_import_preserves_components_materials_and_textures():
    cfg,path,manifest=resolve_scene('hallway2');stage=Usd.Stage.Open(str(path))
    assert sum(p.IsA(UsdGeom.Mesh) for p in stage.Traverse())==272
    assert sum(p.IsA(UsdShade.Material) for p in stage.Traverse())==15
    assert sum(p.IsA(UsdGeom.Camera) for p in stage.Traverse())==7 # 4 source + 3 acceptance cameras
    textures=[]
    for prim in stage.Traverse():
        for attr in prim.GetAttributes():
            if attr.GetTypeName()==Sdf.ValueTypeNames.Asset:
                value=attr.Get()
                if value and value.path.lower().endswith(('.png','.jpg','.jpeg')):
                    assert value.resolvedPath and Path(value.resolvedPath).is_file()
                    textures.append(value.resolvedPath)
    assert textures
    # A particular tread must be below the corridor and extend along X, not stand vertically.
    tread=stage.GetPrimAtPath('/World/Environment/Visual/Straight_stair_tread_4/Cube_066')
    bounds=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render']).ComputeWorldBound(tread).ComputeAlignedRange()
    assert abs(bounds.GetMax()[2]+.72)<.01
    assert bounds.GetMax()[1]-bounds.GetMin()[1]>.9


def test_unknown_scene_is_rejected():
    with pytest.raises(ValueError):load_scene('../../Kitchen')


def test_direct_blend_keeps_native_axis_materials_lights_and_orthographic_camera():
    from pxr import UsdLux
    cfg,path,manifest=resolve_scene('hallway2_blend')
    assert cfg['sources']=={'visual':'World/Environment/hallway2/hallway.blend'}
    assert cfg['source_to_world']['rotate_xyz_deg']==[0,0,0]
    stage=Usd.Stage.Open(str(path))
    visual=stage.GetPrimAtPath('/World/Environment/Visual')
    source_prims=list(Usd.PrimRange(visual))
    assert sum(p.IsA(UsdGeom.Mesh) for p in source_prims)==272
    assert sum(p.IsA(UsdShade.Material) for p in source_prims)==15
    assert sum(p.HasAPI(UsdLux.LightAPI) for p in source_prims)==7
    cameras=[UsdGeom.Camera(p) for p in source_prims if p.IsA(UsdGeom.Camera)]
    assert len(cameras)==4
    assert sum(c.GetProjectionAttr().Get()=='orthographic' for c in cameras)==1
    textures=set()
    for p in source_prims:
        if p.IsA(UsdGeom.Mesh):
            assert UsdShade.MaterialBindingAPI(p).ComputeBoundMaterial()[0]
        for attr in p.GetAttributes():
            if attr.GetTypeName()==Sdf.ValueTypeNames.Asset and attr.Get():
                value=attr.Get()
                assert not Path(value.path).is_absolute()
                assert value.resolvedPath and Path(value.resolvedPath).is_file()
                textures.add(value.resolvedPath)
    assert len(textures)==7 # Original wood + six used floor tones.
    cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render'])
    tread=stage.GetPrimAtPath('/World/Environment/Visual/Straight_stair_tread_4/Cube_066')
    bound=cache.ComputeWorldBound(tread).ComputeAlignedRange()
    assert abs(bound.GetMax()[2]+.72)<.01
    assert bound.GetMax()[1]-bound.GetMin()[1]>.9
