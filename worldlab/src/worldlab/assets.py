"""CPU-only asset auditing and reproducible USD construction."""
from pathlib import Path
import hashlib
import importlib.metadata
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def load_config(path=None):
    path = Path(path) if path else ROOT / "configs/kitchen.json"
    return json.loads(path.read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def validate_splats(data):
    """Accept infinite opacity logits, but reject invalid geometry/NaNs."""
    for name in ("positions", "scales", "rotations", "f_dc"):
        if not np.isfinite(getattr(data, name)).all():
            raise ValueError(f"Non-finite {name}")
    if data.f_rest is not None and not np.isfinite(data.f_rest).all():
        raise ValueError("Non-finite higher-order SH")
    if np.isnan(data.opacities).any():
        raise ValueError("NaN opacity")
    if np.any(np.linalg.norm(data.rotations, axis=1) < 1e-8):
        raise ValueError("Zero quaternion")
    if np.any(data.scales > 80):
        raise ValueError("Unrepresentable Gaussian scale")
    # The converter applies sigmoid, so +/-inf map exactly to 1/0. Clamp only
    # the very negative tail to prevent math.exp overflow in its implementation.
    negative_tail = data.opacities < -700
    stats = {
        "count": data.count,
        "opacity_positive_inf": int(np.isposinf(data.opacities).sum()),
        "opacity_negative_inf": int(np.isneginf(data.opacities).sum()),
        "clamped_negative_opacity_logits": int(negative_tail.sum()),
        "higher_order_sh": data.f_rest is not None,
        "bounds": [data.positions.min(0).tolist(), data.positions.max(0).tolist()],
        "position_percentiles_1_50_99": np.percentile(data.positions, [1, 50, 99], axis=0).tolist(),
    }
    if negative_tail.any():
        data.opacities = np.maximum(data.opacities, -700)
    return stats


def load_mesh(path):
    import trimesh
    scene = trimesh.load(path, force="scene", process=False)
    mesh = scene.to_mesh()  # Bake glTF node transforms, not just raw accessors.
    if not len(mesh.faces) or not np.isfinite(mesh.vertices).all():
        raise ValueError("Empty or non-finite collider")
    if mesh.faces.min() < 0 or mesh.faces.max() >= len(mesh.vertices):
        raise ValueError("Invalid triangle indices")
    return mesh


def convert_collider(mesh, output):
    from pxr import Usd, UsdGeom, Vt
    stage = Usd.Stage.CreateNew(str(output))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1)
    root = UsdGeom.Xform.Define(stage, "/Collider")
    stage.SetDefaultPrim(root.GetPrim())
    geom = UsdGeom.Mesh.Define(stage, "/Collider/Mesh")
    geom.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(np.asarray(mesh.vertices, dtype=np.float32)))
    geom.CreateFaceVertexCountsAttr(Vt.IntArray.FromNumpy(np.full(len(mesh.faces), 3, dtype=np.int32)))
    geom.CreateFaceVertexIndicesAttr(Vt.IntArray.FromNumpy(np.asarray(mesh.faces, dtype=np.int32).ravel()))
    geom.CreateSubdivisionSchemeAttr("none")
    geom.CreateDoubleSidedAttr(True)
    geom.CreateExtentAttr(Vt.Vec3fArray.FromNumpy(np.asarray(mesh.bounds, dtype=np.float32)))
    if hasattr(mesh.visual, "vertex_colors"):
        colors = np.asarray(mesh.visual.vertex_colors[:, :3], dtype=np.float32) / 255
        geom.CreateDisplayColorPrimvar(UsdGeom.Tokens.vertex).Set(Vt.Vec3fArray.FromNumpy(colors))
    stage.GetRootLayer().Save()


def look_at(camera, eye, target):
    from pxr import Gf, UsdGeom
    matrix = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(0, 0, 1)).GetInverse()
    xform = UsdGeom.Xformable(camera)
    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(matrix)


