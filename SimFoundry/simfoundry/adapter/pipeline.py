"""A-period pipeline: library assets + stub VLM → scene package on disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simfoundry.adapter.backends.mesh import FromLibraryBackend
from simfoundry.adapter.backends.vlm import StubVlmBackend
from simfoundry.scene_package import default_scenes_root, load_scene_package
from simfoundry.schema import ScenePackage, TaskSpec

DEFAULT_LAYOUT: dict[str, Any] = {
    "table_frame": {
        "pos": [1.10, 0.0, 0.78],
        "rot_xyzw": [0.0, 0.0, 0.0, 1.0],
        "comment": "Table-top center, z-up. Front edge ~0.80m from G1 at origin.",
    },
    "placements": {
        "counter": {"pos": [0.0, 0.0, -0.39], "kinematic": True},
        "cup": {"pos": [-0.18, -0.12, 0.055]},
        "bowl": {"pos": [-0.16, 0.08, 0.03]},
        "plate": {"pos": [0.08, 0.0, 0.006]},
        "bottle": {"pos": [0.05, -0.28, 0.095]},
    },
}

IDENTITY_XYZW = [0.0, 0.0, 0.0, 1.0]


def _task_to_json(task: TaskSpec) -> dict[str, Any]:
    predicates = []
    for pred in task.predicates:
        item: dict[str, Any] = {"type": pred.type, "a": pred.a, "b": pred.b}
        if pred.threshold is not None:
            item["threshold"] = pred.threshold
        predicates.append(item)
    return {
        "task_id": task.task_id,
        "instruction": task.instruction,
        "predicates": predicates,
        "requires_ee": task.requires_ee,
        "arms": task.arms,
    }


def build_placeholder_kitchen(
    scenes_root: str | Path | None = None,
    scene_id: str = "kitchen_counter_placeholder",
    mesh_backend: FromLibraryBackend | None = None,
    vlm_backend: StubVlmBackend | None = None,
) -> ScenePackage:
    """Write a scene package using A-period stubs. Safe to re-run."""
    scenes_root = Path(scenes_root) if scenes_root is not None else default_scenes_root()
    root = scenes_root / scene_id
    mesh_backend = mesh_backend or FromLibraryBackend()
    vlm_backend = vlm_backend or StubVlmBackend()

    objects = []
    for semantic, placement in DEFAULT_LAYOUT["placements"].items():
        asset = mesh_backend.generate(None, semantic=semantic)
        if asset.primitive is None:
            raise RuntimeError(f"{semantic}: FromLibraryBackend must return a primitive")
        obj = {
            "name": semantic,
            "semantic": semantic,
            **asset.primitive,
            "pos": list(placement["pos"]),
            "rot_xyzw": IDENTITY_XYZW,
            "kinematic": bool(placement.get("kinematic", asset.primitive.get("kinematic", False))),
        }
        objects.append(obj)

    (root / "twin" / "objects").mkdir(parents=True, exist_ok=True)
    (root / "twin" / "collision").mkdir(parents=True, exist_ok=True)
    (root / "twin" / "articulations").mkdir(parents=True, exist_ok=True)
    (root / "twin" / "background").mkdir(parents=True, exist_ok=True)
    (root / "cousins" / "object").mkdir(parents=True, exist_ok=True)
    (root / "cousins" / "scene").mkdir(parents=True, exist_ok=True)
    task_dir = root / "cousins" / "task"
    task_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "scene_id": scene_id,
        "source": "placeholder",
        "units": "m",
        "gravity": [0.0, 0.0, -9.81],
        "up_axis": "z",
        "description": "A-period kitchen counter. YCB mug/bowl/bottle USD + plate primitive.",
    }
    (root / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    layout = {
        "table_frame": DEFAULT_LAYOUT["table_frame"],
        "objects": objects,
    }
    (root / "twin" / "layout.json").write_text(json.dumps(layout, indent=2) + "\n")

    for task in vlm_backend.propose_tasks({}):
        (task_dir / f"{task.task_id}.json").write_text(json.dumps(_task_to_json(task), indent=2) + "\n")

    return load_scene_package(root)
