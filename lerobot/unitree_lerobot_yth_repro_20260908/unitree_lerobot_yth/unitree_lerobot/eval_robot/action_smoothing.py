"""Causal smoothing and rate limiting for absolute joint-position actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np


def parse_joint_limits(value: str | Sequence[float], expected_dim: int, name: str) -> np.ndarray:
    """Parse a comma-separated per-joint limit vector."""
    if isinstance(value, str):
        values = [float(item.strip()) for item in value.split(",") if item.strip()]
    else:
        values = [float(item) for item in value]
    if len(values) != expected_dim:
        raise ValueError(f"{name} must contain {expected_dim} values, got {len(values)}")
    result = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(result)) or np.any(result <= 0.0):
        raise ValueError(f"{name} values must all be finite and greater than zero")
    return result


@dataclass(frozen=True)
class ActionSmoothingConfig:
    enabled: bool
    frequency: float
    arm_dof: int
    waist_dof: int
    arm_cutoff_hz: float
    waist_cutoff_hz: float
    chunk_blend_frames: int
    velocity_limits: str | Sequence[float]
    acceleration_limits: str | Sequence[float]

    @property
    def controlled_dof(self) -> int:
        return self.arm_dof + self.waist_dof

    def validate(self) -> None:
        if self.frequency <= 0.0:
            raise ValueError("action smoothing frequency must be greater than zero")
        if self.arm_dof <= 0 or self.waist_dof < 0:
            raise ValueError("action smoothing requires arm_dof > 0 and waist_dof >= 0")
        if not self.enabled:
            return
        if self.arm_cutoff_hz <= 0.0 or (self.waist_dof and self.waist_cutoff_hz <= 0.0):
            raise ValueError("action smoothing cutoff frequencies must be greater than zero")
        if self.chunk_blend_frames < 0:
            raise ValueError("action_smoothing_chunk_blend_frames must be >= 0")
        parse_joint_limits(self.velocity_limits, self.controlled_dof, "action_velocity_limits")
        parse_joint_limits(
            self.acceleration_limits,
            self.controlled_dof,
            "action_acceleration_limits",
        )


class JointActionSmoother:
    """Stitch action chunks, low-pass targets, and bound velocity/acceleration.

    State is initialized from the measured robot pose. The nominal control
    period is deliberately used for rate limiting, so a long inference pause
    cannot turn into permission for a large target jump.
    """

    def __init__(self, config: ActionSmoothingConfig) -> None:
        config.validate()
        self.config = config
        self.dt = 1.0 / config.frequency
        if not config.enabled:
            self.alpha = np.ones(config.controlled_dof, dtype=np.float64)
            self.velocity_limits = np.full(config.controlled_dof, np.inf, dtype=np.float64)
            self.acceleration_limits = np.full(config.controlled_dof, np.inf, dtype=np.float64)
            self._filtered_q = None
            self._command_q = None
            self._command_v = None
            self._chunk_offset = None
            self._chunk_blend_index = 0
            self._last_inference_index = None
            return
        cutoff = np.full(config.controlled_dof, config.arm_cutoff_hz, dtype=np.float64)
        if config.waist_dof:
            cutoff[config.arm_dof :] = config.waist_cutoff_hz
        self.alpha = 1.0 - np.exp(-2.0 * np.pi * cutoff * self.dt)
        self.velocity_limits = parse_joint_limits(
            config.velocity_limits,
            config.controlled_dof,
            "action_velocity_limits",
        )
        self.acceleration_limits = parse_joint_limits(
            config.acceleration_limits,
            config.controlled_dof,
            "action_acceleration_limits",
        )
        self._filtered_q: np.ndarray | None = None
        self._command_q: np.ndarray | None = None
        self._command_v: np.ndarray | None = None
        self._chunk_offset: np.ndarray | None = None
        self._chunk_blend_index = 0
        self._last_inference_index: int | None = None

    @property
    def initialized(self) -> bool:
        return self._command_q is not None

    def reset(self, measured_q: Sequence[float]) -> None:
        measured = np.asarray(measured_q, dtype=np.float64).reshape(-1)
        if measured.shape != (self.config.controlled_dof,):
            raise ValueError(
                f"measured action-smoothing state must have shape "
                f"({self.config.controlled_dof},), got {measured.shape}"
            )
        if not np.all(np.isfinite(measured)):
            raise ValueError("measured action-smoothing state contains NaN or Inf")
        self._filtered_q = measured.copy()
        self._command_q = measured.copy()
        self._command_v = np.zeros_like(measured)
        self._chunk_offset = None
        self._chunk_blend_index = 0
        self._last_inference_index = None

    def _is_chunk_boundary(self, metadata: dict[str, Any] | None, chunk_refill: bool) -> bool:
        inference_index = None if metadata is None else metadata.get("inference_index")
        if inference_index is not None:
            inference_index = int(inference_index)
            boundary = (
                self._last_inference_index is not None
                and inference_index != self._last_inference_index
            )
            self._last_inference_index = inference_index
            return boundary
        return bool(chunk_refill and self.initialized)

    def _stitch_chunk(self, raw_q: np.ndarray, chunk_boundary: bool) -> tuple[np.ndarray, float]:
        frames = self.config.chunk_blend_frames
        if chunk_boundary and frames > 0:
            self._chunk_offset = self._command_q - raw_q
            self._chunk_blend_index = 0
        if self._chunk_offset is None or frames <= 0:
            return raw_q.copy(), 0.0

        if frames == 1:
            progress = 0.0
        else:
            progress = min(1.0, self._chunk_blend_index / (frames - 1))
        smoothstep = progress * progress * (3.0 - 2.0 * progress)
        weight = 1.0 - smoothstep
        stitched = raw_q + weight * self._chunk_offset
        self._chunk_blend_index += 1
        if self._chunk_blend_index >= frames:
            self._chunk_offset = None
        return stitched, float(weight)

    def process(
        self,
        raw_q: Sequence[float],
        *,
        measured_q: Sequence[float],
        metadata: dict[str, Any] | None = None,
        chunk_refill: bool = False,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        raw = np.asarray(raw_q, dtype=np.float64).reshape(-1)
        if raw.shape != (self.config.controlled_dof,):
            raise ValueError(
                f"action smoothing expected {self.config.controlled_dof} targets, got {raw.shape}"
            )
        if not np.all(np.isfinite(raw)):
            raise ValueError("policy action contains NaN or Inf")
        if not self.config.enabled:
            return raw.astype(np.float32), {"enabled": False}
        if not self.initialized:
            self.reset(measured_q)

        chunk_boundary = self._is_chunk_boundary(metadata, chunk_refill)
        stitched, blend_weight = self._stitch_chunk(raw, chunk_boundary)
        filtered = self.alpha * stitched + (1.0 - self.alpha) * self._filtered_q

        position_error = filtered - self._command_q
        desired_v = position_error / self.dt
        # Begin decelerating early enough to approach a stationary absolute
        # target without the large overshoot produced by a plain acceleration
        # clip. The one-step velocity remains an additional no-crossing bound.
        half_accel_step = 0.5 * self.acceleration_limits * self.dt
        braking_speed = (
            np.sqrt(
                half_accel_step * half_accel_step
                + 2.0 * self.acceleration_limits * np.abs(position_error)
            )
            - half_accel_step
        )
        bounded_speed = np.minimum.reduce(
            (np.abs(desired_v), self.velocity_limits, braking_speed)
        )
        velocity_limited = np.copysign(bounded_speed, position_error)
        min_v = self._command_v - self.acceleration_limits * self.dt
        max_v = self._command_v + self.acceleration_limits * self.dt
        command_v = np.clip(velocity_limited, min_v, max_v)
        command_v = np.clip(command_v, -self.velocity_limits, self.velocity_limits)
        command_q = self._command_q + command_v * self.dt

        diagnostics = {
            "enabled": True,
            "chunk_boundary": chunk_boundary,
            "chunk_blend_weight": blend_weight,
            "stitched_action": stitched.astype(np.float32).tolist(),
            "filtered_action": filtered.astype(np.float32).tolist(),
            "command_velocity": command_v.astype(np.float32).tolist(),
            "velocity_limited": bool(np.any(np.abs(desired_v) > self.velocity_limits + 1e-12)),
            "acceleration_limited": bool(np.any(np.abs(command_v - velocity_limited) > 1e-12)),
        }
        self._filtered_q = filtered
        self._command_q = command_q
        self._command_v = command_v
        return command_q.astype(np.float32), diagnostics
