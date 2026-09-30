# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

import pytest

from simfoundry.pipeline.object_filter import (
    object_stage_is_complete,
    resolve_keep_indices,
    sync_object_filter_from_s5,
    write_object_filter,
)
from simfoundry.pipeline.hunyuan_weights import hunyuan_local_dir, hy3dgen_root


class _Node:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key, default=None):
        return getattr(self, key, default)


def _write_s5(tmp_path):
    s5 = tmp_path / "s5_scene"
    cat = s5 / "obj_cat_list"
    cat.mkdir(parents=True)
    for idx, valid, name in ((1, True, "pear"), (2, False, "glass"), (3, True, "apple")):
        (cat / f"iter_{idx}.json").write_text(
            json.dumps({"is_valid_removed_obj": valid, "removed_obj_phrase": name}),
            encoding="utf-8",
        )
    return s5


def test_auto_keep_indices_drop_invalid(tmp_path):
    s5 = _write_s5(tmp_path)
    assert resolve_keep_indices(s5, include_invalid=False) == {1, 3}
    assert resolve_keep_indices(s5, include_invalid=True) == {1, 2, 3}


def test_object_filter_overrides_validity(tmp_path):
    s5 = _write_s5(tmp_path)
    write_object_filter(s5, keep_indices=[2], invalid_indices=[1, 3], source="human", approved=True)
    assert resolve_keep_indices(s5, include_invalid=False) == {2}


def test_require_review_without_filter_raises(tmp_path):
    s5 = _write_s5(tmp_path)
    with pytest.raises(RuntimeError, match="require_review"):
        resolve_keep_indices(s5, require_review=True)


def test_sync_object_filter_from_s5(tmp_path):
    s5 = _write_s5(tmp_path)
    payload = sync_object_filter_from_s5(s5)
    assert payload["keep_indices"] == [1, 3]
    assert payload["invalid_indices"] == [2]
    assert payload["approved"] is True


def test_object_stage_complete_ignores_invalid(tmp_path):
    s5 = _write_s5(tmp_path)
    up = tmp_path / "s6_upsample" / "upsampled"
    up.mkdir(parents=True)
    (up / "iter_1_transparent.png").write_bytes(b"x")
    (up / "iter_3_transparent.png").write_bytes(b"x")
    cfg = _Node(
        s5_scene=_Node(out_dir=str(s5)),
        s6_upsample=_Node(out_dir=str(tmp_path / "s6_upsample"), include_invalid=False, require_review=False),
        s7_mesh=_Node(out_dir=str(tmp_path / "s7_mesh"), texture_model="hunyuan"),
        s8_pose=_Node(out_dir=str(tmp_path / "s8_pose")),
    )
    assert object_stage_is_complete(cfg, "6") is True
    (up / "iter_1_transparent.png").unlink()
    assert object_stage_is_complete(cfg, "6") is False


def test_hy3dgen_paths_share_one_tree(monkeypatch, tmp_path):
    monkeypatch.setenv("HY3DGEN_MODELS", str(tmp_path / "hy3dgen"))
    assert hunyuan_local_dir() == tmp_path / "hy3dgen" / "tencent" / "Hunyuan3D-2.1"
    assert hy3dgen_root() == tmp_path / "hy3dgen"
