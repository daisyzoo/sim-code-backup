#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Stamp a video object-crop onto a frozen-fold flat box.

This is for towels (and similar thin stacks), not parcels. It does not read
camera K/R/t, does not call ``build_photo_textured_assets.py``, and does not
overwrite Hunyuan meshes. Output goes next to ``asset.json`` in a library
folder.

Convention: ``extents_cm = [length, width, thickness]``, +Z is up. The crop
is fitted onto the +Z face; sides and bottom get the cloth fill sampled from
the mask, not cardboard/bag defaults.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image
from trimesh.visual import TextureVisuals
from trimesh.visual.material import PBRMaterial

PX_PER_CM = 40
ATLAS_PAD = 4
BLACK_LUMA = 18


def load_crop(path: Path) -> tuple[np.ndarray, np.ndarray]:
    im = Image.open(path)
    if im.mode == "RGBA":
        arr = np.asarray(im.convert("RGBA"))
        rgb = arr[:, :, :3]
        alpha = arr[:, :, 3]
        luma = rgb.mean(axis=2)
        mask = (alpha > 16) & (luma > BLACK_LUMA)
    else:
        rgb = np.asarray(im.convert("RGB"))
        luma = rgb.mean(axis=2)
        mask = luma > BLACK_LUMA
    if mask.sum() < 50:
        raise SystemExit(f"crop looks empty: {path}")
    return rgb, mask.astype(np.uint8) * 255


def tight_crop(rgb: np.ndarray, mask: np.ndarray, pad: int = 6) -> tuple[np.ndarray, np.ndarray]:
    ys, xs = np.where(mask > 0)
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0 = max(0, y0 - pad)
    x0 = max(0, x0 - pad)
    y1 = min(rgb.shape[0], y1 + pad)
    x1 = min(rgb.shape[1], x1 + pad)
    return rgb[y0:y1, x0:x1].copy(), mask[y0:y1, x0:x1].copy()


