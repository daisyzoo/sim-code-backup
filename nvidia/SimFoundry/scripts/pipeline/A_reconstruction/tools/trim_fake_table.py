#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Cut the Hunyuan support-plane slab off canonical meshes, then convex-hull the rest.

Hunyuan welds a fake table into hat/bottle reconstructions. Stage 8 poses stay valid
because remaining vertices are not translated. Call this on the *unscaled* s8 backup,
then ``apply_known_extents.py`` so OBB scaling no longer includes the slab.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_known_extents import _as_trimesh, obb_scale_transform


def load_mesh(path: Path):
    return trimesh.load(str(path), process=False)


def table_axis_and_height(mesh: trimesh.Trimesh) -> tuple[int, np.ndarray, bool, dict]:
    geom = _as_trimesh(mesh)
    vertices = np.asarray(geom.vertices)
    faces = np.asarray(geom.faces)
    work = geom.copy()
    work.fix_normals()
    normals = work.face_normals
    areas = work.area_faces
    aabb_min = vertices.min(0)
    extents = np.maximum(vertices.max(0) - aabb_min, 1e-9)
    planar_area = [float(areas[np.abs(normals[:, axis]) > 0.85].sum()) for axis in range(3)]
    axis = int(np.argmax(planar_area))
    height = (vertices[:, axis] - aabb_min[axis]) / extents[axis]
    face_height = (vertices[faces].mean(1)[:, axis] - aabb_min[axis]) / extents[axis]
    low = (face_height < 0.15) & (np.abs(normals[:, axis]) > 0.85)
    high = (face_height > 0.85) & (np.abs(normals[:, axis]) > 0.85)
    table_at_low = float(areas[low].sum()) >= float(areas[high].sum())
    t_from_table = height if table_at_low else 1.0 - height
    meta = {
        "table_axis": "xyz"[axis],
        "table_at_low": table_at_low,
        "planar_area_by_axis": planar_area,
        "aabb_cm": (extents * 100.0).tolist(),
    }
    return axis, t_from_table, table_at_low, meta


def adaptive_t_cut(t_from_table: np.ndarray, vertices: np.ndarray, axis: int) -> float:
    others = [i for i in range(3) if i != axis]
    core = t_from_table > 0.40
    if int(core.sum()) < 80:
        core = t_from_table > np.median(t_from_table)
    center = vertices[core][:, others].mean(0)
    radius = np.linalg.norm(vertices[:, others] - center, axis=1)
    ref = float(np.percentile(radius[core], 90))
    for t_cut in np.linspace(0.0, 0.35, 36):
        band = (t_from_table >= t_cut) & (t_from_table < t_cut + 0.05)
        if int(band.sum()) < 30:
            continue
        if float(np.percentile(radius[band], 90)) < ref * 1.6:
            return float(max(t_cut, 0.03))
    return 0.08


def subset_faces(mesh, keep_faces: np.ndarray):
    geom = _as_trimesh(mesh)
    face_idx = np.flatnonzero(keep_faces)
    if face_idx.size < 20:
        raise RuntimeError("table trim removed almost all faces")
    trimmed = geom.submesh([face_idx], append=True, repair=False)
    if isinstance(trimmed, list):
        trimmed = trimmed[0]
    components = trimmed.split(only_watertight=False)
    if not components:
        return trimmed
    substantial = [part for part in components if len(part.faces) >= 80]
    keep = substantial or [max(components, key=lambda part: len(part.faces))]
    if len(keep) == 1:
        return keep[0]
    return trimesh.util.concatenate(keep)


def trim_fake_table(mesh, t_cut: float | None = None) -> tuple[trimesh.Trimesh, dict]:
    geom = _as_trimesh(mesh)
    axis, t_from_table, _table_at_low, meta = table_axis_and_height(geom)
    if t_cut is None:
        t_cut = adaptive_t_cut(t_from_table, np.asarray(geom.vertices), axis)
    keep_vertex = t_from_table > t_cut
    keep_faces = keep_vertex[np.asarray(geom.faces)].all(axis=1)
    trimmed = subset_faces(geom, keep_faces)
    before = np.asarray(geom.bounding_box.extents)
    after = np.asarray(trimmed.bounding_box.extents)
    meta.update(
        {
            "t_cut": t_cut,
            "faces_before": int(len(geom.faces)),
            "faces_after": int(len(trimmed.faces)),
            "verts_before": int(len(geom.vertices)),
            "verts_after": int(len(trimmed.vertices)),
            "aabb_before_cm": (before * 100.0).tolist(),
            "aabb_after_cm": (after * 100.0).tolist(),
            "obb_after_cm": (np.asarray(trimesh.bounds.oriented_bounds(trimmed)[1]) * 100.0).tolist(),
        }
    )
    return trimmed, meta


