"""Isaac Lab environments. Import only after AppLauncher has started."""

from __future__ import annotations

import gymnasium as gym

gym.register(
    id="SimFoundry-KitchenCounter-G1-Stump",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.kitchen_env_cfg:KitchenCounterEnvCfg",
    },
)
gym.register(
    id="SimFoundry-IndoorLab-G1-Stump",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.indoor_lab_env_cfg:IndoorLabEnvCfg",
    },
)
gym.register(
    id="SimFoundry-SortingStation-G1-Stump",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.sorting_env_cfg:SortingStationEnvCfg",
    },
)
