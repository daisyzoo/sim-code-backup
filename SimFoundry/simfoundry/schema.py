"""Scene-package dataclasses. No robot_dof field by design."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

RequiresEE = Literal["stump", "gripper", "dexhand"]
ShapeKind = Literal["cuboid", "cylinder", "usd"]


@dataclass(frozen=True)
class Pose:
    pos: tuple[float, float, float]
    rot_xyzw: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)


@dataclass(frozen=True)
class SceneObject:
    name: str
    semantic: str
    shape: ShapeKind
    pos: tuple[float, float, float]
    rot_xyzw: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    size: tuple[float, float, float] | None = None
    radius: float | None = None
    height: float | None = None
    mass: float = 0.1
    friction: float = 0.5
    kinematic: bool = False
    color: tuple[float, float, float] = (0.7, 0.7, 0.7)
    # Relative to SimFoundry/ when shape == "usd" (YCB / authored mesh).
    usd_path: str | None = None

    def __post_init__(self) -> None:
        if self.shape == "cuboid" and self.size is None:
            raise ValueError(f"{self.name}: cuboid needs size [x, y, z]")
        if self.shape == "cylinder" and (self.radius is None or self.height is None):
            raise ValueError(f"{self.name}: cylinder needs radius and height")
        if self.shape == "usd" and not self.usd_path:
            raise ValueError(f"{self.name}: usd shape needs usd_path")

@dataclass(frozen=True)
class Predicate:
    type: str
    a: str
    b: str
    threshold: float | None = None


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    instruction: str
    predicates: tuple[Predicate, ...]
    requires_ee: RequiresEE
    arms: str = "bimanual"


@dataclass(frozen=True)
class SceneMeta:
    scene_id: str
    source: str
    units: str = "m"
    gravity: tuple[float, float, float] = (0.0, 0.0, -9.81)
    up_axis: str = "z"
    description: str = ""

    def __post_init__(self) -> None:
        if "robot_dof" in self.__dict__:
            raise ValueError("scene meta must not include robot_dof")


@dataclass(frozen=True)
class ScenePackage:
    root: str
    meta: SceneMeta
    table_frame: Pose
    objects: tuple[SceneObject, ...]
    tasks: tuple[TaskSpec, ...]
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def scene_id(self) -> str:
        return self.meta.scene_id
