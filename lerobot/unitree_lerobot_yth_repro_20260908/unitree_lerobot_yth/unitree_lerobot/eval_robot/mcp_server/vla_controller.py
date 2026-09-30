"""VLA Controller — thread-safe shared state between HTTP server and VLA inference loop."""

import threading
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class VLAState(Enum):
    IDLE = "idle"
    LOOPING = "looping"      # continuous loop mode (task restarts automatically)
    PREPARING = "preparing"  # moving to initial pose
    RUNNING = "running"      # inference loop active
    RETURNING = "returning"  # returning to zero
    ERROR = "error"


@dataclass
class VLATask:
    task_id: str
    task_text: str                # e.g. "wave hand", "pick up the red cup"
    duration_s: float = 10.0
    episode_idx: int = 0


class VLAController:
    """Thread-safe VLA controller — bridge between brain (HTTP) and inference loop."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = VLAState.IDLE
        self._pending_task: Optional[VLATask] = None
        self._current_task: Optional[VLATask] = None
        self._stop_event = threading.Event()
        self._step_count = 0
        self._last_result: Optional[dict] = None
        self._task_text_override: Optional[str] = None
        self._loop_mode = False
        self._loop_task: Optional[VLATask] = None

    # ── External (HTTP server) calls ──────────────────────────────────────────

    def submit_task(self, task: VLATask) -> bool:
        """Submit a single-shot task. Returns False if VLA is busy or in loop mode."""
        with self._lock:
            if self._state == VLAState.LOOPING:
                return False
            if self._state not in (VLAState.IDLE, VLAState.ERROR):
                return False
            self._pending_task = task
            self._task_text_override = task.task_text
            self._stop_event.clear()
            self._last_result = None
            return True

    def stop_current(self):
        """Signal the current episode to stop at the next step check."""
        self._stop_event.set()

    def get_status(self) -> dict:
        """Return current status for SSE / polling."""
        with self._lock:
            return {
                "state": self._state.value,
                "task_id": self._current_task.task_id if self._current_task else None,
                "step": self._step_count,
                "task_text": self._task_text_override,
                "last_result": self._last_result,
                "loop_mode": self._loop_mode,
            }

    def is_idle(self) -> bool:
        with self._lock:
            return self._state == VLAState.IDLE

    def start_loop(self, task: VLATask) -> bool:
        """Enable continuous loop mode. Returns False if already in loop or busy."""
        with self._lock:
            if self._state == VLAState.LOOPING:
                return False
            if self._state not in (VLAState.IDLE, VLAState.ERROR):
                return False
            self._loop_mode = True
            self._loop_task = task
            self._task_text_override = task.task_text
            self._stop_event.clear()
            self._last_result = None
            self._pending_task = None
            self._state = VLAState.LOOPING
            return True

    def stop_loop(self):
        """Disable continuous loop mode — only way to exit loop."""
        with self._lock:
            self._loop_mode = False
            self._loop_task = None
            self._stop_event.clear()
            self._state = VLAState.IDLE

    def request_stop_loop(self):
        """Gracefully stop loop mode after the current episode cleanup completes."""
        with self._lock:
            self._loop_mode = False
            self._loop_task = None
            self._stop_event.set()

    def is_looping(self) -> bool:
        with self._lock:
            return self._state == VLAState.LOOPING

    # ── VLA loop internal calls ──────────────────────────────────────────────

    def pop_task(self) -> Optional[VLATask]:
        """Called by VLA loop to consume a pending task.

        In loop mode, always returns the loop task; ignores pending_task.
        Outside loop mode, normal single-shot behavior.
        """
        with self._lock:
            if self._state == VLAState.LOOPING:
                self._current_task = self._loop_task
                self._step_count = 0
                return self._current_task
            if self._pending_task is not None:
                self._current_task = self._pending_task
                self._pending_task = None
                self._step_count = 0
                return self._current_task
            return None

    def should_stop(self) -> bool:
        """Called every inference step — returns True if brain requested stop."""
        return self._stop_event.is_set()

    def set_state(self, s: VLAState):
        with self._lock:
            self._state = s

    def update_step(self, step: int):
        self._step_count = step

    def complete_episode(
        self,
        completed: bool,
        restart_loop: bool = True,
        reason: str = "",
        details: dict | None = None,
    ):
        """Called by VLA loop when episode ends.

        In loop mode: immediately restart the loop_task without going to IDLE.
        Outside loop mode: clean up normally.
        """
        with self._lock:
            if self._current_task:
                self._last_result = {
                    "task_id": self._current_task.task_id,
                    "steps": self._step_count,
                    "completed": completed,
                }
                if reason:
                    self._last_result["reason"] = reason
                if details:
                    self._last_result["details"] = dict(details)
            self._current_task = None
            self._task_text_override = None

            if restart_loop and self._loop_mode and self._loop_task:
                # Restart next loop episode immediately
                self._current_task = self._loop_task
                self._step_count = 0
                self._task_text_override = self._loop_task.task_text
                self._state = VLAState.LOOPING
                self._stop_event.clear()
            else:
                self._loop_mode = False
                self._loop_task = None
                self._stop_event.clear()
                self._state = VLAState.IDLE
