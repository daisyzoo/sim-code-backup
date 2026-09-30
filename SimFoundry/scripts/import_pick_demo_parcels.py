#!/usr/bin/env python3
"""Import pick_demo atlas bakes as PNG albedo + derived normals for cuboids.

Uses the camera-baked atlas top face (not masked_object JPEG). Bag wrinkle
signal lives in those baked highlights; JPEG + XY-UV was flattening it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT.parent / "nvidia" / "SimFoundry" / "Data" / "pick_demo"
OUT = ROOT / "assets" / "textures" / "sorting_station" / "parcels"
PX_PER_M = 4000.0
ATLAS_PAD = 2

OBJECT_ITERS: dict[str, int] = {
    "parcel_box": 0,
    "parcel_box_b": 2,
    "mailer": 1,
    "mailer_b": 5,
    "mailer_c": 7,
    "mailer_d": 9,
}
EXTRA_ITERS = (4, 6, 8)


def _kind(iter_idx: int) -> str:
    return "mailer" if iter_idx in {1, 5, 7, 8, 9} else "box"


def _filename(iter_idx: int) -> str:
    return f"{_kind(iter_idx)}_iter_{iter_idx}.png"


def _pixel_diff(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _crop_score(im: Image.Image, fill: tuple[int, int, int]) -> float:
    pix = im.load()
    w, h = im.size
    n = max(1, (w * h) // 17)
    acc = 0.0
    count = 0
    for i in range(n):
        x = (i * 17) % w
        y = (i * 13) % h
        acc += _pixel_diff(pix[x, y], fill)
        count += 1
    return acc / count


def crop_atlas_top(atlas: Image.Image, extents_cm: list[float] | None) -> Image.Image:
    """Take the first packed bake (top face) from the SimFoundry atlas."""
    atlas = atlas.convert("RGB")
    fill = atlas.getpixel((0, 0))
    w, h = atlas.size
    cands: list[tuple[int, int]] = []
    if extents_cm and len(extents_cm) == 3:
        e = sorted(float(x) / 100.0 for x in extents_cm)
        mid, long = e[1], e[2]
        cands.extend(
            [
                (max(32, int(round(mid * PX_PER_M))), max(16, int(round(long * PX_PER_M)))),
                (max(32, int(round(long * PX_PER_M))), max(16, int(round(mid * PX_PER_M)))),
            ]
        )
    best = None
    best_score = -1.0
    for nu, nv in cands:
        if ATLAS_PAD + nu > w or ATLAS_PAD + nv > h:
            continue
        crop = atlas.crop((ATLAS_PAD, ATLAS_PAD, ATLAS_PAD + nu, ATLAS_PAD + nv))
        score = _crop_score(crop, fill)
        if score > best_score:
            best_score = score
            best = crop
    if best is not None and best_score > 8.0:
        return best

    # Fallback: bbox of pixels that differ from fill in the top-left quadrant.
    pix = atlas.load()
    max_x, max_y = w // 2, h // 2
    minx, miny, maxx, maxy = max_x, max_y, 0, 0
    found = False
    for y in range(ATLAS_PAD, max_y):
        for x in range(ATLAS_PAD, max_x):
            if _pixel_diff(pix[x, y], fill) > 18:
                found = True
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    if found and maxx - minx > 16 and maxy - miny > 16:
        return atlas.crop((minx, miny, maxx + 1, maxy + 1))
    return atlas


def albedo_to_normal(im: Image.Image, *, strength: float) -> Image.Image:
    """Sobel-from-luma normal map so bag folds read without extra geometry."""
    gray = ImageOps.grayscale(im).filter(ImageFilter.SMOOTH)
    w, h = gray.size
    src = gray.load()
    out = Image.new("RGB", (w, h))
    dst = out.load()
    s = float(strength)
    for y in range(h):
        ym, yp = max(0, y - 1), min(h - 1, y + 1)
        for x in range(w):
            xm, xp = max(0, x - 1), min(w - 1, x + 1)
            dx = (src[xp, y] - src[xm, y]) / 255.0
            dy = (src[x, yp] - src[x, ym]) / 255.0
            nx, ny, nz = -dx * s, -dy * s, 1.0
            nlen = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
            dst[x, y] = (
                int(max(0, min(255, (nx / nlen * 0.5 + 0.5) * 255))),
                int(max(0, min(255, (ny / nlen * 0.5 + 0.5) * 255))),
                int(max(0, min(255, (nz / nlen * 0.5 + 0.5) * 255))),
            )
    return out


def _boost_bag(im: Image.Image) -> Image.Image:
    """Lift fold highlights on near-black plastic without blowing fill."""
    im = ImageEnhance.Contrast(im).enhance(1.18)
    im = ImageEnhance.Brightness(im).enhance(1.08)
    return im


def import_parcels(src: Path, out: Path) -> dict[str, str]:
    preview = src / "photo_textured_preview"
    extents = json.loads((src / "object_extents.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)

    written: dict[str, str] = {}
    normals: dict[str, str] = {}
    iters = sorted({*OBJECT_ITERS.values(), *EXTRA_ITERS})
    for idx in iters:
        atlas_path = preview / f"iter_{idx}_atlas.png"
        if not atlas_path.is_file():
            print(f"skip missing {atlas_path}", file=sys.stderr)
            continue
        atlas = Image.open(atlas_path).convert("RGB")
        cm = extents.get("objects", {}).get(f"iter_{idx}", {}).get("extents_cm")
        top = crop_atlas_top(atlas, cm)
        kind = _kind(idx)
        if kind == "mailer":
            top = _boost_bag(top)
        name = _filename(idx)
        dest = out / name
        top.save(dest, format="PNG")
        n_name = name.replace(".png", "_n.png")
        strength = 4.2 if kind == "mailer" else 1.6
        albedo_to_normal(top, strength=strength).save(out / n_name, format="PNG")
        written[f"iter_{idx}"] = name
        normals[f"iter_{idx}"] = n_name
        print(f"wrote {dest.relative_to(ROOT)}  {top.size}  normal={n_name}")

    mapping = {obj: _filename(idx) for obj, idx in OBJECT_ITERS.items() if _filename(idx) in written.values()}
    box_pool = [written[f"iter_{i}"] for i in (0, 2, 4, 6) if f"iter_{i}" in written]
    mailer_pool = [written[f"iter_{i}"] for i in (1, 5, 7, 8, 9) if f"iter_{i}" in written]
    manifest = {
        "source": str(src),
        "object_to_file": mapping,
        "object_to_normal": {
            obj: normals[f"iter_{idx}"]
            for obj, idx in OBJECT_ITERS.items()
            if f"iter_{idx}" in normals
        },
        "iter_to_file": written,
        "iter_to_normal": normals,
        "box_pool": box_pool,
        "mailer_pool": mailer_pool,
        "extents_cm": {k: v.get("extents_cm") for k, v in extents.get("objects", {}).items()},
        "notes": "PNG atlas top-face bakes + sobel normals. Do not JPEG bags.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return mapping


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    if not (src / "object_extents.json").is_file():
        raise SystemExit(f"pick_demo scene not found: {src}")
    mapping = import_parcels(src, OUT)
    print(f"object mapping: {mapping}")


if __name__ == "__main__":
    main()
