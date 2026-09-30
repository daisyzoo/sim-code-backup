"""A-period VLM stub: return the three stump kitchen tasks plus a dexhand placeholder."""

from __future__ import annotations

from typing import Any

from simfoundry.adapter.backends.base import VlmBackend
from simfoundry.schema import Predicate, ScenePackage, TaskSpec

KITCHEN_TASKS: tuple[TaskSpec, ...] = (
    TaskSpec(
        task_id="approach_counter",
        instruction="Walk up to the kitchen counter and stand still.",
        predicates=(Predicate(type="Near", a="pelvis", b="counter", threshold=0.55),),
        requires_ee="stump",
        arms="bimanual",
    ),
    TaskSpec(
        task_id="reach_cup",
        instruction="Reach the right arm toward the cup on the kitchen counter.",
        predicates=(Predicate(type="Near", a="right_ee", b="cup", threshold=0.12),),
        requires_ee="stump",
        arms="bimanual",
    ),
    TaskSpec(
        task_id="push_cup_to_bowl",
        instruction="Push the cup toward the bowl on the kitchen counter.",
        predicates=(Predicate(type="Near", a="cup", b="bowl", threshold=0.12),),
        requires_ee="stump",
        arms="bimanual",
    ),
    TaskSpec(
        task_id="pick_cup",
        instruction="Pick up the cup from the kitchen counter.",
        predicates=(Predicate(type="Lifted", a="cup", b="counter", threshold=0.08),),
        requires_ee="stump",
        arms="right",
    ),
    TaskSpec(
        task_id="place_cup_in_bowl",
        instruction="Pick up the cup and place it in the bowl.",
        predicates=(Predicate(type="In", a="cup", b="bowl"),),
        requires_ee="dexhand",
        arms="bimanual",
    ),
)


class StubVlmBackend(VlmBackend):
    def propose_tasks(self, scene: ScenePackage | dict[str, Any]) -> list[TaskSpec]:
        return list(KITCHEN_TASKS)