def cloth_fill(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    pix = rgb[mask > 0]
    med = np.median(pix, axis=0)
    return tuple(int(np.clip(c, 0, 255)) for c in med)


def fit_top(crop_rgb: np.ndarray, crop_mask: np.ndarray, nu: int, nv: int, fill: tuple[int, int, int]) -> np.ndarray:
    """Letterbox the crop into a length×width rectangle. Preserve aspect."""
    canvas = np.empty((nv, nu, 3), dtype=np.uint8)
    canvas[:] = np.asarray(fill, dtype=np.uint8)
    ch, cw = crop_rgb.shape[:2]
    scale = min(nu / max(cw, 1), nv / max(ch, 1))
    tw = max(1, int(round(cw * scale)))
    th = max(1, int(round(ch * scale)))
    resized = np.asarray(Image.fromarray(crop_rgb).resize((tw, th), Image.Resampling.LANCZOS))
    mask_r = np.asarray(
        Image.fromarray(crop_mask).resize((tw, th), Image.Resampling.NEAREST)
    )
    x0 = (nu - tw) // 2
    y0 = (nv - th) // 2
    dest = canvas[y0 : y0 + th, x0 : x0 + tw]
    keep = mask_r > 0
    dest[keep] = resized[keep]
    return canvas


def side_strip(fill: tuple[int, int, int], nu: int, nv: int, darken: float = 0.92) -> np.ndarray:
    color = np.clip(np.asarray(fill, dtype=np.float32) * darken, 0, 255).astype(np.uint8)
    img = np.empty((nv, nu, 3), dtype=np.uint8)
    img[:] = color
    # Slight top-to-bottom shade so the stack is not a flat slab in side view.
    ramp = np.linspace(1.06, 0.82, nv, dtype=np.float32)[:, None, None]
    return np.clip(img.astype(np.float32) * ramp, 0, 255).astype(np.uint8)


def pack_atlas(faces: list[np.ndarray], fill: tuple[int, int, int]) -> tuple[Image.Image, list[tuple[float, float, float, float]]]:
    top, bottom, pos_x, neg_x, pos_y, neg_y = faces
    row0_h, row0_w = top.shape[0], top.shape[1] + ATLAS_PAD + bottom.shape[1]
    side_h = max(pos_x.shape[0], neg_x.shape[0], pos_y.shape[0], neg_y.shape[0])
    side_w = pos_x.shape[1] + neg_x.shape[1] + pos_y.shape[1] + neg_y.shape[1] + ATLAS_PAD * 3
    atlas_w = max(row0_w, side_w) + ATLAS_PAD * 2
    atlas_h = top.shape[0] + side_h + ATLAS_PAD * 3
    side = int(2 ** np.ceil(np.log2(max(atlas_w, atlas_h, 64))))
    atlas = np.empty((side, side, 3), dtype=np.uint8)
    atlas[:] = np.asarray(fill, dtype=np.uint8)

    placements: list[tuple[int, int, int, int]] = []

    def blit(im: np.ndarray, x: int, y: int) -> None:
        fh, fw = im.shape[:2]
        atlas[y : y + fh, x : x + fw] = im
        placements.append((x, y, fw, fh))

    blit(top, ATLAS_PAD, ATLAS_PAD)
    blit(bottom, ATLAS_PAD * 2 + top.shape[1], ATLAS_PAD)
    x = ATLAS_PAD
    y = ATLAS_PAD * 2 + top.shape[0]
    for im in (pos_x, neg_x, pos_y, neg_y):
        blit(im, x, y)
        x += im.shape[1] + ATLAS_PAD

    uvs: list[tuple[float, float, float, float]] = []
    for x0, y0, fw, fh in placements:
        u0, u1 = x0 / side, (x0 + fw) / side
        v0 = 1.0 - y0 / side
        v1 = 1.0 - (y0 + fh) / side
        uvs.append((u0, v0, u1, v1))
    return Image.fromarray(atlas), uvs


def textured_flatbox(
    length_m: float,
    width_m: float,
    thick_m: float,
    top: np.ndarray,
    fill: tuple[int, int, int],
    roughness: float,
) -> tuple[trimesh.Trimesh, Image.Image]:
    hx, hy, hz = length_m / 2.0, width_m / 2.0, thick_m / 2.0
    nu_len = max(32, int(round(length_m * 100 * PX_PER_CM)))
    nv_wid = max(32, int(round(width_m * 100 * PX_PER_CM)))
    nv_th = max(8, int(round(thick_m * 100 * PX_PER_CM)))

    bottom = np.empty_like(top)
    bottom[:] = np.clip(np.asarray(fill, dtype=np.float32) * 0.72, 0, 255).astype(np.uint8)
    pos_x = side_strip(fill, nv_wid, nv_th, 0.90)
    neg_x = side_strip(fill, nv_wid, nv_th, 0.88)
    pos_y = side_strip(fill, nu_len, nv_th, 0.94)
    neg_y = side_strip(fill, nu_len, nv_th, 0.86)

    atlas, uv_boxes = pack_atlas([top, bottom, pos_x, neg_x, pos_y, neg_y], fill)

    def corner(x, y, z):
        return np.array([x, y, z], dtype=np.float64)

    # origin, +u, +u+v, +v ; u along first edge in bake
    quads = [
        [  # +Z top, u=+X (length), v=+Y (width)
            corner(-hx, -hy, hz),
            corner(hx, -hy, hz),
            corner(hx, hy, hz),
            corner(-hx, hy, hz),
        ],
        [  # -Z bottom
            corner(-hx, -hy, -hz),
            corner(-hx, hy, -hz),
            corner(hx, hy, -hz),
            corner(hx, -hy, -hz),
        ],
        [  # +X
            corner(hx, -hy, -hz),
            corner(hx, hy, -hz),
            corner(hx, hy, hz),
            corner(hx, -hy, hz),
        ],
        [  # -X
            corner(-hx, hy, -hz),
            corner(-hx, -hy, -hz),
            corner(-hx, -hy, hz),
            corner(-hx, hy, hz),
        ],
        [  # +Y
            corner(-hx, hy, -hz),
            corner(-hx, hy, hz),
            corner(hx, hy, hz),
            corner(hx, hy, -hz),
        ],
        [  # -Y
            corner(hx, -hy, -hz),
            corner(hx, -hy, hz),
            corner(-hx, -hy, hz),
            corner(-hx, -hy, -hz),
        ],
    ]

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
    return tm, atlas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-dir", required=True, type=Path, help="library folder with asset.json")
    parser.add_argument(
        "--crop",
        default="s5_crop.png",
        help="Video crop inside asset-dir. Default s5_crop.png (real mask), not the Hunyuan upsample.",
    )
    parser.add_argument("--roughness", type=float, default=0.82)
    args = parser.parse_args()

    asset_dir = args.asset_dir.resolve()
    spec = json.loads((asset_dir / "asset.json").read_text(encoding="utf-8"))
    extents_cm = np.asarray(spec["extents_cm"], dtype=float)
    if extents_cm.size != 3:
        raise SystemExit("asset.json extents_cm must be [length, width, thickness] cm")
    length_m, width_m, thick_m = extents_cm / 100.0

    crop_path = asset_dir / args.crop
    if not crop_path.is_file():
        raise SystemExit(f"missing crop: {crop_path}")
    rgb, mask = load_crop(crop_path)
    rgb, mask = tight_crop(rgb, mask)
    fill = cloth_fill(rgb, mask)

    nu = max(32, int(round(extents_cm[0] * PX_PER_CM)))
    nv = max(32, int(round(extents_cm[1] * PX_PER_CM)))
    top = fit_top(rgb, mask, nu, nv, fill)
    mesh, atlas = textured_flatbox(length_m, width_m, thick_m, top, fill, args.roughness)

    atlas_path = asset_dir / "photo_flatbox_atlas.png"
    glb_path = asset_dir / "photo_flatbox.glb"
    top_path = asset_dir / "photo_flatbox_top.png"
    atlas.save(atlas_path)
    Image.fromarray(top).save(top_path)
    mesh.export(str(glb_path))

    after = mesh.extents
    visual = spec.setdefault("visual", {})
    visual["photo_flatbox_glb"] = glb_path.name
    visual["photo_flatbox_atlas"] = atlas_path.name
    visual["photo_flatbox_top"] = top_path.name
    visual["primary"] = glb_path.name
    visual["quality"] = "photo_flatbox"
    visual["fill_rgb"] = list(fill)
    visual["notes"] = (
        "Frozen-fold flat AABB. Top face is the video crop (s5 mask), sides/bottom "
        "use sampled cloth fill. Hunyuan kept as hunyuan_*.glb, not used as primary visual."
    )
    spec["collision"] = {
        "type": "aabb",
        "extents_cm": extents_cm.tolist(),
        "do_not_use_full_mesh": True,
        "visual_mesh": glb_path.name,
        "reason": "flat box matches the frozen fold; Hunyuan has a fake slab",
    }
    (asset_dir / "asset.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(
        f"{spec['id']}: wrote {glb_path.name}  extents_cm={extents_cm.tolist()}  "
        f"aabb_cm={np.round(after * 100, 2).tolist()}  fill_rgb={fill}"
    )


if __name__ == "__main__":
    main()
