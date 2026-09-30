"""Sorting-station geometry aligned to official G1-23 URDF + picktask-sim.

Method:
  - Table front edge from layout.json (TABLE 0.60 m along X).
  - D435i install matches unitree ``d435_joint`` (xyz + pitch≈47.6°), Isaac ROS optical.
  - Pelvis standing height matches picktask-sim / real G1 (z=0.793).
  - Robot yaw = 0 → faces +X toward the table (near edge at x = TABLE_FRONT_X).
  - Only tune standoff / scene props; do not retune camera relative to torso.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np

# layout.json table_frame + table.size[0]
TABLE_FRAME_X = 0.58
TABLE_HALF_X = 0.30
TABLE_TOP_Z = 0.75
TABLE_FRONT_X = TABLE_FRAME_X - TABLE_HALF_X  # 0.28 — robot-side table edge

PARCEL_BOX_SIZE = (0.14, 0.09, 0.045)
MAILER_SIZE_XYH = (0.15, 0.145, 0.040)
# Start in resting contact, not 2 mm above the table.  The old micro-drop
# injected lateral Newton solver velocity before every demonstration.
TABLE_TOP_BOX_Z = TABLE_TOP_Z + PARCEL_BOX_SIZE[2] / 2
TABLE_TOP_MAILER_Z = TABLE_TOP_Z + MAILER_SIZE_XYH[2] / 2

# Dual-parcel legacy rests (physics).
SORTING_BOX_REST = (0.30, -0.16, TABLE_TOP_BOX_Z)
SORTING_MAILER_REST = (0.31, 0.16, TABLE_TOP_MAILER_Z)

# Single-parcel sorting must begin near the conveyor/table centreline.  Giving
# box and mailer opposite signed Y starts leaks the answer into the image and
# lets a policy associate class with initial position instead of material.
# The Cartesian expert approaches across the centreline from the active side.
# Spawn slightly table-inward so the short Newton contact-settle transient
# lands near the evaluation centre x=0.40 without risking front-edge overhang.
SORTING_BOX_REST_SINGLE = (0.46, 0.0, TABLE_TOP_BOX_Z)
SORTING_MAILER_REST_SINGLE = (0.46, 0.0, TABLE_TOP_MAILER_Z)

_DECORATIVE_PARCELS: tuple[str, ...] = (
    "parcel_box_b",
    "mailer_b",
    "mailer_c",
    "mailer_d",
)
_PARCEL_LABELS: tuple[str, ...] = (
    "parcel_box_label",
    "parcel_box_b_label",
    "mailer_label",
    "mailer_b_label",
    "mailer_c_label",
    "mailer_d_label",
)

# Move hidden parcels off-camera (set_visibility alone is unreliable under RTX).
_OFFTABLE_XYZ = (5.0, 5.0, 3.0)

# The earlier 0.30 m standoff was compensating for a detached 0.16 m palm
# collision proxy. With the proxy aligned to the visible rubber hand, move the
# fixed-base robot 10 cm closer so the rendered hand and collision core reach
# the same tabletop workspace.
SORTING_ROBOT_STANDOFF_M = 0.20
# Standing pelvis height: picktask-sim DEFAULT_ROBOT_POSITION[2] / real G1.
SORTING_ROBOT_POS = (TABLE_FRONT_X - SORTING_ROBOT_STANDOFF_M, 0.0, 0.793)
SORTING_ROBOT_ROT_XYZW = (0.0, 0.0, 0.0, 1.0)

# Official URDF d435_joint on torso_link (g1_23dof_mode_10 / rev_1_0 / u1_black).
# Position: xyz from URDF. Rotation: URDF Ry(0.8307767) ∘ ROS optical (Rz(-90)∘Rx(-90)),
# Isaac Lab CameraCfg convention="ros" (looks along +Z). Pitch ≈ 47.6° down.
SORTING_D435I_POS = (0.0576235, 0.01753, 0.42987)
SORTING_D435I_ROT_XYZW = (-0.659252, 0.659252, -0.255707, 0.255707)

_SIMFOUNDRY = Path(__file__).resolve().parents[2]
SORTING_HDR_TEXTURE = (
    _SIMFOUNDRY / "assets" / "textures" / "sorting_station" / "sorting_lab.hdr"
)

ParcelKind = Literal["parcel_box", "mailer"]

_PHOTOS_ATTR = "_sorting_parcel_photos"
_PHOTO_LOOK = {
    "parcel_box": {"roughness": 0.86, "metallic": 0.0, "fallback_color": (0.78, 0.62, 0.40)},
    "mailer": {"roughness": 0.22, "metallic": 0.04, "fallback_color": (0.04, 0.04, 0.045)},
}


def _prim_paths_for(env, name: str) -> list[str]:
    try:
        asset = env.scene[name]
    except (KeyError, AttributeError):
        return []
    prims = getattr(asset, "_prims", None)
    if prims:
        return [p.GetPath().pathString for p in prims]
    try:
        import isaaclab.sim as sim_utils
    except ImportError:
        return [f"/World/envs/env_{i}/{name}" for i in range(getattr(env, "num_envs", 1))]
    cfg_path = getattr(getattr(asset, "cfg", None), "prim_path", None)
    if not cfg_path:
        return [f"/World/envs/env_{i}/{name}" for i in range(getattr(env, "num_envs", 1))]
    return [p.GetPath().pathString for p in sim_utils.find_matching_prims(cfg_path)]


def _apply_parcel_albedos(env, chosen: dict[str, Path], *, active: ParcelKind | None) -> None:
    if active == "parcel_box":
        names = ("parcel_box",)
    elif active == "mailer":
        names = ("mailer",)
    else:
        names = ("parcel_box", "mailer")
    try:
        from simfoundry.scene_bridge.textures import set_diffuse_texture_file
    except ImportError:
        return
    for name in names:
        image = chosen.get(name)
        if image is None or not image.is_file():
            continue
        look = _PHOTO_LOOK[name]
        for prim_path in _prim_paths_for(env, name):
            set_diffuse_texture_file(prim_path, image, **look)


def _randomize_parcel_photos(
    env,
    rng: np.random.Generator | None,
    *,
    active: ParcelKind | None,
) -> None:
    """One box photo from 4, one bag photo from 5. Reuse within an episode when rng is omitted."""
    from simfoundry.scene_bridge.parcel_photos import choose_parcel_albedos

    stored = getattr(env, _PHOTOS_ATTR, None)
    if rng is not None or not stored:
        stored = choose_parcel_albedos(rng if rng is not None else np.random.default_rng())
        setattr(env, _PHOTOS_ATTR, stored)
    if stored:
        _apply_parcel_albedos(env, stored, active=active)


def _set_visible(env, name: str, visible: bool) -> None:
    try:
        asset = env.scene[name]
    except (KeyError, AttributeError):
        return
    if hasattr(asset, "set_visibility"):
        try:
            asset.set_visibility(bool(visible))
        except Exception:
            pass


def _write_pose(env, name: str, xyz: tuple[float, float, float]) -> None:
    import torch

    try:
        asset = env.scene[name]
    except (KeyError, AttributeError):
        return
    if not hasattr(asset, "write_root_pose_to_sim_index"):
        return
    pose = torch.tensor(
        [[xyz[0], xyz[1], xyz[2], 0.0, 0.0, 0.0, 1.0]],
        dtype=torch.float32,
        device=env.device,
    )
    asset.write_root_pose_to_sim_index(root_pose=pose)
    zero_vel = torch.zeros((env.num_envs, 6), dtype=torch.float32, device=env.device)
    if hasattr(asset, "write_root_velocity_to_sim_index"):
        asset.write_root_velocity_to_sim_index(root_velocity=zero_vel)
    elif hasattr(asset, "write_root_com_velocity_to_sim_index"):
        asset.write_root_com_velocity_to_sim_index(root_velocity=zero_vel)


def _jitter_xy(
    base: tuple[float, float, float],
    rng: np.random.Generator | None,
    *,
    x_span: float = 0.015,
    y_span: float = 0.012,
) -> tuple[float, float, float]:
    if rng is None:
        return base
    return (
        float(base[0] + rng.uniform(-x_span, x_span)),
        float(base[1] + rng.uniform(-y_span, y_span)),
        float(base[2]),
    )


def active_parcel_for_task(task_id: str | None) -> ParcelKind | None:
    if task_id == "push_box_to_bin":
        return "parcel_box"
    if task_id == "nudge_mailer_to_bin":
        return "mailer"
    return None


def reset_sorting_parcels(
    env,
    *,
    task_id: str | None = None,
    single_parcel: bool = True,
    rng: np.random.Generator | None = None,
    box_xyz: tuple[float, float, float] | None = None,
    mailer_xyz: tuple[float, float, float] | None = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Place parcels. ``single_parcel`` keeps only the active package visible on the table."""
    from simfoundry.scene_bridge.labels import sync_shipping_labels

    empty_table = task_id == "wait_no_package"
    active = None if empty_table else (active_parcel_for_task(task_id) if single_parcel else None)

    if box_xyz is None or mailer_xyz is None:
        if empty_table:
            box_xyz = box_xyz or _OFFTABLE_XYZ
            mailer_xyz = mailer_xyz or _OFFTABLE_XYZ
        elif active == "parcel_box":
            box_xyz = box_xyz or _jitter_xy(SORTING_BOX_REST_SINGLE, rng)
            mailer_xyz = mailer_xyz or _OFFTABLE_XYZ
        elif active == "mailer":
            box_xyz = box_xyz or _OFFTABLE_XYZ
            mailer_xyz = mailer_xyz or _jitter_xy(SORTING_MAILER_REST_SINGLE, rng)
        else:
            box_xyz = box_xyz or SORTING_BOX_REST
            mailer_xyz = mailer_xyz or SORTING_MAILER_REST

    _write_pose(env, "parcel_box", box_xyz)
    _write_pose(env, "mailer", mailer_xyz)

    if empty_table or single_parcel:
        for name in _DECORATIVE_PARCELS:
            _set_visible(env, name, False)
            _write_pose(env, name, _OFFTABLE_XYZ)
        if empty_table:
            _set_visible(env, "parcel_box", False)
            _set_visible(env, "mailer", False)
            _write_pose(env, "parcel_box", _OFFTABLE_XYZ)
            _write_pose(env, "mailer", _OFFTABLE_XYZ)
        elif active == "parcel_box":
            _set_visible(env, "parcel_box", True)
            _set_visible(env, "mailer", False)
            _write_pose(env, "mailer", _OFFTABLE_XYZ)
        elif active == "mailer":
            _set_visible(env, "mailer", True)
            _set_visible(env, "parcel_box", False)
            _write_pose(env, "parcel_box", _OFFTABLE_XYZ)
    else:
        for name in ("parcel_box", "mailer", *_DECORATIVE_PARCELS):
            _set_visible(env, name, True)

    # Photo textures already include waybills; keep sticker cuboids off-camera.
    for name in _PARCEL_LABELS:
        _set_visible(env, name, False)
        _write_pose(env, name, _OFFTABLE_XYZ)

    _randomize_parcel_photos(env, rng, active=active)
    sync_shipping_labels(env)
    return box_xyz, mailer_xyz
