#!/usr/bin/env python3
"""Crop reference textures from ../pic/ for sorting_station Real2Sim look."""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pip install pillow") from exc

ROOT = Path(__file__).resolve().parents[1]
PIC = ROOT.parent / "pic"
OUT = ROOT / "assets" / "textures" / "sorting_station"


def _save(crop: Image.Image, name: str, size: tuple[int, int]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    img = crop.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    path = OUT / name
    img.save(path, quality=92)
    return path


def main() -> None:
    # Powder-blue tabletop with scuffs (pic/5 top-down).
    table = Image.open(PIC / "5.jpg")
    _save(table.crop((180, 220, 900, 980)), "table_top.jpg", (1024, 1024))

    # Front edge wear strip (pic/5 bottom edge).
    _save(table.crop((120, 900, 980, 1020)), "table_edge.jpg", (1024, 128))

    # Grey speckled carpet (pic/3 floor).
    floor = Image.open(PIC / "3.jpg")
    carpet = floor.crop((40, 900, 700, 1400))
    carpet = ImageEnhance.Contrast(carpet).enhance(1.08)
    _save(carpet, "floor_carpet.jpg", (1024, 1024))

    # White backdrop / wrapped equipment (pic/3 right).
    backdrop = floor.crop((520, 80, 900, 720))
    _save(backdrop, "backdrop.jpg", (512, 1024))

    # Thermal label patch (pic/1).
    label = Image.open(PIC / "1.jpg").crop((420, 280, 620, 420))
    _save(label, "shipping_label.jpg", (256, 128))

    # Kraft cardboard tone (pic/4 box top).
    box = Image.open(PIC / "4.jpg").crop((300, 320, 620, 560))
    _save(box, "kraft_box.jpg", (256, 256))

    print(f"Wrote textures to {OUT}")


if __name__ == "__main__":
    main()
