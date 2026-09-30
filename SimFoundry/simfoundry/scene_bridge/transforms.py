"""Table-frame → world pose helpers shared by USDA export and Isaac spawners."""

from __future__ import annotations

import math

from simfoundry.schema import Pose, SceneObject, ScenePackage


def quat_mul(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def quat_rotate(q: tuple[float, float, float, float], v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z, w = q
    vx, vy, vz = v
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


def world_pose(table: Pose, obj: SceneObject) -> Pose:
    pos = quat_rotate(table.rot_xyzw, obj.pos)
    return Pose(
        pos=(table.pos[0] + pos[0], table.pos[1] + pos[1], table.pos[2] + pos[2]),
        rot_xyzw=quat_mul(table.rot_xyzw, obj.rot_xyzw),
    )


def object_extents(obj: SceneObject) -> tuple[float, float, float]:
    if obj.shape == "cuboid":
        assert obj.size is not None
        return obj.size
    assert obj.radius is not None and obj.height is not None
    return (obj.radius * 2.0, obj.radius * 2.0, obj.height)


def almost_identity(q: tuple[float, float, float, float], eps: float = 1e-6) -> bool:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(q, (0.0, 0.0, 0.0, 1.0), strict=True))) < eps


def iter_world_objects(package: ScenePackage) -> list[tuple[SceneObject, Pose]]:
    return [(obj, world_pose(package.table_frame, obj)) for obj in package.objects]