def render_vertex_views(mesh, path: Path, size: int = 360) -> None:
    vertices = np.asarray(_as_trimesh(mesh).vertices)
    vertices = vertices - vertices.mean(0)
    height = vertices[:, 1]
    height = (height - height.min()) / max(float(height.ptp()), 1e-8)
    colors = np.stack([height, 0.35 + 0.4 * (1.0 - height), 1.0 - height], axis=1)
    colors = (np.clip(colors, 0, 1) * 255).astype(np.uint8)
    tiles = []
    order = np.argsort(vertices[:, 1])
    for axes in ((0, 2), (0, 1), (2, 1)):
        pts = vertices[:, list(axes)]
        span = float((pts.max(0) - pts.min(0)).max()) * 1.15
        mid = (pts.max(0) + pts.min(0)) / 2.0
        uv = (pts - mid) / max(span, 1e-8)
        px = ((uv[:, 0] + 0.5) * (size - 1)).astype(int)
        py = ((0.5 - uv[:, 1]) * (size - 1)).astype(int)
        image = np.full((size, size, 3), 240, np.uint8)
        for i in order[::2]:
            x, y = int(px[i]), int(py[i])
            if 0 <= x < size and 0 <= y < size:
                image[y, x] = colors[i]
        tiles.append(Image.fromarray(image))
    out = Image.new("RGB", (size * 3 + 8, size), (255, 255, 255))
    for i, tile in enumerate(tiles):
        out.paste(tile, (i * (size + 4), 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)


def copy_to_library(
    *,
    library_dir: Path,
    visual: trimesh.Trimesh,
    hull: trimesh.Trimesh,
    info: dict,
    meta: dict,
    extents_cm: list[float],
) -> None:
    library_dir.mkdir(parents=True, exist_ok=True)
    visual.export(str(library_dir / "visual_scaled.glb"))
    hull.export(str(library_dir / "collision_hull.glb"))
    (library_dir / "pose_info.json").write_text(json.dumps(info, indent=4) + "\n", encoding="utf-8")
    (library_dir / "trim_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    asset_path = library_dir / "asset.json"
    asset = json.loads(asset_path.read_text(encoding="utf-8")) if asset_path.is_file() else {}
    asset["extents_cm"] = extents_cm
    asset.setdefault("visual", {})
    asset["visual"]["scaled_glb"] = "visual_scaled.glb"
    asset["visual"]["quality"] = "trimmed_hunyuan"
    asset["visual"]["notes"] = (
        "Fake Hunyuan table slab cut off; remaining shell scaled to locked extents. "
        "Collision is the convex hull of the trimmed mesh, not the full visual."
    )
    asset["collision"] = {
        "type": "convex_hull",
        "glb": "collision_hull.glb",
        "do_not_use_full_mesh": True,
        "reason": "visual is a thin shell; hull is the remaining hat/bottle after table trim",
    }
    asset_path.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-dir", required=True, type=Path)
    parser.add_argument("--indices", default="0,1")
    parser.add_argument(
        "--extents-cm",
        action="append",
        default=[],
        metavar="IDX:L,W,H",
        help="Per-object locked extents, e.g. 0:28,22,16  (repeatable)",
    )
    parser.add_argument("--library-root", type=Path, default=None)
    parser.add_argument(
        "--library-names",
        default="hard_hat,water_bottle",
        help="Comma-separated library folder names, same order as --indices",
    )
    args = parser.parse_args()

    indices = [int(x.strip()) for x in args.indices.split(",") if x.strip()]
    extents_by_idx: dict[int, np.ndarray] = {}
    for item in args.extents_cm:
        idx_s, cm_s = item.split(":", 1)
        extents_by_idx[int(idx_s)] = np.array([float(x) for x in cm_s.split(",")], dtype=float)
        if extents_by_idx[int(idx_s)].size != 3:
            raise SystemExit(f"bad extents: {item}")
    library_names = [x.strip() for x in args.library_names.split(",") if x.strip()]
    if args.library_root and len(library_names) != len(indices):
        raise SystemExit("--library-names must match --indices")

    mesh_dir = args.scene_dir / "s8_pose" / "canonical_mesh"
    info_dir = args.scene_dir / "s8_pose" / "info"
    source_dir = mesh_dir / "_backup_pre_known_extents"
    dirty_backup = mesh_dir / "_backup_pre_table_trim"
    preview_dir = args.scene_dir / "s8_pose" / "table_trim_preview"
    dirty_backup.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    for order, idx in enumerate(indices):
        glb = mesh_dir / f"iter_{idx}.glb"
        info_path = info_dir / f"iter_{idx}.json"
        source = source_dir / glb.name
        if not source.is_file():
            raise SystemExit(f"missing unscaled backup: {source}")
        if glb.is_file() and not (dirty_backup / glb.name).exists():
            shutil.copy2(glb, dirty_backup / glb.name)
        if info_path.is_file() and not (dirty_backup / info_path.name).exists():
            shutil.copy2(info_path, dirty_backup / info_path.name)

        raw = load_mesh(source)
        render_vertex_views(_as_trimesh(raw), preview_dir / f"iter_{idx}_before.png")
        trimmed, meta = trim_fake_table(raw)
        render_vertex_views(trimmed, preview_dir / f"iter_{idx}_after.png")
        hull = _as_trimesh(trimmed).convex_hull
        render_vertex_views(hull, preview_dir / f"iter_{idx}_hull.png")

        if idx in extents_by_idx:
            bake, scale_meta = obb_scale_transform(trimmed, extents_by_idx[idx] / 100.0)
            trimmed = trimmed.copy()
            trimmed.apply_transform(bake)
            hull = _as_trimesh(trimmed).convex_hull
            after = trimesh.bounds.oriented_bounds(_as_trimesh(trimmed))[1]
            meta["known_extents_cm"] = extents_by_idx[idx].tolist()
            meta["known_extents_meta"] = scale_meta
            meta["obb_after_scale_cm"] = (np.asarray(after) * 100.0).tolist()

        trimmed.export(str(glb))
        hull_dir = args.scene_dir / "s8_pose" / "collision_hull"
        hull_dir.mkdir(parents=True, exist_ok=True)
        hull.export(str(hull_dir / f"iter_{idx}.glb"))
        (preview_dir / f"iter_{idx}_meta.json").write_text(
            json.dumps(meta, indent=2) + "\n", encoding="utf-8"
        )

        info = json.loads(info_path.read_text(encoding="utf-8"))
        if idx in extents_by_idx:
            target_m = extents_by_idx[idx] / 100.0
            info["known_extents_cm"] = extents_by_idx[idx].tolist()
            info["known_extents_m"] = target_m.tolist()
            info["known_extents_meta"] = meta["known_extents_meta"]
            info["obb_extents_after_m"] = np.asarray(after, dtype=float).tolist()
            info["obb_extents_after_cm"] = (np.asarray(after) * 100.0).tolist()
            info["table_trim"] = {k: meta[k] for k in ("t_cut", "table_axis", "aabb_before_cm", "aabb_after_cm")}
            for key in ("z_up", "y_up"):
                if key in info and "scale" in info[key]:
                    info[key]["scale"] = [1.0, 1.0, 1.0] if isinstance(info[key]["scale"], list) else 1.0
        info_path.write_text(json.dumps(info, indent=4) + "\n", encoding="utf-8")

        if args.library_root:
            copy_to_library(
                library_dir=args.library_root / library_names[order],
                visual=trimmed,
                hull=hull,
                info=info,
                meta=meta,
                extents_cm=extents_by_idx[idx].tolist() if idx in extents_by_idx else meta["aabb_after_cm"],
            )
            shutil.copy2(preview_dir / f"iter_{idx}_before.png", args.library_root / library_names[order] / "trim_before.png")
            shutil.copy2(preview_dir / f"iter_{idx}_after.png", args.library_root / library_names[order] / "trim_after.png")
            shutil.copy2(preview_dir / f"iter_{idx}_hull.png", args.library_root / library_names[order] / "trim_hull.png")

        after_cm = np.round(np.sort(meta.get("obb_after_scale_cm", meta["obb_after_cm"])), 2).tolist()
        print(
            f"iter_{idx}: t_cut={meta['t_cut']:.3f} axis={meta['table_axis']} "
            f"AABB {np.round(meta['aabb_before_cm'],2).tolist()} -> {np.round(meta['aabb_after_cm'],2).tolist()} cm "
            f"OBB {after_cm} cm  faces {meta['faces_before']}->{meta['faces_after']}"
        )


if __name__ == "__main__":
    main()
