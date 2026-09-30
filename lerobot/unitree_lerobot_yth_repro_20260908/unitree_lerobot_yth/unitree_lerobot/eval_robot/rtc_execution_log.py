"""Low-overhead JSONL logging for actions actually issued by RTC evaluation."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any


class RTCExecutionLogger:
    """Append one machine-readable record per control-loop action.

    The file is line-buffered so a run that is stopped with ``q`` still leaves
    all previously issued commands available for analysis.
    """

    def __init__(self, path: str) -> None:
        self.path = Path(path).expanduser() if path else None
        self._lock = threading.Lock()
        self._file = None
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._file = self.path.open("a", encoding="utf-8", buffering=1)

    @property
    def enabled(self) -> bool:
        return self._file is not None

    def write(self, record: dict[str, Any]) -> None:
        if self._file is None:
            return
        payload = {
            "record_type": "rtc_executed_action",
            "logged_wall_time_ns": time.time_ns(),
            "logged_monotonic_ns": time.monotonic_ns(),
            **record,
        }
        with self._lock:
            self._file.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
            self._file.flush()

    def close(self) -> None:
        if self._file is not None:
            with self._lock:
                self._file.close()
                self._file = None
