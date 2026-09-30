#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Rescale canonical meshes so their OBB matches known real-world extents.

Maps the current oriented-bounds axes (shortest / mid / longest) onto the
sorted target lengths, bakes the scale into ``s8_pose/canonical_mesh``, and
records the mapping in ``s8_pose/info``. Stage 11 still applies ``z_up.scale``
on top, so leave that at 1 after this script.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import trimesh


def _as_trimesh(mesh):
    if isinstance(mesh, trimesh.Scene):
        return mesh.to_geometry()
    return mesh


def obb_scale_transform(mesh, target_extents_m: np.ndarray) -> tuple[np.ndarray, dict]:
    geom = _as_trimesh(mesh)
    to_origin, extents = trimesh.bounds.oriented_bounds(geom)
    extents = np.asarray(extents, dtype=float)
    target_sorted = np.sort(np.asarray(target_extents_m, dtype=float))
    order = np.argsort(extents)
    axis_scale = np.ones(3, dtype=float)
    axis_scale[order] = target_sorted / np.maximum(extents[order], 1e-8)
    scale_tf = np.eye(4)
    scale_tf[0, 0], scale_tf[1, 1], scale_tf[2, 2] = axis_scale
    bake = np.linalg.inv(to_origin) @ scale_tf @ to_origin
    meta = {
        "obb_extents_before_m": extents.tolist(),
        "obb_extents_before_cm": (extents * 100.0).tolist(),
        "target_extents_m": np.asarray(target_extents_m, dtype=float).tolist(),
        "obb_axis_scale": axis_scale.tolist(),
        "mapped_axes": {
            "shortest_m": float(extents[order[0]]),
            "mid_m": float(extents[order[1]]),
            "longest_m": float(extents[order[2]]),
        },
    }
    return bake, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-dir", required=True, type=Path)
    parser.add_argument("--indices", required=True, help="Comma-separated iteration indices")
    parser.add_argument(
        "--extents-cm",
        required=True,
        help="Length,width,height in centimetres, e.g. 13,8,2.5",
    )
    args = parser.parse_args()

    indices = [int(x.strip()) for x in args.indices.split(",") if x.strip()]
    target_cm = np.array([float(x) for x in args.extents_cm.split(",")], dtype=float)
    if target_cm.size != 3:
        raise SystemExit("--extents-cm must be three comma-separated numbers")
    target_m = target_cm / 100.0

    mesh_dir = args.scene_dir / "s8_pose" / "canonical_mesh"
    info_dir = args.scene_dir / "s8_pose" / "info"
    backup_dir = mesh_dir / "_backup_pre_known_extents"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for idx in indices:
        glb = mesh_dir / f"iter_{idx}.glb"
        info_path = info_dir / f"iter_{idx}.json"
        if not glb.is_file():
            raise SystemExit(f"missing mesh: {glb}")
        if not info_path.is_file():
            raise SystemExit(f"missing pose info: {info_path}")

        backup_glb = backup_dir / glb.name
        if not backup_glb.exists():
            shutil.copy2(glb, backup_glb)
        backup_info = backup_dir / info_path.name
        if not backup_info.exists():
            shutil.copy2(info_path, backup_info)

        mesh = trimesh.load(str(glb), process=False)
        bake, meta = obb_scale_transform(mesh, target_m)
        mesh.apply_transform(bake)
        mesh.export(str(glb))

        after = trimesh.bounds.oriented_bounds(_as_trimesh(trimesh.load(str(glb), force="mesh")))[1]
        info = json.loads(info_path.read_text(encoding="utf-8"))
        info["known_extents_cm"] = target_cm.tolist()
        info["known_extents_m"] = target_m.tolist()
        info["known_extents_meta"] = meta
        info["obb_extents_after_m"] = np.asarray(after, dtype=float).tolist()
        info["obb_extents_after_cm"] = (np.asarray(after, dtype=float) * 100.0).tolist()
        info_path.write_text(json.dumps(info, indent=4) + "\n", encoding="utf-8")

        before_cm = np.round(np.sort(meta["obb_extents_before_m"]) * 100.0, 2).tolist()
        after_cm = np.round(np.sort(after) * 100.0, 2).tolist()
        print(f"iter_{idx}: {before_cm} cm  ->  {after_cm} cm  (target {np.sort(target_cm).tolist()})")


if __name__ == "__main__":
    main()
