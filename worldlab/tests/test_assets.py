from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import numpy as np
import pytest
from pxr import Usd, UsdGeom, UsdPhysics

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from worldlab.assets import validate_splats


def splats():
    return SimpleNamespace(count=2, positions=np.zeros((2, 3)), scales=np.zeros((2, 3)),
                           rotations=np.array([[1., 0, 0, 0], [1., 0, 0, 0]]),
                           opacities=np.array([np.inf, -np.inf]), f_dc=np.zeros((2, 3)), f_rest=None)


def test_infinite_logits_are_valid_but_invalid_geometry_is_not():
    data = splats()
    result = validate_splats(data)
    assert result["opacity_positive_inf"] == 1
    assert result["opacity_negative_inf"] == 1
    assert data.opacities[1] == -700
    data.positions[0, 0] = np.nan
    with pytest.raises(ValueError, match="positions"):
        validate_splats(data)


def test_zero_quaternion_rejected():
    data = splats()
    data.rotations[0] = 0
    with pytest.raises(ValueError, match="quaternion"):
        validate_splats(data)


def test_generated_stage_is_portable_and_keeps_collider():
    stage = Usd.Stage.Open(str(ROOT / "generated/Kitchen/kitchen.usda"))
    assert stage
    assert UsdGeom.GetStageUpAxis(stage) == "Z"
    field = stage.GetPrimAtPath("/World/Kitchen/Visual")
    assert field.GetTypeName() == "ParticleField3DGaussianSplat"
    assert len(field.GetAttribute("positions").Get()) == 2000000
    opacity = np.asarray(field.GetAttribute("opacities").Get())
    assert np.isfinite(opacity).all() and opacity.min() >= 0 and opacity.max() <= 1
    mesh = stage.GetPrimAtPath("/World/Kitchen/Collision/Mesh")
    assert len(mesh.GetAttribute("faceVertexCounts").Get()) == 114183
    assert mesh.HasAPI(UsdPhysics.CollisionAPI)
    assert UsdPhysics.MeshCollisionAPI(mesh).GetApproximationAttr().Get() == "none"
    assert not mesh.HasAPI(UsdPhysics.RigidBodyAPI)
    assert UsdGeom.Imageable(mesh).ComputeVisibility() == "invisible"
    for layer in stage.GetUsedLayers():
        for ref in layer.GetExternalReferences():
            assert not Path(ref).is_absolute()
    a = UsdGeom.Xformable(field).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    b = UsdGeom.Xformable(mesh).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    assert a == b


def test_relocated_stage_resolves_assets(tmp_path):
    for name in ["kitchen.usda", "visual.usdc", "collision.usdc"]:
        shutil.copyfile(ROOT / "generated/Kitchen" / name, tmp_path / name)
    stage = Usd.Stage.Open(str(tmp_path / "kitchen.usda"))
    assert len(stage.GetPrimAtPath("/World/Kitchen/Visual").GetAttribute("positions").Get()) == 2000000
    assert stage.GetPrimAtPath("/World/Kitchen/Collision/Mesh").HasAPI(UsdPhysics.CollisionAPI)
