#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Add leftover black mailers from the source video. Does not add the table."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
import trimesh
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.pipeline.A_reconstruction.tools.build_photo_textured_assets import (  # noqa: E402
    object_fill_color,
    textured_box,
)

PHRASE = "black plastic bag"
START_ITER = 7


def load_rgb_and_union(scene_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    img_idx = int(json.loads((scene_dir / "s5_scene" / "decomposition_frame.json").read_text())["img_idx"])
    frames = sorted((scene_dir / "s1_video" / "frames_subsampled_15").glob("*.png"))
    rgb = np.asarray(Image.open(frames[img_idx]).convert("RGB"))
    h, w = rgb.shape[:2]
    union = np.zeros((h, w), np.uint8)
    for path in sorted((scene_dir / "s5_scene" / "removal_mask").glob("iter_*.png")):
        idx = int(path.stem.split("_")[1])
        if idx == 3 or idx >= START_ITER:
            continue
        raw = np.asarray(Image.open(path).convert("L"))
        mh, mw = raw.shape
        union |= (raw[(mh - h) // 2 : (mh - h) // 2 + h, (mw - w) // 2 : (mw - w) // 2 + w] > 0).astype(np.uint8)
    return rgb, union


def remaining_bag_masks(rgb: np.ndarray, union: np.ndarray) -> list[np.ndarray]:
    h, w = rgb.shape[:2]
    luma = rgb.mean(axis=2)
    dark = ((luma < 90) & (union == 0)).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(dark, 8)
    masks: list[np.ndarray] = []
    for i in range(1, n):
        area = int(stats[i, cv2.CC_STAT_AREA])
        cx, cy = cents[i]
        if area < 2500 or cx < 220 or cy > 620:
            continue
        # leftovers of already-kept bags sit next to large existing masks
        if area < 7000:
            continue
        comp = lab == i
        if area > 15000:
            ys, xs = np.where(comp)
            pts = np.stack([xs, ys], 1).astype(np.float32)
            _, labels, _ = cv2.kmeans(
                pts,
                2,
                None,
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5),
                8,
                cv2.KMEANS_PP_CENTERS,
            )
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            for k in range(2):
                m = np.zeros((h, w), np.uint8)
                m[ys[labels.ravel() == k], xs[labels.ravel() == k]] = 255
                m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)
                if int(m.sum() / 255) >= 2500:
                    masks.append(m)
        else:
            masks.append((comp.astype(np.uint8) * 255))
    masks.sort(key=lambda m: -int(m.sum()))
    return masks[:3]


def min_area_wh(mask: np.ndarray) -> tuple[float, float]:
    ys, xs = np.where(mask > 0)
    pts = np.stack([xs, ys], 1).astype(np.float32)
    (_cx, _cy), (bw, bh), _ang = cv2.minAreaRect(pts)
    return float(max(bw, bh)), float(min(bw, bh))


def pad_mask(mask_hi: np.ndarray, pad_h: int = 736, pad_w: int = 1408) -> np.ndarray:
    h, w = mask_hi.shape
    out = np.zeros((pad_h, pad_w), np.uint8)
    top, left = (pad_h - h) // 2, (pad_w - w) // 2
    out[top : top + h, left : left + w] = mask_hi
    return out


def masked_crop(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    ys, xs = np.where(mask > 0)
    y0, y1 = max(0, ys.min() - 4), min(rgb.shape[0], ys.max() + 5)
    x0, x1 = max(0, xs.min() - 4), min(rgb.shape[1], xs.max() + 5)
    crop = rgb[y0:y1, x0:x1].copy()
    m = mask[y0:y1, x0:x1] > 0
    crop[~m] = 0
    return crop


def estimate_extents_cm(depth_pts: np.ndarray, scale: float) -> list[float]:
    obb = np.sort(trimesh.bounds.oriented_bounds(depth_pts)[1]) * 100.0 * scale
    thick, width, length = (float(v) for v in obb)
    thick = float(np.clip(thick, 2.5, 3.5))
    width = float(np.clip(width, 6.0, 14.0))
    length = float(np.clip(length, 8.0, 16.0))
    return [round(length, 1), round(width, 1), round(thick, 1)]


def camera_points(mask_hi: np.ndarray, depth: np.ndarray, k_da: np.ndarray) -> np.ndarray:
    h_da, w_da = depth.shape
    h_hi, w_hi = mask_hi.shape
    small = cv2.resize(mask_hi, (w_da, h_da), interpolation=cv2.INTER_NEAREST)
    ys, xs = np.where(small > 0)
    z = depth[ys, xs]
    keep = np.isfinite(z) & (z > 0.05) & (z < 2.5)
    ys, xs, z = ys[keep], xs[keep], z[keep]
    kinv = np.linalg.inv(k_da)
    uv = np.stack([xs.astype(np.float64), ys.astype(np.float64), np.ones(len(xs))], 1)
    return (uv @ kinv.T) * z[:, None]


def pose_from_points(pts: np.ndarray, target_cm: list[float]):
    to_origin, obb = trimesh.bounds.oriented_bounds(pts)
    target = np.sort(np.asarray(target_cm, dtype=float)) / 100.0
    extents = np.zeros(3, dtype=float)
    extents[np.argsort(obb)] = target
    inv = np.linalg.inv(to_origin)
    R, t = inv[:3, :3], inv[:3, 3]
    info = {
        "z_up": {"trans": t.tolist(), "rot": R.tolist(), "scale": [1.0, 1.0, 1.0]},
        "y_up": {"trans": t.tolist(), "rot": R.tolist(), "scale": [1.0, 1.0, 1.0]},
        "pre_scale_factor": 1.0,
        "known_extents_cm": target_cm,
        "known_extents_m": (np.asarray(target_cm) / 100.0).tolist(),
        "obb_extents_after_m": np.sort(extents).tolist(),
        "obb_extents_after_cm": (np.sort(extents) * 100.0).tolist(),
        "known_extents_source": "video_estimate_remaining_bag",
    }
    return np.eye(4), extents, R, t, info


def write_s5(scene_dir: Path, idx: int, mask_hi: np.ndarray, rgb: np.ndarray) -> None:
    s5 = scene_dir / "s5_scene"
    padded = pad_mask(mask_hi)
    Image.fromarray(padded).save(s5 / "removal_mask" / f"iter_{idx}.png")
    Image.fromarray(padded).save(s5 / "removal_mask_resized" / f"iter_{idx}.png")
    crop = masked_crop(rgb, mask_hi)
    Image.fromarray(crop).save(s5 / "masked_object" / f"iter_{idx}.png")
    Image.fromarray(crop).save(s5 / "masked_object_focus" / f"iter_{idx}.png")
    cat = {
        "vlm_categories": [PHRASE],
        "pruned_phrases": [PHRASE],
        "removed_obj_phrase": PHRASE,
        "vlm_categories_full": [PHRASE],
        "pruned_phrases_full": [PHRASE],
        "removed_obj_phrase_full": PHRASE,
        "is_valid_removed_obj": True,
        "skipped_objects": [],
        "source": "add_remaining_bags",
    }
    (s5 / "obj_cat_list" / f"iter_{idx}.json").write_text(json.dumps(cat, indent=4), encoding="utf-8")
    up = scene_dir / "s6_upsample" / "upsampled"
    up.mkdir(parents=True, exist_ok=True)
    Image.fromarray(crop).save(up / f"iter_{idx}.png")


def main() -> None:
    scene_dir = Path("/home/user/Documents/zoo/sim/nvidia/SimFoundry/Data/pick_demo")
    rgb, union = load_rgb_and_union(scene_dir)
    masks = remaining_bag_masks(rgb, union)
    if len(masks) < 3:
        raise SystemExit(f"expected 3 leftover bags, got {len(masks)}")

    img_idx = int(json.loads((scene_dir / "s5_scene" / "decomposition_frame.json").read_text())["img_idx"])
    results = np.load(scene_dir / "s2_da" / "da" / "exports" / "npz" / "results.npz")
    depth = np.asarray(results["depth"][img_idx])
    k_da = np.asarray(results["intrinsics"][img_idx], dtype=np.float64)
    h_da, w_da = results["image"][img_idx].shape[:2]
    h_hi, w_hi = rgb.shape[:2]
    K = k_da.copy()
    K[0] *= w_hi / w_da
    K[1] *= h_hi / h_da

    # calibrate in-plane scale from the user-measured large bag (iter_1, 15 cm)
    m1 = np.asarray(Image.open(scene_dir / "s5_scene" / "removal_mask" / "iter_1.png").convert("L"))
    mh, mw = m1.shape
    m1_hi = m1[(mh - h_hi) // 2 : (mh - h_hi) // 2 + h_hi, (mw - w_hi) // 2 : (mw - w_hi) // 2 + w_hi]
    # Metric size from depth, then scale so the known 15 cm bag matches.
    pts_ref = camera_points(m1_hi, depth, k_da)
    ref_long = float(np.sort(trimesh.bounds.oriented_bounds(pts_ref)[1])[-1] * 100.0)
    size_scale = 15.0 / ref_long

    extents_path = scene_dir / "object_extents.json"
    spec = json.loads(extents_path.read_text(encoding="utf-8"))
    filt_path = scene_dir / "s5_scene" / "object_filter.json"
    filt = json.loads(filt_path.read_text(encoding="utf-8"))
    preview = scene_dir / "photo_textured_preview"
    preview.mkdir(exist_ok=True)
    mesh_dir = scene_dir / "s8_pose" / "canonical_mesh"
    info_dir = scene_dir / "s8_pose" / "info"

    overlay = rgb.copy()
    for i, mask in enumerate(masks):
        idx = START_ITER + i
        pts = camera_points(mask, depth, k_da)
        target_cm = estimate_extents_cm(pts, size_scale)
        to_origin, extents, R, t, pose_info = pose_from_points(pts, target_cm)
        fill = object_fill_color(rgb, mask, PHRASE)
        mesh, atlas = textured_box(extents, to_origin, R, t, 1.0, K, rgb, mask, fill, 0.42)
        write_s5(scene_dir, idx, mask, rgb)
        atlas.save(preview / f"iter_{idx}_atlas.png")
        mesh.export(str(mesh_dir / f"iter_{idx}.glb"))
        (info_dir / f"iter_{idx}.json").write_text(json.dumps(pose_info, indent=4), encoding="utf-8")
        spec["objects"][f"iter_{idx}"] = {
            "phrase": f"{PHRASE} (added)",
            "extents_cm": target_cm,
            "source": "video_estimate",
            "evidence": f"leftover mask {int(mask.sum()/255)} px; depth OBB scaled by {size_scale:.3f} so iter_1=15cm",
        }
        if idx not in filt["keep_indices"]:
            filt["keep_indices"].append(idx)
        color = [(0, 180, 255), (80, 220, 80), (255, 90, 90)][i]
        overlay[mask > 0] = (overlay[mask > 0].astype(np.float32) * 0.45 + np.array(color) * 0.55).astype(np.uint8)
        after = trimesh.bounds.oriented_bounds(mesh)[1]
        print(f"iter_{idx} extents_cm={target_cm} OBB_cm={np.round(np.sort(after)*100, 2).tolist()} fill={fill}")

    filt["keep_indices"] = sorted(int(v) for v in filt["keep_indices"])
    filt["source"] = "human_drop_transparent_sheet_plus_remaining_bags"
    extents_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    filt_path.write_text(json.dumps(filt, indent=4), encoding="utf-8")
    Image.fromarray(overlay).save(preview / "remaining_bags_overlay.png")
    print("keep", filt["keep_indices"])


if __name__ == "__main__":
    main()
