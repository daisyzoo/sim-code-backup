"""Standalone PI0.5 Real-Time Chunking runtime for G1 evaluation.

This module is intentionally kept outside the policy implementation so the existing
training and evaluation paths remain unchanged.  It follows LeRobot's RTC inference
algorithm: infer action chunks in a background thread, guide each new denoising
trajectory with the unexecuted prefix of the previous chunk, and replace the action
queue after accounting for actions consumed during inference.
"""

from __future__ import annotations

import logging
import math
import os
import json
import select
import sys
import termios
import time
import traceback
import tty
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any, Callable

import torch
from torch import Tensor, nn

from lerobot.policies.pi05.modeling_pi05 import make_att_2d_masks
from lerobot.processor import PolicyAction, PolicyProcessorPipeline
from lerobot.utils.constants import ACTION, OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PI05RTCConfig:
    """Runtime-only RTC settings.

    ``prefix_attention_schedule`` accepts ``zeros``, ``ones``, ``linear`` or
    ``exp``.  ``exp`` is the recommended smooth handover schedule.
    """

    enabled: bool = True
    # Keep asynchronous queueing/scheduling but optionally disable the RTC
    # flow-matching prefix/Jacobian guidance for an ablation experiment.
    guidance_enabled: bool = True
    # False restores the original identity-Jacobian approximation: use the
    # prefix error directly without differentiating through the denoiser.
    use_autograd_jacobian: bool = True
    execution_horizon: int = 10
    max_guidance_weight: float = 10.0
    prefix_attention_schedule: str = "exp"
    queue_threshold: int = 30
    # While a replacement chunk is being inferred, execute at most this many
    # actions from the old chunk and then hold the last robot target.  Use -1
    # to disable the cap and keep consuming until the new chunk is ready.
    max_actions_during_inference: int = -1
    inference_timeout_s: float = 120.0
    latency_window: int = 100

    def __post_init__(self) -> None:
        schedule = self.prefix_attention_schedule.lower()
        if schedule not in {"zeros", "ones", "linear", "exp"}:
            raise ValueError(
                "prefix_attention_schedule must be one of zeros, ones, linear, exp; "
                f"got {self.prefix_attention_schedule!r}"
            )
        if self.execution_horizon <= 0:
            raise ValueError("execution_horizon must be > 0")
        if self.max_guidance_weight <= 0:
            raise ValueError("max_guidance_weight must be > 0")
        if self.queue_threshold < 0:
            raise ValueError("queue_threshold must be >= 0")
        if self.max_actions_during_inference < -1:
            raise ValueError("max_actions_during_inference must be -1 or >= 0")
        if self.max_actions_during_inference > self.execution_horizon:
            raise ValueError(
                "max_actions_during_inference must not exceed execution_horizon; "
                f"got {self.max_actions_during_inference} > {self.execution_horizon}"
            )
        if self.inference_timeout_s <= 0:
            raise ValueError("inference_timeout_s must be > 0")
        if self.latency_window <= 0:
            raise ValueError("latency_window must be > 0")


