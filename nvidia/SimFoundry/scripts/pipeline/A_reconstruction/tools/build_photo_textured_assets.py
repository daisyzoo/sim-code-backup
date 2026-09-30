#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Build graspable photo-textured cuboids from the source video.

Hunyuan invents drawers and holes on thin parcels. For vision tasks we keep a
correctly-sized convex box and bake the real video (camera projection) onto
every visible face. Unseen faces get the object's cardboard / bag color, not
white, so side views still look like the parcels.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
import trimesh
from PIL import Image
from trimesh.visual import TextureVisuals
from trimesh.visual.material import PBRMaterial

PX_PER_M = 4000.0  # 40 px / cm
ATLAS_PAD = 2


def _as_mesh(mesh):
    if isinstance(mesh, trimesh.Scene):
        return mesh.dump(concatenate=True)
    return mesh


def object_fill_color(rgb: np.ndarray, mask: np.ndarray, phrase: str) -> tuple[int, int, int]:
    pix = rgb[mask > 0]
    if len(pix) < 20:
        return (25, 25, 25) if "bag" in phrase else (163, 117, 70)
    luma = pix.mean(axis=1)
    chroma = pix.max(axis=1) - pix.min(axis=1)
    if "bag" in phrase or "plastic" in phrase:
        keep = luma < 90
        if keep.sum() < 30:
            keep = luma < 140
    else:
        keep = (luma > 45) & (luma < 185) & (chroma > 12)
        if keep.sum() < 30:
            keep = (luma > 45) & (luma < 185)
    sample = pix[keep] if keep.sum() >= 20 else pix
    med = np.median(sample, axis=0)
    return tuple(int(np.clip(c, 0, 255)) for c in med)