def assemble(cfg, output):
    from pxr import Gf, Usd, UsdGeom, UsdLux, UsdPhysics
    stage = Usd.Stage.CreateNew(str(output / "kitchen.usda"))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    stage.SetTimeCodesPerSecond(60)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(36000)
    env = UsdGeom.Xform.Define(stage, "/World/Kitchen")
    t = cfg["source_to_world"]
    env.AddTranslateOp().Set(Gf.Vec3d(*t["translate"]))
    env.AddRotateXYZOp().Set(Gf.Vec3f(*t["rotate_xyz_deg"]))
    env.AddScaleOp().Set(Gf.Vec3f(t["scale"]))
    # USD composition does not automatically rotate referenced layers' up-axis.
    # Both assets keep their original coordinates and share the SAME parent.
    visual = stage.DefinePrim("/World/Kitchen/Visual")
    visual.GetReferences().AddReference("./visual.usdc")
    collider = stage.DefinePrim("/World/Kitchen/Collision")
    collider.GetReferences().AddReference("./collision.usdc")
    UsdGeom.Imageable(collider).CreateVisibilityAttr().Set("invisible")
    for prim in Usd.PrimRange(collider):
        if prim.IsA(UsdGeom.Mesh):
            UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
            # A whole-room convex hull would fill the walkable interior.
            UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("none")
    physics = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    physics.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    physics.CreateGravityMagnitudeAttr(9.81)
    light = UsdLux.DomeLight.Define(stage, "/World/Lighting/Dome")
    light.CreateIntensityAttr(300)
    sun = UsdLux.DistantLight.Define(stage, "/World/Lighting/Sun")
    sun.CreateIntensityAttr(500)
    UsdGeom.Xformable(sun).AddRotateXYZOp().Set(Gf.Vec3f(-45, 20, 0))
    for name, settings in cfg["cameras"].items():
        cam = UsdGeom.Camera.Define(stage, f"/World/Cameras/{name}")
        cam.CreateFocalLengthAttr(18)
        cam.CreateHorizontalApertureAttr(36)
        cam.CreateVerticalApertureAttr(20.25)
        cam.CreateClippingRangeAttr(Gf.Vec2f(0.05, 100))
        look_at(cam, settings["eye"], settings["target"])
    stage.GetRootLayer().customLayerData = {"worldlab_config": json.dumps(cfg), "scale_status": cfg["scale_status"]}
    stage.GetRootLayer().Save()


def build(cfg, force=False):
    from usd_convert_gsplat import read_ply, write_gaussian_splat_usd
    output = ROOT / cfg["output"]
    output.mkdir(parents=True, exist_ok=True)
    splat, collider = ROOT / cfg["splat"], ROOT / cfg["collider"]
    hashes = {"splat": digest(splat), "collider": digest(collider)}
    converter_version = importlib.metadata.version("usd-convert-gsplat")
    usd_version = importlib.metadata.version("usd-core")
    assets = ("visual.usdc", "collision.usdc")
    previous = output / "manifest.json"
    if not force and previous.exists():
        old = json.loads(previous.read_text())
        cache_valid = (old.get("source_sha256") == hashes
                       and old.get("converter_version") == converter_version
                       and old.get("usd_core_version") == usd_version
                       and all((output / x).exists() and digest(output / x) == old.get("output_sha256", {}).get(x)
                               for x in assets))
        if cache_valid:
            assemble(cfg, output)
            if (old["config"] != cfg
                    or old.get("scene_sha256") != digest(output / "kitchen.usda")):
                old["runtime_validated"] = False
            old["config"] = cfg
            old["scene_sha256"] = digest(output / "kitchen.usda")
            save_json(previous, old)
            return old
    # An interrupted rebuild must not leave an old success manifest validating
    # partially overwritten assets. Original PLY/GLB remain untouched.
    previous.unlink(missing_ok=True)
    data = read_ply(str(splat))
    audit = validate_splats(data)
    mesh = load_mesh(collider)
    audit["collider"] = {"vertices": len(mesh.vertices), "triangles": len(mesh.faces), "bounds": mesh.bounds.tolist()}
    save_json(output / "asset_audit.json", audit)
    print("Converting full-resolution Gaussian field", flush=True)
    write_gaussian_splat_usd(data, str(output / "visual.usdc"), source_file=cfg["splat"], prim_name="Visual", up_axis="Y")
    convert_collider(mesh, output / "collision.usdc")
    assemble(cfg, output)
    manifest = {"source_sha256": hashes, "config": cfg, "audit": audit,
                "converter_version": converter_version, "usd_core_version": usd_version,
                "output_sha256": {x: digest(output / x) for x in assets},
                "scene_sha256": digest(output / "kitchen.usda"),
                "runtime_validated": False}
    save_json(previous, manifest)
    return manifest
