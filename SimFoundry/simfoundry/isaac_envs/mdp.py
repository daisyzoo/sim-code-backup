"""Custom MDP terms for the kitchen stump env. Import only after AppLauncher."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def root_height_below(
    env: ManagerBasedRLEnv,
    minimum_height: float,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    asset = env.scene[asset_cfg.name]
    return asset.data.root_pos_w.torch[:, 2] < minimum_height


def xy_distance(env: ManagerBasedRLEnv, asset_a: str, asset_b: str) -> torch.Tensor:
    pos_a = env.scene[asset_a].data.root_pos_w.torch[:, :2]
    pos_b = env.scene[asset_b].data.root_pos_w.torch[:, :2]
    return torch.norm(pos_a - pos_b, dim=-1)


def negative_xy_distance(env: ManagerBasedRLEnv, asset_a: str, asset_b: str) -> torch.Tensor:
    return -xy_distance(env, asset_a, asset_b)


def xy_near(
    env: ManagerBasedRLEnv,
    asset_a: str,
    asset_b: str,
    threshold: float,
) -> torch.Tensor:
    return (xy_distance(env, asset_a, asset_b) < threshold).float()