class RTCProcessor:
    """Apply RTC prefix guidance to one flow-matching denoising step."""

    def __init__(self, config: PI05RTCConfig) -> None:
        self.config = config

    def get_prefix_weights(self, start: int, end: int, total: int) -> Tensor:
        start = max(0, min(int(start), int(end), int(total)))
        end = max(start, min(int(end), int(total)))
        schedule = self.config.prefix_attention_schedule.lower()

        if schedule == "zeros":
            weights = torch.zeros(total)
            weights[:start] = 1.0
            return weights
        if schedule == "ones":
            weights = torch.zeros(total)
            weights[:end] = 1.0
            return weights

        weights = torch.zeros(total)
        weights[:start] = 1.0
        transition_steps = end - start
        if transition_steps <= 0:
            return weights

        transition = torch.linspace(1, 0, transition_steps + 2)[1:-1]
        if schedule == "exp":
            transition = transition * torch.expm1(transition) / (math.e - 1)
        weights[start:end] = transition
        return weights

    def denoise_step(
        self,
        *,
        x_t: Tensor,
        prev_chunk_left_over: Tensor | None,
        inference_delay: int,
        time_value: Tensor,
        original_denoise_step: Callable[[Tensor], Tensor],
    ) -> Tensor:
        """Return the original or RTC-guided velocity for the current latent."""
        # This preserves the asynchronous RTC queue, real consumed-frame
        # alignment, and chunk replacement behavior, while removing every
        # flow-matching/Jacobian constraint on the newly inferred chunk.
        if (
            not self.config.guidance_enabled
            or prev_chunk_left_over is None
            or prev_chunk_left_over.numel() == 0
        ):
            return original_denoise_step(x_t)

        x_t = x_t.clone().detach()
        squeezed = x_t.ndim == 2
        if squeezed:
            x_t = x_t.unsqueeze(0)

        prev = prev_chunk_left_over
        if prev.ndim == 2:
            prev = prev.unsqueeze(0)
        prev = prev.to(device=x_t.device, dtype=x_t.dtype)

        batch_size, chunk_size, action_dim = x_t.shape
        execution_horizon = min(self.config.execution_horizon, prev.shape[1], chunk_size)
        padded = torch.zeros_like(x_t)
        copy_batch = min(batch_size, prev.shape[0])
        copy_steps = min(chunk_size, prev.shape[1])
        copy_dim = min(action_dim, prev.shape[2])
        padded[:copy_batch, :copy_steps, :copy_dim] = prev[:copy_batch, :copy_steps, :copy_dim]
        prev = padded

        weights = self.get_prefix_weights(inference_delay, execution_horizon, chunk_size).to(
            device=x_t.device, dtype=x_t.dtype
        )[None, :, None]

        expanded_time = time_value
        while expanded_time.ndim < x_t.ndim:
            expanded_time = expanded_time.unsqueeze(-1)

        if self.config.use_autograd_jacobian:
            # Compute the VJP of x_1 = x_t - t*v_theta(x_t). This is
            # inference-time autodiff only and does not update policy weights.
            x_t = x_t.requires_grad_(True)
            with torch.enable_grad():
                v_t = original_denoise_step(x_t)
                x1_t = x_t - expanded_time * v_t
                error = (prev - x1_t) * weights
                correction = torch.autograd.grad(
                    x1_t,
                    x_t,
                    grad_outputs=error.detach(),
                    retain_graph=False,
                )[0]
        else:
            # This is mathematically equivalent to the original local RTC
            # implementation's effective behavior: v_t was produced before
            # x_t required gradients, so the VJP was the identity and
            # correction == error. Compute it directly to avoid the autograd
            # graph and its latency.
            v_t = original_denoise_step(x_t)
            x1_t = x_t - expanded_time * v_t
            error = (prev - x1_t) * weights
            correction = error

        # The local PI0.5 flow time runs from 1 -> 0.  These equations are the
        # reference RTC guidance schedule expressed in that convention.
        tau = 1 - time_value
        max_weight = torch.as_tensor(
            self.config.max_guidance_weight, device=x_t.device, dtype=x_t.dtype
        )
        one_minus_tau_sq = (1 - tau) ** 2
        inv_r2 = (one_minus_tau_sq + tau**2) / one_minus_tau_sq
        guidance_weight = torch.nan_to_num(
            ((1 - tau) / tau) * inv_r2,
            posinf=float(self.config.max_guidance_weight),
            neginf=0.0,
        ).clamp(min=0.0, max=float(self.config.max_guidance_weight))
        while guidance_weight.ndim < correction.ndim:
            guidance_weight = guidance_weight.unsqueeze(-1)

        result = v_t - guidance_weight * correction
        return result.squeeze(0) if squeezed else result


