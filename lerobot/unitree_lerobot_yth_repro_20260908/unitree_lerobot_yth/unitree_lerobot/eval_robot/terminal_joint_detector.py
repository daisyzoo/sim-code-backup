"""Thread-safe terminal joint-pose hold detector for real-robot evaluation."""

from __future__ import annotations

import json
import logging
import math
import time
from collections import deque
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Callable

import numpy as np

logger = logging.getLogger(__name__)


class TerminalJointPoseDetector:
    """Declare success after a measured joint pose stays in a learned terminal region."""

    def __init__(self, config_path: str | Path, frequency: float) -> None:
        self.config_path = Path(config_path).expanduser().resolve()
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        if config.get("detector_type") != "terminal_joint_pose_hold":
            raise ValueError(f"Unsupported terminal detector config: {config.get('detector_type')!r}")

        self.joint_names = tuple(config["joint_names"])
        self.lower_bounds = np.asarray(config["lower_bounds"], dtype=np.float64)
        self.upper_bounds = np.asarray(config["upper_bounds"], dtype=np.float64)
        self.max_p90_abs_deviation = np.asarray(
            config["max_p90_abs_deviation"], dtype=np.float64
        )
        self.reference_center = np.asarray(config["reference_center"], dtype=np.float64)
        self.hold_duration_s = float(config["hold_duration_s"])
        self.min_episode_elapsed_s = float(config["min_episode_elapsed_s"])
        self.minimum_sample_fraction = float(config.get("minimum_sample_fraction", 0.8))
        self.minimum_terminal_inlier_fraction = float(
            config.get("minimum_terminal_inlier_fraction", 0.9)
        )
        self.frequency = float(frequency)
        self.state_dim = len(self.joint_names)

        arrays = (
            self.lower_bounds,
            self.upper_bounds,
            self.max_p90_abs_deviation,
            self.reference_center,
        )
        if any(values.shape != (self.state_dim,) for values in arrays):
            raise ValueError("Terminal detector arrays must match joint_names length")
        if np.any(self.lower_bounds >= self.upper_bounds):
            raise ValueError("Each terminal lower bound must be below its upper bound")
        if np.any(self.max_p90_abs_deviation <= 0.0):
            raise ValueError("Each terminal p90 deviation threshold must be positive")
        if self.hold_duration_s <= 0.0 or self.frequency <= 0.0:
            raise ValueError("hold_duration_s and frequency must be positive")
        if not 0.0 < self.minimum_sample_fraction <= 1.0:
            raise ValueError("minimum_sample_fraction must be in (0, 1]")
        if not 0.0 < self.minimum_terminal_inlier_fraction <= 1.0:
            raise ValueError("minimum_terminal_inlier_fraction must be in (0, 1]")

        self._minimum_samples = max(
            2,
            int(math.ceil(self.hold_duration_s * self.frequency * self.minimum_sample_fraction)),
        )
        self._samples: deque[tuple[float, np.ndarray]] = deque()
        self._lock = Lock()
        self._active = Event()
        self._succeeded = Event()
        self._shutdown = Event()
        self._episode_start_time: float | None = None
        self._success_details: dict = {}
        self._monitor_thread: Thread | None = None

    @property
    def succeeded(self) -> bool:
        return self._succeeded.is_set()

    @property
    def success_details(self) -> dict:
        with self._lock:
            return dict(self._success_details)

    def reset(self) -> None:
        self._active.clear()
        self._succeeded.clear()
        with self._lock:
            self._samples.clear()
            self._episode_start_time = None
            self._success_details = {}

    def start_episode(self, timestamp: float | None = None) -> None:
        self.reset()
        with self._lock:
            self._episode_start_time = time.monotonic() if timestamp is None else float(timestamp)
        self._active.set()
        logger.info(
            "Terminal joint detector active: hold_s=%.2f min_elapsed_s=%.2f config=%s",
            self.hold_duration_s,
            self.min_episode_elapsed_s,
            self.config_path,
        )

    def stop_episode(self) -> None:
        self._active.clear()

    def observe(self, state: np.ndarray, timestamp: float | None = None) -> bool:
        if not self._active.is_set() or self._succeeded.is_set():
            return self._succeeded.is_set()
        now = time.monotonic() if timestamp is None else float(timestamp)
        values = np.asarray(state, dtype=np.float64).reshape(-1)
        if values.shape != (self.state_dim,) or not np.all(np.isfinite(values)):
            return False

        with self._lock:
            if self._episode_start_time is None:
                return False
            elapsed_s = now - self._episode_start_time
            if elapsed_s < self.min_episode_elapsed_s:
                self._samples.clear()
                return False

            self._samples.append((now, values.copy()))
            cutoff = now - self.hold_duration_s
            while self._samples and self._samples[0][0] < cutoff:
                self._samples.popleft()
            if len(self._samples) < self._minimum_samples:
                return False
            coverage_s = self._samples[-1][0] - self._samples[0][0]
            if coverage_s < self.hold_duration_s * 0.9:
                return False

            sample_values = np.stack([sample for _, sample in self._samples])
            inlier_frames = np.all(
                (sample_values >= self.lower_bounds) & (sample_values <= self.upper_bounds),
                axis=1,
            )
            inlier_fraction = float(np.mean(inlier_frames))
            if inlier_fraction < self.minimum_terminal_inlier_fraction:
                return False

            median_state = np.median(sample_values, axis=0)
            median_in_terminal_region = bool(
                np.all(median_state >= self.lower_bounds)
                and np.all(median_state <= self.upper_bounds)
            )
            if not median_in_terminal_region:
                return False

            p90_abs_deviation = np.quantile(
                np.abs(sample_values - median_state),
                0.9,
                axis=0,
            )
            if not np.all(p90_abs_deviation <= self.max_p90_abs_deviation):
                return False

            self._success_details = {
                "reason": "terminal joint pose held",
                "elapsed_s": round(elapsed_s, 4),
                "hold_s": round(coverage_s, 4),
                "samples": len(self._samples),
                "terminal_inlier_fraction": round(inlier_fraction, 4),
                "median_joint_state": [round(float(value), 6) for value in median_state],
                "p90_abs_deviation": [
                    round(float(value), 6) for value in p90_abs_deviation
                ],
            }
            self._succeeded.set()
            self._active.clear()
            logger.info("Terminal joint pose success detected: %s", self._success_details)
            return True

    def start_monitor(self, state_reader: Callable[[], np.ndarray]) -> None:
        if self._monitor_thread is not None:
            raise RuntimeError("Terminal joint monitor has already been started")

        def monitor_loop() -> None:
            period_s = 1.0 / self.frequency
            read_error_logged = False
            while not self._shutdown.is_set():
                loop_start = time.monotonic()
                if self._active.is_set():
                    try:
                        self.observe(state_reader(), timestamp=loop_start)
                        read_error_logged = False
                    except Exception as exc:  # monitoring must not crash robot control
                        if not read_error_logged:
                            logger.warning("Terminal joint monitor state read failed: %s", exc)
                            read_error_logged = True
                self._shutdown.wait(max(0.0, period_s - (time.monotonic() - loop_start)))

        self._monitor_thread = Thread(
            target=monitor_loop,
            name="TerminalJointMonitor",
            daemon=True,
        )
        self._monitor_thread.start()

    def close(self) -> None:
        self._active.clear()
        self._shutdown.set()
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
