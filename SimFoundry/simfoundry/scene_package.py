"""Load and validate a SimFoundry scene package from disk."""

from __future__ import annotations

import json
from pathlib import Path

from simfoundry.schema import Pose, Predicate, SceneMeta, SceneObject, ScenePackage, TaskSpec


def _as_xyz(value: list[float]) -> tuple[float, float, float]:
    if len(value) != 3:
        raise ValueError(f"expected xyz of length 3, got {value}")
    return float(value[0]), float(value[1]), float(value[2])


def _as_xyzw(value: list[float] | None) -> tuple[float, float, float, float]:
    if value is None:
        return (0.0, 0.0, 0.0, 1.0)
    if len(value) != 4:
        raise ValueError(f"expected xyzw of length 4, got {value}")
    return float(value[0]), float(value[1]), float(value[2]), float(value[3])


def _as_color(value: list[float] | None) -> tuple[float, float, float]:
    if value is None:
        return (0.7, 0.7, 0.7)
    return _as_xyz(value)


def load_scene_package(root: str | Path) -> ScenePackage:
    root = Path(root).resolve()
    meta_raw = json.loads((root / "meta.json").read_text())
    if "robot_dof" in meta_raw:
        raise ValueError(f"{root}: scene meta must not contain robot_dof")
    meta = SceneMeta(
        scene_id=meta_raw["scene_id"],
        source=meta_raw["source"],
        units=meta_raw.get("units", "m"),
        gravity=_as_xyz(meta_raw.get("gravity", [0.0, 0.0, -9.81])),
        up_axis=meta_raw.get("up_axis", "z"),
        description=meta_raw.get("description", ""),
    )
    layout_raw = json.loads((root / "twin" / "layout.json").read_text())
    table = layout_raw["table_frame"]
    table_frame = Pose(pos=_as_xyz(table["pos"]), rot_xyzw=_as_xyzw(table.get("rot_xyzw")))
    objects = []
    for item in layout_raw["objects"]:
        size = item.get("size")
        objects.append(
            SceneObject(
                name=item["name"],
                semantic=item["semantic"],
                shape=item["shape"],
                pos=_as_xyz(item["pos"]),
                rot_xyzw=_as_xyzw(item.get("rot_xyzw")),
                size=_as_xyz(size) if size is not None else None,
                radius=item.get("radius"),
                height=item.get("height"),
                mass=float(item.get("mass", 0.1)),
                friction=float(item.get("friction", 0.5)),
                kinematic=bool(item.get("kinematic", False)),
                color=_as_color(item.get("color")),
                usd_path=item.get("usd_path"),
            )
        )
    tasks = []
    task_dir = root / "cousins" / "task"
    if task_dir.is_dir():
        for path in sorted(task_dir.glob("*.json")):
            raw = json.loads(path.read_text())
            predicates = tuple(
                Predicate(
                    type=p["type"],
                    a=p["a"],
                    b=p["b"],
                    threshold=p.get("threshold"),
                )
                for p in raw.get("predicates", [])
            )
            tasks.append(
                TaskSpec(
                    task_id=raw["task_id"],
                    instruction=raw.get("instruction", raw["task_id"]),
                    predicates=predicates,
                    requires_ee=raw["requires_ee"],
                    arms=raw.get("arms", "bimanual"),
                )
            )
    return ScenePackage(
        root=str(root),
        meta=meta,
        table_frame=table_frame,
        objects=tuple(objects),
        tasks=tuple(tasks),
    )


def filter_tasks(package: ScenePackage, requires_ee: str = "stump") -> tuple[TaskSpec, ...]:
    return tuple(t for t in package.tasks if t.requires_ee == requires_ee)


def default_scenes_root() -> Path:
    return Path(__file__).resolve().parents[1] / "scenes"


def load_named_scene(scene_id: str, scenes_root: str | Path | None = None) -> ScenePackage:
    root = Path(scenes_root) if scenes_root is not None else default_scenes_root()
    return load_scene_package(root / scene_id)