class RTCActionQueue:
    """Thread-safe paired queue for normalized and robot-space actions."""

    def __init__(self) -> None:
        self._original: Tensor | None = None
        self._processed: Tensor | None = None
        self._metadata: list[dict[str, Any]] | None = None
        self._index = 0
        self._lock = Lock()

    def __len__(self) -> int:
        return self.qsize()

    def clear(self) -> None:
        with self._lock:
            self._original = None
            self._processed = None
            self._metadata = None
            self._index = 0

    def qsize(self) -> int:
        with self._lock:
            if self._processed is None:
                return 0
            return max(0, len(self._processed) - self._index)

    def get_action_index(self) -> int:
        with self._lock:
            return self._index

    def get(self) -> Tensor | None:
        action, _ = self.get_with_metadata()
        return action

    def get_with_metadata(self) -> tuple[Tensor | None, dict[str, Any] | None]:
        with self._lock:
            if self._processed is None or self._index >= len(self._processed):
                return None, None
            action = self._processed[self._index].clone()
            metadata = (
                None if self._metadata is None else dict(self._metadata[self._index])
            )
            self._index += 1
            return action, metadata

    def get_left_over(self) -> Tensor | None:
        with self._lock:
            if self._original is None or self._index >= len(self._original):
                return None
            return self._original[self._index :].clone()

    def merge(
        self,
        original: Tensor,
        processed: Tensor,
        consumed_during_inference: int,
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        with self._lock:
            delay = max(0, min(int(consumed_during_inference), len(original), len(processed)))
            self._original = original[delay:].detach().clone()
            self._processed = processed[delay:].detach().clone()
            self._metadata = (
                None if metadata is None else [dict(item) for item in metadata[delay:]]
            )
            self._index = 0


class _LatencyTracker:
    def __init__(self, maxlen: int) -> None:
        self._values: deque[float] = deque(maxlen=maxlen)

    def add(self, latency_s: float) -> None:
        if latency_s >= 0:
            self._values.append(float(latency_s))

    def maximum(self) -> float:
        return max(self._values, default=0.0)


def _clone_batch(batch: dict[str, Any]) -> dict[str, Any]:
    cloned: dict[str, Any] = {}
    for key, value in batch.items():
        if isinstance(value, Tensor):
            cloned[key] = value.detach().clone()
        elif isinstance(value, list):
            cloned[key] = list(value)
        else:
            cloned[key] = value
    return cloned


def sample_actions_with_rtc(
    model: nn.Module,
    images: list[Tensor],
    img_masks: list[Tensor],
    tokens: Tensor,
    masks: Tensor,
    rtc_processor: RTCProcessor,
    *,
    inference_delay: int,
    prev_chunk_left_over: Tensor | None,
    noise: Tensor | None = None,
    num_steps: int | None = None,
) -> Tensor:
    """Run the local PI0.5 sampler with optional RTC guidance."""
    total_start = time.perf_counter()
    if num_steps is None:
        num_steps = model.config.num_inference_steps

    batch_size = tokens.shape[0]
    device = tokens.device
    if noise is None:
        noise = model.sample_noise(
            (batch_size, model.config.chunk_size, model.config.max_action_dim),
            device,
        )

    with torch.no_grad():
        prefix_start = time.perf_counter()
        prefix_embs, prefix_pad_masks, prefix_att_masks = model.embed_prefix(
            images, img_masks, tokens, masks
        )
        prefix_dtype = (
            model.paligemma_with_expert.paligemma.language_model.layers[0]
            .self_attn.q_proj.weight.dtype
        )
        prefix_embs = prefix_embs.to(dtype=prefix_dtype)
        prefix_att_2d_masks = make_att_2d_masks(prefix_pad_masks, prefix_att_masks)
        prefix_position_ids = torch.cumsum(prefix_pad_masks, dim=1) - 1
        prefix_att_2d_masks_4d = model._prepare_attention_masks_4d(  # noqa: SLF001
            prefix_att_2d_masks, dtype=prefix_embs.dtype
        )
        _, past_key_values = model.paligemma_with_expert.forward(
            attention_mask=prefix_att_2d_masks_4d,
            position_ids=prefix_position_ids,
            past_key_values=None,
            inputs_embeds=[prefix_embs, None],
            use_cache=True,
        )

        dt = torch.tensor(-1.0 / num_steps, dtype=torch.float32, device=device)
        x_t = noise
        flow_time = torch.tensor(1.0, dtype=torch.float32, device=device)
        denoise_start = time.perf_counter()
        denoise_steps = 0
        while flow_time >= -dt / 2:
            expanded_time = flow_time.expand(batch_size)

            def original_denoise_step(input_x_t: Tensor) -> Tensor:
                return model.denoise_step(
                    prefix_pad_masks,
                    past_key_values,
                    input_x_t,
                    expanded_time,
                )

            v_t = rtc_processor.denoise_step(
                x_t=x_t,
                prev_chunk_left_over=prev_chunk_left_over,
                inference_delay=inference_delay,
                time_value=expanded_time,
                original_denoise_step=original_denoise_step,
            )
            x_t = x_t + dt * v_t
            flow_time += dt
            denoise_steps += 1

    model._last_sample_actions_profile = {
        "total_s": time.perf_counter() - total_start,
        "prefix_s": denoise_start - prefix_start,
        "denoise_total_s": time.perf_counter() - denoise_start,
        "denoise_steps": denoise_steps,
    }
    return x_t


class PI05RTCPolicyAdapter(nn.Module):
    """Expose asynchronous RTC inference through the existing eval policy API."""

    def __init__(
        self,
        policy: nn.Module,
        postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction],
        rtc_config: PI05RTCConfig,
        frequency: float,
        max_episode_wall_time_s: float = 0.0,
        snapshot_dir: str = "",
        external_stop_requested: Callable[[], bool] | None = None,
        enable_terminal_control: bool = True,
    ) -> None:
        super().__init__()
        if getattr(policy.config, "type", None) != "pi05":
            raise TypeError("PI05RTCPolicyAdapter only supports policy.type='pi05'")
        if rtc_config.queue_threshold >= policy.config.chunk_size:
            raise ValueError(
                f"queue_threshold ({rtc_config.queue_threshold}) must be smaller than "
                f"PI0.5 chunk_size ({policy.config.chunk_size})"
            )

        self.policy = policy
        self.config = policy.config
        self.postprocessor = postprocessor
        self.rtc_config = rtc_config
        self.frequency = float(frequency)
        self.max_episode_wall_time_s = float(max_episode_wall_time_s)
        self.snapshot_dir = Path(snapshot_dir).expanduser() if snapshot_dir else None
        self.external_stop_requested = external_stop_requested
        self.enable_terminal_control = bool(enable_terminal_control)
        if self.max_episode_wall_time_s < 0.0:
            raise ValueError("max_episode_wall_time_s must be >= 0")
        self.rtc_processor = RTCProcessor(rtc_config)
        self._action_queue = RTCActionQueue()

        self._latest_batch: dict[str, Any] | None = None
        self._latest_snapshot_observation: dict[str, Any] | None = None
        self._batch_lock = Lock()
        self._reset_lock = Lock()
        self._inference_budget_lock = Lock()
        self._observation_ready = Event()
        self._active = Event()
        self._inference_active = Event()
        self._shutdown = Event()
        self._actions_during_current_inference = 0
        self._hold_logged = False
        self._worker_error: BaseException | None = None
        self._episode_first_action_time: float | None = None
        self.episode_stop_reason = ""
        self._stdin_fd: int | None = None
        self._stdin_termios: list[Any] | None = None
        self._latencies = _LatencyTracker(rtc_config.latency_window)
        self._snapshot_index = 0
        self._inference_index = 0
        self._last_action_metadata: dict[str, Any] | None = None
        self._thread = Thread(target=self._inference_loop, name="PI05-RTC", daemon=True)
        self._thread.start()

    def reset(self) -> None:
        self._active.clear()
        self._restore_terminal()
        with self._reset_lock:
            self.policy.reset()
            with self._inference_budget_lock:
                self._inference_active.clear()
                self._actions_during_current_inference = 0
                self._hold_logged = False
                self._action_queue.clear()
                self._last_action_metadata = None
            with self._batch_lock:
                self._latest_batch = None
                self._latest_snapshot_observation = None
            self._observation_ready.clear()
            self._worker_error = None
            self._episode_first_action_time = None
            self.episode_stop_reason = ""

    def close(self) -> None:
        self._shutdown.set()
        self._active.set()
        self._observation_ready.set()
        if self._thread.is_alive():
            self._thread.join(timeout=5.0)
        if self._thread.is_alive():
            logger.warning("PI0.5 RTC worker did not stop within 5 seconds")
        self._restore_terminal()

    def on_episode_end(self) -> None:
        """Pause action production and restore terminal state after an episode."""
        self._active.clear()
        with self._inference_budget_lock:
            self._inference_active.clear()
            self._actions_during_current_inference = 0
            self._hold_logged = False
            self._action_queue.clear()
            self._last_action_metadata = None
        self._restore_terminal()

    def select_action(
        self,
        batch: dict[str, Any],
        snapshot_observation: dict[str, Any] | None = None,
    ) -> Tensor | None:
        self._enable_terminal_keys()
        with self._batch_lock:
            self._latest_batch = _clone_batch(batch)
            self._latest_snapshot_observation = (
                None if snapshot_observation is None else _clone_batch(snapshot_observation)
            )
        self._observation_ready.set()
        self._active.set()

        deadline = time.monotonic() + self.rtc_config.inference_timeout_s
        while True:
            if self._runtime_stop_requested():
                return None
            if self._worker_error is not None:
                raise RuntimeError("PI0.5 RTC background inference failed") from self._worker_error
            action = self._get_action_with_inference_budget()
            if action is not None:
                if self._episode_first_action_time is None:
                    self._episode_first_action_time = time.monotonic()
                return action.unsqueeze(0)
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Timed out after {self.rtc_config.inference_timeout_s:.1f}s waiting for an RTC action"
                )
            time.sleep(0.002)

    def _runtime_stop_requested(self) -> bool:
        if self.external_stop_requested is not None and self.external_stop_requested():
            self.episode_stop_reason = "external stop requested"
            logger.info("External stop received; stopping the current episode")
            return True

        if self.enable_terminal_control:
            key = self._read_terminal_key()
            if key == "q":
                self.episode_stop_reason = "operator pressed q"
                logger.info("Runtime q received; stopping the current episode")
                return True

        if self.max_episode_wall_time_s > 0.0 and self._episode_first_action_time is not None:
            elapsed_s = time.monotonic() - self._episode_first_action_time
            if elapsed_s >= self.max_episode_wall_time_s:
                self.episode_stop_reason = (
                    f"maximum wall time reached ({elapsed_s:.3f}s >= "
                    f"{self.max_episode_wall_time_s:.3f}s)"
                )
                logger.info("Stopping current episode: %s", self.episode_stop_reason)
                return True
        return False

    def _enable_terminal_keys(self) -> None:
        if not self.enable_terminal_control or self._stdin_termios is not None or not sys.stdin.isatty():
            return
        try:
            self._stdin_fd = sys.stdin.fileno()
            self._stdin_termios = termios.tcgetattr(self._stdin_fd)
            tty.setcbreak(self._stdin_fd)
            logger.info("Runtime control enabled: press q to stop the current episode")
        except (OSError, termios.error):
            self._stdin_fd = None
            self._stdin_termios = None
            logger.warning("Could not enable single-key runtime control; wall-time stop remains active")

    def _read_terminal_key(self) -> str | None:
        if self._stdin_fd is None:
            return None
        try:
            readable, _, _ = select.select([self._stdin_fd], [], [], 0.0)
            if not readable:
                return None
            return os.read(self._stdin_fd, 1).decode(errors="ignore").lower()
        except OSError:
            return None

    def _restore_terminal(self) -> None:
        if self._stdin_fd is not None and self._stdin_termios is not None:
            try:
                termios.tcsetattr(self._stdin_fd, termios.TCSADRAIN, self._stdin_termios)
            except (OSError, termios.error):
                logger.warning("Failed to restore terminal settings")
        self._stdin_fd = None
        self._stdin_termios = None

    def _get_action_with_inference_budget(self) -> Tensor | None:
        """Get one action, or hold when the in-flight inference budget is spent."""
        with self._inference_budget_lock:
            max_actions = self.rtc_config.max_actions_during_inference
            if (
                self._inference_active.is_set()
                and max_actions >= 0
                and self._actions_during_current_inference >= max_actions
            ):
                if not self._hold_logged:
                    logger.info(
                        "RTC execution budget reached (%d actions); holding the last robot target "
                        "until inference completes",
                        max_actions,
                    )
                    self._hold_logged = True
                return None

            action, metadata = self._action_queue.get_with_metadata()
            self._last_action_metadata = metadata
            if action is not None and self._inference_active.is_set():
                self._actions_during_current_inference += 1
            return action

    def get_last_action_metadata(self) -> dict[str, Any] | None:
        """Metadata for the action returned by the latest ``select_action`` call."""
        return None if self._last_action_metadata is None else dict(self._last_action_metadata)

    def _predict_action_chunk(
        self,
        batch: dict[str, Any],
        inference_delay: int,
        prev_chunk_left_over: Tensor | None,
    ) -> Tensor:
        self.policy.eval()
        images, img_masks = self.policy._preprocess_images(batch)  # noqa: SLF001
        tokens = batch[OBS_LANGUAGE_TOKENS]
        masks = batch[OBS_LANGUAGE_ATTENTION_MASK]
        actions = sample_actions_with_rtc(
            self.policy.model,
            images,
            img_masks,
            tokens,
            masks,
            self.rtc_processor,
            inference_delay=inference_delay,
            prev_chunk_left_over=prev_chunk_left_over,
        )
        action_dim = self.config.output_features[ACTION].shape[0]
        return actions[:, :, :action_dim]

    def _save_inference_snapshot(
        self,
        snapshot_observation: dict[str, Any] | None,
        *,
        queue_size_before: int,
        predicted_delay: int,
    ) -> None:
        """Save the exact raw image/state pair associated with an RTC inference."""
        if self.snapshot_dir is None or snapshot_observation is None:
            return

        try:
            import cv2
            import numpy as np

            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            self._snapshot_index += 1
            now = datetime.now().astimezone()
            inference_start_wall_time_ns = time.time_ns()
            inference_start_monotonic_ns = time.monotonic_ns()
            stem = f"inference_{self._snapshot_index:04d}_{now.strftime('%Y%m%d_%H%M%S_%f')}"
            observed_wall_time_ns = int(snapshot_observation.get("observed_wall_time_ns", 0))
            observed_monotonic_ns = int(snapshot_observation.get("observed_monotonic_ns", 0))
            image_files: dict[str, str] = {}

            for name, value in snapshot_observation.items():
                if not name.startswith("observation.images.") or not isinstance(value, Tensor):
                    continue
                image = value.detach().cpu()
                if image.ndim == 4 and image.shape[0] == 1:
                    image = image[0]
                if image.ndim == 3 and image.shape[0] in {1, 3, 4}:
                    image = image.permute(1, 2, 0)
                array = image.numpy()
                if array.dtype != np.uint8:
                    scale = 255.0 if array.size and float(np.nanmax(array)) <= 1.0 else 1.0
                    array = np.clip(array * scale, 0, 255).astype(np.uint8)
                if array.ndim == 3 and array.shape[2] == 1:
                    array = array[:, :, 0]
                elif array.ndim == 3 and array.shape[2] >= 3:
                    array = cv2.cvtColor(array[:, :, :3], cv2.COLOR_RGB2BGR)
                camera_name = name.removeprefix("observation.images.").replace("/", "_")
                image_path = self.snapshot_dir / f"{stem}_{camera_name}.jpg"
                if not cv2.imwrite(str(image_path), array):
                    raise RuntimeError(f"cv2.imwrite returned false for {image_path}")
                image_files[name] = image_path.name

            state = snapshot_observation.get("observation.state")
            state_values = state.detach().cpu().reshape(-1).tolist() if isinstance(state, Tensor) else None
            metadata = {
                "inference_index": self._snapshot_index,
                "inference_start_local_time": now.isoformat(),
                "inference_start_wall_time_ns": inference_start_wall_time_ns,
                "observation_read_wall_time_ns": observed_wall_time_ns or None,
                "observation_to_inference_ms": (
                    (inference_start_monotonic_ns - observed_monotonic_ns) / 1_000_000.0
                    if observed_monotonic_ns
                    else None
                ),
                "queue_size_before": queue_size_before,
                "predicted_delay_frames": predicted_delay,
                "observation_state": state_values,
                "images": image_files,
                "note": "Times are client-side; camera capture/network age is not available in the current stream.",
            }
            metadata_path = self.snapshot_dir / f"{stem}.json"
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info(
                "Saved RTC inference snapshot %d: images=%d observation_to_inference_ms=%.1f dir=%s",
                self._snapshot_index,
                len(image_files),
                metadata["observation_to_inference_ms"] or 0.0,
                self.snapshot_dir,
            )
        except Exception:
            logger.warning("Failed to save RTC inference snapshot", exc_info=True)

    def _inference_loop(self) -> None:
        try:
            seconds_per_action = 1.0 / self.frequency
            while not self._shutdown.is_set():
                if not self._active.wait(timeout=0.01):
                    continue
                if not self._observation_ready.wait(timeout=0.01):
                    continue
                if self._action_queue.qsize() > self.rtc_config.queue_threshold:
                    time.sleep(0.005)
                    continue

                with self._reset_lock:
                    if not self._active.is_set() or self._shutdown.is_set():
                        continue
                    with self._batch_lock:
                        batch = None if self._latest_batch is None else _clone_batch(self._latest_batch)
                        snapshot_observation = (
                            None
                            if self._latest_snapshot_observation is None
                            else _clone_batch(self._latest_snapshot_observation)
                        )
                    if batch is None:
                        continue

                    with self._inference_budget_lock:
                        queue_size_before = self._action_queue.qsize()
                        index_before = self._action_queue.get_action_index()
                        prev_actions = self._action_queue.get_left_over()
                        self._actions_during_current_inference = 0
                        self._hold_logged = False
                        self._inference_active.set()

                    latency_delay = math.ceil(self._latencies.maximum() / seconds_per_action)
                    max_actions = self.rtc_config.max_actions_during_inference
                    predicted_delay = (
                        min(latency_delay, max_actions) if max_actions >= 0 else latency_delay
                    )
                    if prev_actions is not None:
                        prev_actions = prev_actions[: self.rtc_config.execution_horizon]

                    self._save_inference_snapshot(
                        snapshot_observation,
                        queue_size_before=queue_size_before,
                        predicted_delay=predicted_delay,
                    )

                    start = time.perf_counter()
                    inference_start_wall_time_ns = time.time_ns()
                    inference_start_monotonic_ns = time.monotonic_ns()
                    autocast = (
                        torch.autocast(device_type="cuda")
                        if str(self.config.device).startswith("cuda") and self.config.use_amp
                        else torch.autocast(device_type="cpu", enabled=False)
                    )
                    with autocast:
                        actions = self._predict_action_chunk(batch, predicted_delay, prev_actions)
                    original = actions.squeeze(0).detach()
                    with torch.no_grad():
                        processed = self.postprocessor(actions).squeeze(0).detach()
                    latency_s = time.perf_counter() - start
                    self._latencies.add(latency_s)

                    # No action executes during the initial blocking inference.  For
                    # later chunks, use the actual number consumed by the control loop
                    # rather than only the wall-clock latency estimate.
                    with self._inference_budget_lock:
                        if not self._active.is_set():
                            self._inference_active.clear()
                            self._actions_during_current_inference = 0
                            self._hold_logged = False
                            logger.info("Discarding RTC chunk because the episode has ended")
                            continue
                        index_after = self._action_queue.get_action_index()
                        consumed = (
                            0 if queue_size_before == 0 else max(0, index_after - index_before)
                        )
                        self._inference_index += 1
                        inference_index = self._inference_index
                        inference_end_wall_time_ns = time.time_ns()
                        inference_end_monotonic_ns = time.monotonic_ns()
                        metadata = [
                            {
                                "inference_index": inference_index,
                                "chunk_action_index": action_index,
                                "inference_start_wall_time_ns": inference_start_wall_time_ns,
                                "inference_end_wall_time_ns": inference_end_wall_time_ns,
                                "inference_start_monotonic_ns": inference_start_monotonic_ns,
                                "inference_end_monotonic_ns": inference_end_monotonic_ns,
                                "inference_latency_s": latency_s,
                                "guided_delay_frames": predicted_delay,
                                "consumed_during_inference": consumed,
                            }
                            for action_index in range(len(processed))
                        ]
                        self._action_queue.merge(original, processed, consumed, metadata)
                        self._inference_active.clear()
                        self._actions_during_current_inference = 0
                        self._hold_logged = False
                    policy_model = getattr(self.policy, "model", None)
                    self._last_chunk_profile = dict(
                        getattr(policy_model, "_last_sample_actions_profile", {})
                    )
                    self._last_chunk_profile.update(
                        {
                            "latency_delay": latency_delay,
                            "inference_delay": predicted_delay,
                            "consumed_during_inference": consumed,
                            "queue_after_merge": self._action_queue.qsize(),
                        }
                    )
                    logger.info(
                        "RTC chunk ready: latency_s=%.3f latency_delay=%d guided_delay=%d "
                        "consumed=%d queue=%d",
                        latency_s,
                        latency_delay,
                        predicted_delay,
                        consumed,
                        self._action_queue.qsize(),
                    )
        except BaseException as exc:  # propagate worker failures to the control thread
            self._worker_error = exc
            logger.error("Fatal PI0.5 RTC inference error: %s", exc)
            logger.error(traceback.format_exc())
