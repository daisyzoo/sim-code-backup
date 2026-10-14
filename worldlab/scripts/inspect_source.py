#!/usr/bin/env python3
"""Sparse CPU projection for orientation diagnosis, NOT an RTX render."""
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from pxr import Gf, Usd, UsdGeom
from usd_convert_gsplat import read_ply

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from worldlab.assets import load_config

if __name__ == "__main__":
    cfg = load_config()
    data = read_ply(str(ROOT / cfg["splat"]))
    stage = Usd.Stage.Open(str(ROOT / cfg["output"] / "kitchen.usda"))
    transform = UsdGeom.Xformable(stage.GetPrimAtPath("/World/Kitchen")).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    points = np.column_stack([data.positions[::2], np.ones(len(data.positions[::2]))]) @ np.array(transform)
    colors = np.uint8(np.clip(0.5 + 0.28209479 * data.f_dc[::2], 0, 1) * 255)
    images = []
    for name, camera in cfg["cameras"].items():
        view = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*camera["eye"]), Gf.Vec3d(*camera["target"]), Gf.Vec3d(0, 0, 1))
        p = points @ np.array(view)
        depth = -p[:, 2]
        u = (p[:, 0] / np.maximum(depth, 1e-5) * 320 + 320).astype(int)
        v = (180 - p[:, 1] / np.maximum(depth, 1e-5) * 320).astype(int)
        keep = (depth > 0.05) & (data.opacities[::2] > -3) & (u >= 0) & (u < 640) & (v >= 0) & (v < 360)
        ids = np.flatnonzero(keep)
        ids = ids[np.argsort(depth[ids])[::-1]]
        pixels = np.zeros((360, 640, 3), dtype=np.uint8)
        pixels[v[ids], u[ids]] = colors[ids]
        image = Image.fromarray(pixels)
        ImageDraw.Draw(image).text((8, 8), "CPU points diagnostic: " + name, fill="white")
        images.append(image)
    canvas = Image.new("RGB", (640, 360 * len(images)))
    for index, image in enumerate(images):
        canvas.paste(image, (0, index * 360))
    (ROOT / "outputs").mkdir(exist_ok=True)
    canvas.save(ROOT / "outputs/source_orientation_diagnostic.jpg")
