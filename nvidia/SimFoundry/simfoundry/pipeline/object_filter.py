# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Stage-5 object validity filter used by upsample and --skip-successful.

Streaming a single object writes `stage_info.json` with success=true. Skip-successful must
not treat that as "every object is done": completeness is "all keep-list artifacts exist".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simfoundry.pipeline.stage_utils import parse_iter_index
from simfoundry.utils.processing_utils import dump_json

OBJECT_FILTER_FILENAME = "object_filter.json"

OBJECT_STAGE_ARTIFACTS = {
    "6": ("s6_upsample", lambda cfg, s5, keep: _existing_indices(
        Path(str(cfg.s6_upsample.out_dir)) / "upsampled",
        suffix="_transparent.png",
    )),
    "7": ("s7_mesh", lambda cfg, s5, keep: _existing_indices(
        Path(str(cfg.s7_mesh.out_dir)) / "textured_mesh" / str(cfg.s7_mesh.texture_model),
        suffix="_mesh.glb",
    )),
    "8": ("s8_pose", lambda cfg, s5, keep: _existing_indices(
        Path(str(cfg.s8_pose.out_dir)) / "info",
        suffix=".json",
    )),
}


def s5_dir_from_cfg(cfg) -> Path:
    return Path(str(cfg.s5_scene.out_dir))


def list_s5_objects(s5_dir: str | Path) -> list[dict[str, Any]]:
    obj_dir = Path(s5_dir) / "obj_cat_list"
    if not obj_dir.is_dir():
        return []
    records = []
    for path in sorted(obj_dir.glob("iter_*.json")):
        idx = parse_iter_index(path.stem)
        if idx is None:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue
        records.append(
            {
                "idx": idx,
                "phrase": payload.get("removed_obj_phrase"),
                "is_valid": bool(payload.get("is_valid_removed_obj", False)),
                "path": str(path),
            }
        )
    return records


def object_filter_path(s5_dir: str | Path) -> Path:
    return Path(s5_dir) / OBJECT_FILTER_FILENAME


def load_object_filter(s5_dir: str | Path) -> dict[str, Any] | None:
    path = object_filter_path(s5_dir)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def write_object_filter(
    s5_dir: str | Path,
    *,
    keep_indices: list[int],
    invalid_indices: list[int] | None = None,
    source: str = "s5_auto",
    approved: bool = True,
) -> dict[str, Any]:
    payload = {
        "keep_indices": sorted({int(i) for i in keep_indices}),
        "invalid_indices": sorted({int(i) for i in (invalid_indices or [])}),
        "source": source,
        "approved": bool(approved),
    }
    Path(s5_dir).mkdir(parents=True, exist_ok=True)
    dump_json(payload, str(object_filter_path(s5_dir)))
    return payload


def sync_object_filter_from_s5(s5_dir: str | Path, *, source: str = "s5_auto", approved: bool = True) -> dict[str, Any]:
    records = list_s5_objects(s5_dir)
    keep = [row["idx"] for row in records if row["is_valid"]]
    invalid = [row["idx"] for row in records if not row["is_valid"]]
    return write_object_filter(
        s5_dir,
        keep_indices=keep,
        invalid_indices=invalid,
        source=source,
        approved=approved,
    )


def resolve_keep_indices(
    s5_dir: str | Path,
    *,
    include_invalid: bool = False,
    require_review: bool = False,
) -> set[int]:
    records = list_s5_objects(s5_dir)
    all_idx = {row["idx"] for row in records}
    valid_idx = {row["idx"] for row in records if row["is_valid"]}
    filt = load_object_filter(s5_dir)
    if require_review and (filt is None or not filt.get("approved")):
        raise RuntimeError(
            f"s6_upsample.require_review=true but {object_filter_path(s5_dir)} is missing "
            "or not approved. Run "
            "`python scripts/pipeline/A_reconstruction/stages/5c_filter_objects.py` "
            "(or 5b_visualize_decomposition.py, then 5c --auto) before upsample."
        )
    if filt is not None and "keep_indices" in filt:
        return {int(i) for i in filt["keep_indices"]} & all_idx
    if include_invalid:
        return all_idx
    return valid_idx


def should_upsample_index(s5_dir: str | Path, idx: int, *, include_invalid: bool = False) -> bool:
    keep = resolve_keep_indices(s5_dir, include_invalid=include_invalid, require_review=False)
    records = list_s5_objects(s5_dir)
    if not records:
        return True
    return int(idx) in keep


def resolve_keep_indices_from_cfg(cfg) -> set[int]:
    s6 = getattr(cfg, "s6_upsample", None)
    include_invalid = bool(s6.get("include_invalid", False)) if s6 is not None else False
    require_review = bool(s6.get("require_review", False)) if s6 is not None else False
    return resolve_keep_indices(
        s5_dir_from_cfg(cfg),
        include_invalid=include_invalid,
        require_review=require_review,
    )


def _existing_indices(directory: Path, *, suffix: str) -> set[int]:
    if not directory.is_dir():
        return set()
    found: set[int] = set()
    for path in directory.iterdir():
        if not path.is_file() or not path.name.endswith(suffix):
            continue
        idx = parse_iter_index(path.name.removesuffix(suffix))
        if idx is not None:
            found.add(idx)
    return found


def produced_object_indices(cfg, stage_id: str) -> set[int] | None:
    spec = OBJECT_STAGE_ARTIFACTS.get(str(stage_id))
    if spec is None:
        return None
    _, reader = spec
    return reader(cfg, None, None)


def object_stage_is_complete(cfg, stage_id: str) -> bool:
    """True when every keep-list object has an artifact for this stage."""
    records = list_s5_objects(s5_dir_from_cfg(cfg))
    if not records:
        return False
    try:
        expected = resolve_keep_indices_from_cfg(cfg)
    except RuntimeError:
        return False
    produced = produced_object_indices(cfg, stage_id)
    if produced is None:
        return False
    if not expected:
        return True
    return expected.issubset(produced)