def bake_quad(
    corners: np.ndarray,
    R: np.ndarray,
    t: np.ndarray,
    scale: float,
    K: np.ndarray,
    rgb: np.ndarray,
    mask: np.ndarray,
    fill: tuple[int, int, int],
    nu: int,
    nv: int,
) -> np.ndarray:
    """Rasterize a quad in canonical space and sample the video where the face is visible."""
    origin = corners[0]
    axis_u = corners[1] - corners[0]
    axis_v = corners[3] - corners[0]
    n_cam = R @ np.cross(axis_u, axis_v)
    us = (np.arange(nu) + 0.5) / nu
    vs = (np.arange(nv) + 0.5) / nv
    uu, vv = np.meshgrid(us, vs)
    pts = origin + uu[..., None] * axis_u + vv[..., None] * axis_v
    pc = scale * (pts.reshape(-1, 3) @ R.T) + t
    z = pc[:, 2]
    homog = (K @ pc.T).T
    uv = homog[:, :2] / np.clip(homog[:, 2:3], 1e-6, None)
    h, w = rgb.shape[:2]
    xi = np.rint(uv[:, 0]).astype(np.int32)
    yi = np.rint(uv[:, 1]).astype(np.int32)
    facing = (n_cam * pc).sum(axis=1) < 0
    vis = facing & (z > 1e-3) & (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
    img = np.empty((nv * nu, 3), dtype=np.uint8)
    img[:] = np.asarray(fill, dtype=np.uint8)
    if vis.any():
        in_mask = mask[yi[vis], xi[vis]] > 0
        take = np.zeros(vis.shape, dtype=bool)
        take[np.flatnonzero(vis)[in_mask]] = True
        if take.any():
            img[take] = rgb[yi[take], xi[take]]
    return img.reshape(nv, nu, 3)


def pack_atlas(
    faces: list[np.ndarray], fill: tuple[int, int, int]
) -> tuple[Image.Image, list[tuple[float, float, float, float]]]:
    """Pack face images into a square atlas. Returns image and (u0,v0,u1,v1) in OpenGL UV."""
    widths = [im.shape[1] for im in faces]
    heights = [im.shape[0] for im in faces]
    # Two rows: top+bottom, then four sides.
    row0_w = widths[0] + ATLAS_PAD + widths[1]
    row1_w = sum(widths[2:]) + ATLAS_PAD * 3
    atlas_w = max(row0_w, row1_w) + ATLAS_PAD * 2
    atlas_h = heights[0] + max(heights[2:]) + ATLAS_PAD * 3
    side = int(2 ** np.ceil(np.log2(max(atlas_w, atlas_h, 64))))
    atlas = np.zeros((side, side, 3), dtype=np.uint8)
    atlas[:] = np.asarray(fill, dtype=np.uint8)

    uvs: list[tuple[float, float, float, float]] = []
    x = ATLAS_PAD
    y = ATLAS_PAD
    placements: list[tuple[int, int]] = []
    for i, im in enumerate(faces):
        if i == 2:
            x = ATLAS_PAD
            y = ATLAS_PAD * 2 + heights[0]
        fh, fw = im.shape[:2]
        atlas[y : y + fh, x : x + fw] = im
        placements.append((x, y, fw, fh))
        x += fw + ATLAS_PAD

    for x0, y0, fw, fh in placements:
        # trimesh / OBJ: V=0 at texture bottom.
        u0, u1 = x0 / side, (x0 + fw) / side
        # numpy row 0 is the face v=0 edge; trimesh V=0 is the texture bottom.
        v_face0 = 1.0 - y0 / side
        v_face1 = 1.0 - (y0 + fh) / side
        uvs.append((u0, v_face0, u1, v_face1))
    return Image.fromarray(atlas), uvs


def textured_box(
    extents: np.ndarray,
    to_origin: np.ndarray,
    R: np.ndarray,
    t: np.ndarray,
    scale: float,
    K: np.ndarray,
    rgb: np.ndarray,
    mask: np.ndarray,
    fill: tuple[int, int, int],
    roughness: float,
) -> tuple[trimesh.Trimesh, Image.Image]:
    hx, hy, hz = extents / 2.0
    inv = np.linalg.inv(to_origin)
    # +X in the OBB frame is the thin axis. Pick the 13×8 face the camera actually sees
    # (canonical +Y is not always world-up after pose fitting).
    n_plus_cam = R @ (inv[:3, :3] @ np.array([1.0, 0.0, 0.0]))
    c_plus_cam = scale * (R @ (inv[:3, :3] @ np.array([hx, 0.0, 0.0]) + inv[:3, 3])) + t
    top_sign = 1.0 if float(n_plus_cam @ c_plus_cam) < 0 else -1.0

    def corner(x, y, z):
        return np.array([x, y, z], dtype=np.float64)

    plus_x = [  # outward +X
        corner(hx, -hy, -hz),
        corner(hx, hy, -hz),
        corner(hx, hy, hz),
        corner(hx, -hy, hz),
    ]
    minus_x = [  # outward -X
        corner(-hx, -hy, -hz),
        corner(-hx, -hy, hz),
        corner(-hx, hy, hz),
        corner(-hx, hy, -hz),
    ]
    # Each remaining quad: origin, +u, +u+v, +v with outward winding.
    quads = [
        plus_x if top_sign > 0 else minus_x,
        minus_x if top_sign > 0 else plus_x,
        [  # z = -hz
            corner(-hx, -hy, -hz),
            corner(-hx, hy, -hz),
            corner(hx, hy, -hz),
            corner(hx, -hy, -hz),
        ],
        [  # z = +hz
            corner(-hx, -hy, hz),
            corner(hx, -hy, hz),
            corner(hx, hy, hz),
            corner(-hx, hy, hz),
        ],
        [  # y = -hy
            corner(-hx, -hy, -hz),
            corner(hx, -hy, -hz),
            corner(hx, -hy, hz),
            corner(-hx, -hy, hz),
        ],
        [  # y = +hy
            corner(-hx, hy, -hz),
            corner(-hx, hy, hz),
            corner(hx, hy, hz),
            corner(hx, hy, -hz),
        ],
    ]

    baked = []
    for q in quads:
        pts = [inv[:3, :3] @ p + inv[:3, 3] for p in q]
        # Bake in canonical (same as mesh after apply_transform).
        edge_u = np.linalg.norm(q[1] - q[0])
        edge_v = np.linalg.norm(q[3] - q[0])
        nu = max(32, int(round(edge_u * PX_PER_M)))
        nv = max(16, int(round(edge_v * PX_PER_M)))
        baked.append(bake_quad(np.stack(pts), R, t, scale, K, rgb, mask, fill, nu, nv))

    atlas, uv_boxes = pack_atlas(baked, fill)

    verts: list[np.ndarray] = []
    faces: list[list[int]] = []
    uvs: list[tuple[float, float]] = []
    for q, (u0, v0, u1, v1) in zip(quads, uv_boxes):
        base = len(verts)
        verts.extend(q)
        faces.append([base, base + 1, base + 2])
        faces.append([base, base + 2, base + 3])
        uvs.extend([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    tm = trimesh.Trimesh(
        vertices=np.vstack(verts),
        faces=np.asarray(faces, dtype=np.int64),
        process=False,
    )
    material = PBRMaterial(
        baseColorTexture=atlas.convert("RGB"),
        metallicFactor=0.0,
        roughnessFactor=float(roughness),
    )
    tm.visual = TextureVisuals(uv=np.asarray(uvs, dtype=np.float64), material=material)
    tm.apply_transform(inv)
    return tm, atlas


def load_video_and_masks(scene_dir: Path) -> tuple[np.ndarray, np.ndarray, dict[int, np.ndarray]]:
    img_idx = int(json.loads((scene_dir / "s5_scene" / "decomposition_frame.json").read_text())["img_idx"])
    results = np.load(scene_dir / "s2_da" / "da" / "exports" / "npz" / "results.npz")
    k_da = np.asarray(results["intrinsics"][img_idx], dtype=np.float64)
    h_da, w_da = results["image"][img_idx].shape[:2]

    frames = sorted((scene_dir / "s1_video" / "frames_subsampled_15").glob("*.png"))
    rgb = np.asarray(Image.open(frames[img_idx]).convert("RGB"))
    h_hi, w_hi = rgb.shape[:2]
    K = k_da.copy()
    K[0] *= w_hi / w_da
    K[1] *= h_hi / h_da

    masks: dict[int, np.ndarray] = {}
    for path in sorted((scene_dir / "s5_scene" / "removal_mask").glob("iter_*.png")):
        idx = int(path.stem.split("_")[1])
        raw = np.asarray(Image.open(path).convert("L"))
        mh, mw = raw.shape
        top = max(0, (mh - h_hi) // 2)
        left = max(0, (mw - w_hi) // 2)
        cropped = raw[top : top + h_hi, left : left + w_hi]
        if cropped.shape != (h_hi, w_hi):
            cropped = cv2.resize(cropped, (w_hi, h_hi), interpolation=cv2.INTER_NEAREST)
        masks[idx] = cv2.dilate(cropped, np.ones((7, 7), np.uint8), iterations=1)
    return rgb, K, masks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-dir", required=True, type=Path)
    args = parser.parse_args()

    extents_path = args.scene_dir / "object_extents.json"
    spec = json.loads(extents_path.read_text(encoding="utf-8"))
    mesh_dir = args.scene_dir / "s8_pose" / "canonical_mesh"
    info_dir = args.scene_dir / "s8_pose" / "info"
    backup = mesh_dir / "_backup_before_photo_box"
    backup.mkdir(parents=True, exist_ok=True)
    preview_dir = args.scene_dir / "photo_textured_preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    rgb, K, masks = load_video_and_masks(args.scene_dir)

    for key, obj in spec["objects"].items():
        idx = int(key.split("_")[1])
        glb = mesh_dir / f"iter_{idx}.glb"
        if not backup.joinpath(glb.name).exists():
            shutil.copy2(glb, backup / glb.name)
        src = backup / glb.name

        old = _as_mesh(trimesh.load(str(src), force="mesh"))
        to_origin, obb = trimesh.bounds.oriented_bounds(old)
        target_cm = np.sort(np.asarray(obj["extents_cm"], dtype=float))
        new_extents = np.zeros(3, dtype=float)
        new_extents[np.argsort(obb)] = target_cm / 100.0

        pose = json.loads((info_dir / f"iter_{idx}.json").read_text())["z_up"]
        R = np.asarray(pose["rot"], dtype=np.float64)
        t = np.asarray(pose["trans"], dtype=np.float64)
        scale = float(pose["scale"][0] if isinstance(pose["scale"], list) else pose["scale"])

        phrase = obj["phrase"]
        fill = object_fill_color(rgb, masks[idx], phrase)
        roughness = 0.42 if "bag" in phrase else 0.86
        mesh, atlas = textured_box(
            new_extents, to_origin, R, t, scale, K, rgb, masks[idx], fill, roughness
        )
        atlas.save(preview_dir / f"iter_{idx}_atlas.png")
        mesh.export(str(glb))
        after = trimesh.bounds.oriented_bounds(_as_mesh(trimesh.load(str(glb), force="mesh")))[1]
        print(
            f"{key} {phrase}: OBB {np.round(np.sort(after) * 100, 2).tolist()} cm  "
            f"fill_rgb={fill}"
        )


if __name__ == "__main__":
    main()
