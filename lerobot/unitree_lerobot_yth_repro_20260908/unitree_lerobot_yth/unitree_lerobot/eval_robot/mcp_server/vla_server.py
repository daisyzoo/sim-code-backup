"""VLA HTTP Server — exposes /vla/execute (SSE), /vla/stop, /vla/status endpoints.

Run in a separate thread; communicates with the VLA inference loop via VLAController.
"""

import uuid
import json
import asyncio
import threading
import logging
from collections import OrderedDict
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse

from .vla_controller import VLAController, VLATask, VLAState

logger = logging.getLogger("vla_server")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# App factory (allows reusing in unit tests)
# ---------------------------------------------------------------------------

MAX_TASK_CACHE = 1000

def create_vla_server(
    controller: VLAController,
    run_eval_fn,
    default_episode_duration_s: float = 6.0,
) -> FastAPI:
    """Build FastAPI app, wire controller and eval runner.

    Args:
        controller: VLAController shared between HTTP server and eval loop.
        run_eval_fn: Callable that starts the eval loop with the controller.
        default_episode_duration_s: Fallback duration when HTTP body doesn't specify one.
    """

    app = FastAPI(title="VLA Control Server")

    # Idempotency cache: req_id → result (bounded to avoid memory leak)
    task_cache: OrderedDict[str, dict] = OrderedDict()
    # In-flight SSE streams: req_id → last_step
    activeStreams: dict[str, int] = {}
    stream_lock = threading.Lock()

    # ---------------------------------------------------------------------------
    # Background: start VLA inference loop in a daemon thread
    # ---------------------------------------------------------------------------
    def vla_loop():
        run_eval_fn(controller)

    threading.Thread(target=vla_loop, daemon=True, name="VLA-InferenceLoop").start()
    logger.info("VLA inference loop started in background thread.")

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    async def event_generator(req_id: str):
        """SSE stream: ack → progress → done (loop: done per episode, never closes)."""
        nonlocal activeStreams

        # 1. Immediate ack
        yield f"data: {json.dumps({'type': 'ack', 'task_id': req_id})}\n\n"

        last_step = -1
        last_state = None
        while True:
            await asyncio.sleep(0.2)

            status = controller.get_status()
            cur_step = status["step"]
            cur_state = status["state"]

            # Progress update (only on step change)
            if cur_step != last_step:
                last_step = cur_step
                payload = {
                    "type": "progress",
                    "state": cur_state,
                    "step": cur_step,
                }
                yield f"data: {json.dumps(payload)}\n\n"

            last_result = status.get("last_result")
            current_state = status["state"]

            # Detect episode completion:
            # - Single-shot: state transitions from RUNNING/RETURNING to IDLE
            # - Loop mode: state transitions from RUNNING/RETURNING back to LOOPING
            #   (complete_episode resets _current_task to loop_task and keeps LOOPING)
            episode_done = (
                last_result is not None
                and last_state in (VLAState.RUNNING.value, VLAState.RETURNING.value, VLAState.PREPARING.value)
                and current_state in (VLAState.IDLE.value, VLAState.LOOPING.value)
            )
            last_state = current_state

            if episode_done:
                if len(task_cache) >= MAX_TASK_CACHE:
                    task_cache.popitem(last=False)
                task_cache[req_id] = last_result
                done_payload = {"type": "done", "result": last_result}
                yield f"data: {json.dumps(done_payload)}\n\n"

                # Single-shot: IDLE means fully done. Loop: LOOPING means next episode already running.
                if current_state == VLAState.IDLE.value:
                    yield "data: [DONE]\n\n"
                    with stream_lock:
                        activeStreams.pop(req_id, None)
                    break

    # ---------------------------------------------------------------------------
    # Routes
    # ---------------------------------------------------------------------------

    @app.post("/vla/execute")
    async def execute_task(
        body: dict,
        x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    ):
        """Execute a VLA skill.

        Request body (JSON):
            task_text: str  — natural language task, e.g. "wave hand"
            duration_s: float (optional, falls back to EPISODE_DURATION_S env var)

        Returns: SSE stream with ack / progress / done events.
        Raises: 409 if VLA is busy or in loop mode.
        """
        req_id = x_request_id or str(uuid.uuid4())

        # Idempotency: return cached result if same req_id replayed
        if req_id in task_cache:
            cached = task_cache[req_id]
            async def cached_stream():
                yield f"data: {json.dumps({'type': 'ack', 'task_id': req_id})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'result': cached})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(cached_stream(), media_type="text/event-stream")

        task = VLATask(
            task_id=req_id,
            task_text=body.get("task_text", ""),
            duration_s=body.get("duration_s", default_episode_duration_s),
        )

        if not controller.submit_task(task):
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "VLA busy — current state",
                    "status": controller.get_status(),
                },
            )

        with stream_lock:
            activeStreams[req_id] = -1

        return StreamingResponse(
            event_generator(req_id),
            media_type="text/event-stream",
            headers={"X-Request-Id": req_id},
        )

    @app.post("/vla/stop")
    async def stop_task():
        """Emergency stop — signal current episode to abort at next step."""
        controller.stop_current()
        return {"ok": True, "state": controller.get_status()["state"]}

    @app.post("/vla/loop_start")
    async def loop_start(
        body: dict,
        x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    ):
        """Start continuous loop mode — repeatedly execute the same task.

        Body:
            task_text: str
            duration_s: float (optional)
        """
        req_id = x_request_id or str(uuid.uuid4())
        task = VLATask(
            task_id=req_id,
            task_text=body.get("task_text", ""),
            duration_s=body.get("duration_s", default_episode_duration_s),
        )
        controller.start_loop(task)
        return {"ok": True, "task_id": req_id, "state": controller.get_status()["state"]}

    @app.post("/vla/loop_stop")
    async def loop_stop():
        """Stop continuous loop mode after current episode finishes."""
        controller.stop_loop()
        return {"ok": True, "state": controller.get_status()["state"]}

    @app.get("/vla/status")
    async def get_status():
        """Poll current VLA state."""
        return controller.get_status()

    @app.get("/vla/health")
    async def health():
        """Liveness probe."""
        return {"ok": True}

    return app