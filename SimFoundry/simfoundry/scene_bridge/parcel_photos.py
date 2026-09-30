"""pick_demo parcel albedo pools. Isaac-free so tests can import it."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

_SIMFOUNDRY = Path(__file__).resolve().parents[2]
PARCEL_TEX_DIR = _SIMFOUNDRY / "assets" / "textures" / "sorting_station" / "parcels"

_BOX_FALLBACK = (
    "box_iter_0.png",
    "box_iter_2.png",
    "box_iter_4.png",
    "box_iter_6.png",
)
_MAILER_FALLBACK = (
    "mailer_iter_1.png",
    "mailer_iter_5.png",
    "mailer_iter_7.png",
    "mailer_iter_8.png",
    "mailer_iter_9.png",
)


def _existing(names: list[str] | tuple[str, ...]) -> list[Path]:
    return [p for name in names if (p := PARCEL_TEX_DIR / name).is_file()]


def load_photo_pools() -> dict[str, list[Path]]:
    """Return ``{"box": [...4], "mailer": [...5]}`` of existing albedo files."""
    box_names: list[str] = list(_BOX_FALLBACK)
    mailer_names: list[str] = list(_MAILER_FALLBACK)
    manifest = PARCEL_TEX_DIR / "manifest.json"
    if manifest.is_file():
        raw = json.loads(manifest.read_text(encoding="utf-8"))
        if raw.get("box_pool"):
            box_names = list(raw["box_pool"])
        if raw.get("mailer_pool"):
            mailer_names = list(raw["mailer_pool"])
        elif raw.get("iter_to_file"):
            box_names = [n for n in raw["iter_to_file"].values() if n.startswith("box_")]
            mailer_names = [n for n in raw["iter_to_file"].values() if n.startswith("mailer_")]
    return {"box": _existing(box_names), "mailer": _existing(mailer_names)}


def choose_parcel_albedos(rng: np.random.Generator) -> dict[str, Path]:
    """Pick one box photo and one mailer photo."""
    pools = load_photo_pools()
    chosen: dict[str, Path] = {}
    if pools["box"]:
        chosen["parcel_box"] = pools["box"][int(rng.integers(0, len(pools["box"])))]
    if pools["mailer"]:
        chosen["mailer"] = pools["mailer"][int(rng.integers(0, len(pools["mailer"])))]
    return chosen
