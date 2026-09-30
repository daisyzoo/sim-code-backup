"""Map scene_id → env cfg class + embodiment metadata for data collection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Type

from isaaclab.envs import ManagerBasedRLEnvCfg

from simfoundry.embodiment import EMBODIMENT_ID, EMBODIMENT_ID_U1, G1_23DOF_JOINT_NAMES
from simfoundry.robots import G1_U1_23DOF_JOINT_NAMES


@dataclass(frozen=True)
class SceneEnvSpec:
    scene_id: str
    env_cfg_cls: Type[ManagerBasedRLEnvCfg]
    embodiment_id: str
    joint_names: tuple[str, ...]
    default_out_dir: str


def _kitchen() -> Type[ManagerBasedRLEnvCfg]:
    from simfoundry.isaac_envs.kitchen_env_cfg import KitchenCounterEnvCfg

    return KitchenCounterEnvCfg


def _indoor() -> Type[ManagerBasedRLEnvCfg]:
    from simfoundry.isaac_envs.indoor_lab_env_cfg import IndoorLabEnvCfg

    return IndoorLabEnvCfg


def _sorting() -> Type[ManagerBasedRLEnvCfg]:
    from simfoundry.isaac_envs.sorting_env_cfg import SortingStationEnvCfg

    return SortingStationEnvCfg


SCENE_ENV_REGISTRY: dict[str, SceneEnvSpec] = {
    "kitchen_counter_placeholder": SceneEnvSpec(
        scene_id="kitchen_counter_placeholder",
        env_cfg_cls=_kitchen(),
        embodiment_id=EMBODIMENT_ID,
        joint_names=G1_23DOF_JOINT_NAMES,
        default_out_dir="datasets/kitchen_counter_placeholder",
    ),
    "indoor_lab_g1_23": SceneEnvSpec(
        scene_id="indoor_lab_g1_23",
        env_cfg_cls=_indoor(),
        embodiment_id=EMBODIMENT_ID,
        joint_names=G1_23DOF_JOINT_NAMES,
        default_out_dir="datasets/indoor_lab_g1_23",
    ),
    "sorting_station_g1_23": SceneEnvSpec(
        scene_id="sorting_station_g1_23",
        env_cfg_cls=_sorting(),
        embodiment_id=EMBODIMENT_ID_U1,
        joint_names=G1_U1_23DOF_JOINT_NAMES,
        default_out_dir="datasets/sorting_station_g1_23",
    ),
}


def resolve_scene_env(scene_id: str) -> SceneEnvSpec:
    if scene_id not in SCENE_ENV_REGISTRY:
        known = ", ".join(sorted(SCENE_ENV_REGISTRY))
        raise KeyError(f"unknown scene_id={scene_id!r}; known: {known}")
    return SCENE_ENV_REGISTRY[scene_id]
