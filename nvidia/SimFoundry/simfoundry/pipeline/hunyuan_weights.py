# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Local Hunyuan3D / DINOv2 weight locations shared by shape, paint, and install prefetch.

Shape generation (`smart_load_model`) already reads `~/.cache/hy3dgen/tencent/Hunyuan3D-2.1/`.
Paint used Hugging Face hub cache, so the same ~15 GB repo was fetched twice. Point both at
this directory, and treat a folder that has `config.yaml` but no checkpoint as incomplete.
"""

from __future__ import annotations

import os
from pathlib import Path

HUNYUAN_REPO_ID = "tencent/Hunyuan3D-2.1"
DINO_REPO_ID = "facebook/dinov2-giant"
SHAPE_SUBFOLDERS = ("hunyuan3d-dit-v2-1", "hunyuan3d-vae-v2-1")
PAINT_SUBFOLDER = "hunyuan3d-paintpbr-v2-1"
SHAPE_CKPT_NAME = "model.fp16.ckpt"


def hy3dgen_root() -> Path:
    return Path(os.path.expanduser(os.environ.get("HY3DGEN_MODELS", "~/.cache/hy3dgen")))


def hunyuan_local_dir() -> Path:
    return hy3dgen_root() / HUNYUAN_REPO_ID


def dino_local_dir() -> Path:
    return hy3dgen_root() / DINO_REPO_ID


def shape_ckpt_path(subfolder: str) -> Path:
    return hunyuan_local_dir() / subfolder / SHAPE_CKPT_NAME


def shape_weights_complete(subfolder: str) -> bool:
    folder = hunyuan_local_dir() / subfolder
    return (folder / "config.yaml").is_file() and shape_ckpt_path(subfolder).is_file()


def paint_weights_complete() -> bool:
    folder = hunyuan_local_dir() / PAINT_SUBFOLDER
    return (folder / "model_index.json").is_file()


def dino_weights_complete() -> bool:
    folder = dino_local_dir()
    if not folder.is_dir() or not (folder / "config.json").is_file():
        return False
    return any(folder.glob("*.bin")) or any(folder.glob("*.safetensors"))


def _snapshot(repo_id: str, *, local_dir: Path, allow_patterns: list[str] | None = None) -> Path:
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from huggingface_hub import snapshot_download

    kwargs = {
        "repo_id": repo_id,
        "local_dir": str(local_dir),
        "resume_download": True,
    }
    if allow_patterns:
        kwargs["allow_patterns"] = allow_patterns
    try:
        snapshot_download(**kwargs, local_dir_use_symlinks=False)
    except TypeError:
        snapshot_download(**kwargs)
    return local_dir


def prefetch_hunyuan_weights(*, include_paint: bool = True) -> dict[str, str]:
    """Download Hunyuan shape (and paint) weights into the hy3dgen directory."""
    local = hunyuan_local_dir()
    local.mkdir(parents=True, exist_ok=True)
    patterns = [f"{sub}/*" for sub in SHAPE_SUBFOLDERS]
    if include_paint:
        patterns.append(f"{PAINT_SUBFOLDER}/*")
    _snapshot(HUNYUAN_REPO_ID, local_dir=local, allow_patterns=patterns)
    missing = [sub for sub in SHAPE_SUBFOLDERS if not shape_weights_complete(sub)]
    if include_paint and not paint_weights_complete():
        missing.append(PAINT_SUBFOLDER)
    if missing:
        raise FileNotFoundError(f"Hunyuan prefetch finished but still missing: {missing}")
    return {"hunyuan_local_dir": str(local)}


def prefetch_dinov2_giant() -> dict[str, str]:
    """Download facebook/dinov2-giant into the same hy3dgen tree paint can load from."""
    local = dino_local_dir()
    local.mkdir(parents=True, exist_ok=True)
    _snapshot(DINO_REPO_ID, local_dir=local)
    if not dino_weights_complete():
        raise FileNotFoundError(f"DINOv2 prefetch finished but {local} is incomplete")
    return {"dino_local_dir": str(local)}
