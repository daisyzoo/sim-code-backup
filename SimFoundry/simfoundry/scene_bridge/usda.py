"""Write a USDA stage from a scene package. No Isaac / pxr required."""

from __future__ import annotations

from pathlib import Path

from simfoundry.scene_bridge.transforms import iter_world_objects
from simfoundry.schema import SceneObject, ScenePackage


def _fmt_vec3(v: tuple[float, float, float]) -> str:
    return f"({v[0]:.6f}, {v[1]:.6f}, {v[2]:.6f})"


def _fmt_quat(q: tuple[float, float, float, float]) -> str:
    x, y, z, w = q
    return f"({x:.6f}, {y:.6f}, {z:.6f}, {w:.6f})"


def _geom_block(obj: SceneObject) -> str:
    if obj.shape == "cuboid":
        assert obj.size is not None
        sx, sy, sz = obj.size
        return "\n".join(
            [
                '    def Cube "Geom"',
                "    {",
                f"        float3 xformOp:scale = {_fmt_vec3((sx * 0.5, sy * 0.5, sz * 0.5))}",
                '        uniform token[] xformOpOrder = ["xformOp:scale"]',
                "    }",
            ]
        )
    if obj.shape == "usd":
        # USDA export stays lightweight: approximate bbox cylinder + asset path note.
        r = obj.radius if obj.radius is not None else 0.05
        h = obj.height if obj.height is not None else 0.1
        return "\n".join(
            [
                '    def Cylinder "Geom"',
                "    {",
                f"        double radius = {r:.6f}",
                f"        double height = {h:.6f}",
                '        uniform token axis = "Z"',
                f'        string simfoundry:usdPath = "{obj.usd_path}"',
                "    }",
            ]
        )
    assert obj.radius is not None and obj.height is not None
    return "\n".join(
        [
            '    def Cylinder "Geom"',
            "    {",
            f"        double radius = {obj.radius:.6f}",
            f"        double height = {obj.height:.6f}",
            '        uniform token axis = "Z"',
            "    }",
        ]
    )


def package_to_usda(package: ScenePackage) -> str:
    lines = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "World"',
        "    metersPerUnit = 1",
        '    upAxis = "Z"',
        '    doc = "SimFoundry scene_bridge export. Source of truth remains twin/layout.json."',
        ")",
        "",
        "def Xform \"World\" (",
        f'    doc = "scene_id={package.scene_id} source={package.meta.source}"',
        ")",
        "{",
    ]
    for obj, pose in iter_world_objects(package):
        kinematic = "true" if obj.kinematic else "false"
        lines.extend(
            [
                f'  def Xform "{obj.name}" (',
                '    prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsCollisionAPI", "PhysicsMassAPI"]',
                "  )",
                "  {",
                f"    quatf xformOp:orient = {_fmt_quat(pose.rot_xyzw)}",
                f"    double3 xformOp:translate = {_fmt_vec3(pose.pos)}",
                '    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient"]',
                f"    bool physics:kinematicEnabled = {kinematic}",
                "    bool physics:collisionEnabled = true",
                f"    float physics:mass = {obj.mass:.4f}",
                f"    color3f primvars:displayColor = {_fmt_vec3(obj.color)}",
                _geom_block(obj),
                "  }",
                "",
            ]
        )
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def export_usda(package: ScenePackage, dest: str | Path | None = None) -> Path:
    dest = Path(dest) if dest is not None else Path(package.root) / "twin" / "scene.usda"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(package_to_usda(package))
    return dest
