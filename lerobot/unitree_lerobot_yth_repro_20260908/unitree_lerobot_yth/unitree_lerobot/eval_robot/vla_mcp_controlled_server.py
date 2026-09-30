"""Single-shot VLA HTTP/MCP server.

`/vla/execute` starts one VLA task and streams progress until it finishes.
`/vla/stop` requests the current task to stop and return to idle.
`/mcp` exposes the same VLA controls as Streamable HTTP MCP tools.
"""

import argparse
import asyncio
import json
import logging
import sys
import threading
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse

try:
    from mcp.server.fastmcp import FastMCP

    _MCP_AVAILABLE = True
except ImportError:
    FastMCP = None
    _MCP_AVAILABLE = False

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

logger = logging.getLogger("vla_mcp_controlled")
logger.setLevel(logging.INFO)

DEFAULT_VLA_BASE = "http://localhost:8765"
MAX_TASK_CACHE = 1000


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(asctime)s %(name)s:%(lineno)d %(message)s",
        force=True,
    )


def create_vla_mcp(
    vla_base: str = DEFAULT_VLA_BASE,
    default_duration_s: float = 10.0,
    allow_duration_override: bool = True,
) -> "FastMCP":
    if not _MCP_AVAILABLE:
        raise RuntimeError("MCP not available — install with: pip install mcp[fastmcp]")
    if httpx is None:
        raise RuntimeError("httpx not available — install with: pip install httpx")

    mcp = FastMCP("vla-controlled-task")

    async def execute_request(
        task_text: str,
        duration_s: float,
        request_id: Optional[str],
    ) -> str:
        headers = {}
        if request_id:
            headers["X-Request-Id"] = request_id

        result = None
        timeout = httpx.Timeout(connect=5.0, read=300.0, write=30.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{vla_base}/vla/execute",
                json={"task_text": task_text, "duration_s": duration_s},
                headers=headers,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        raw = line[6:]
                        if raw == "[DONE]":
                            break
                        try:
                            payload = json.loads(raw)
                        except json.JSONDecodeError:
                            logger.debug("Non-JSON SSE line: %s", raw)
                            continue
                        if payload.get("type") == "done":
                            result = payload.get("result")
                        logger.debug("SSE line: %s", raw)

        if result:
            return json.dumps(result)

        timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            status = await client.get(f"{vla_base}/vla/status")
        last = status.json().get("last_result")
        if last:
            import json as _json

            return _json.dumps(last)
        return '{"error": "no result returned"}'

    if allow_duration_override:

        @mcp.tool(name="vla_execute")
        async def vla_execute_with_duration(
            task_text: str,
            duration_s: float = default_duration_s,
            request_id: Optional[str] = None,
        ) -> str:
            return await execute_request(task_text, duration_s, request_id)

    else:

        @mcp.tool(name="vla_execute")
        async def vla_execute_fixed_duration(
            task_text: str,
            request_id: Optional[str] = None,
        ) -> str:
            return await execute_request(task_text, default_duration_s, request_id)

    @mcp.tool()
    async def vla_stop() -> str:
        timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{vla_base}/vla/stop")
            return r.json()

    @mcp.tool()
    async def vla_status() -> dict:
        timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{vla_base}/vla/status")
            return r.json()

    return mcp


def create_vla_controlled_server(
    controller,
    run_eval_fn,
    default_episode_duration_s: float = 6.0,
    vla_base: str = DEFAULT_VLA_BASE,
    mcp_default_duration_s: float | None = None,
    max_task_duration_s: float = 0.0,
    allow_task_duration_override: bool = True,
) -> FastAPI:
    if not _MCP_AVAILABLE:
        raise RuntimeError("MCP not available — install with: pip install 'mcp[fastmcp]'")
    if httpx is None:
        raise RuntimeError("httpx not available — install with: pip install httpx")

    if default_episode_duration_s <= 0.0:
        raise ValueError("default_episode_duration_s must be greater than zero")
    if max_task_duration_s < 0.0:
        raise ValueError("max_task_duration_s must be greater than or equal to zero")
    tool_default_duration_s = 10.0 if mcp_default_duration_s is None else mcp_default_duration_s
    if tool_default_duration_s <= 0.0:
        raise ValueError("mcp_default_duration_s must be greater than zero")

    mcp = create_vla_mcp(
        vla_base,
        default_duration_s=tool_default_duration_s,
        allow_duration_override=allow_task_duration_override,
    )
    mcp.settings.streamable_http_path = "/"
    mcp_app = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(title="VLA Controlled Loop Server", lifespan=lifespan)

    task_cache: OrderedDict[str, dict] = OrderedDict()
    stream_lock = threading.Lock()
    active_streams: dict[str, int] = {}

    def vla_loop():
        logger.info("VLA controlled eval loop thread entering run_eval.")
        try:
            run_eval_fn(controller)
        except Exception:
            logger.exception("VLA controlled eval loop crashed during startup/runtime.")
            raise

    threading.Thread(target=vla_loop, daemon=True, name="VLA-ControlledLoop").start()
    logger.info("VLA controlled eval loop started in background thread.")

    async def event_generator(req_id: str):
        yield f"data: {json.dumps({'type': 'ack', 'task_id': req_id})}\n\n"

        last_step = -1
        last_result = None
        while True:
            await asyncio.sleep(0.2)

            status = controller.get_status()
            cur_step = status["step"]
            cur_state = status["state"]

            if cur_step != last_step:
                last_step = cur_step
                payload = {"type": "progress", "state": cur_state, "step": cur_step}
                yield f"data: {json.dumps(payload)}\n\n"

            current_result = status.get("last_result")
            if current_result is not None and current_result != last_result:
                last_result = current_result
                if len(task_cache) >= MAX_TASK_CACHE:
                    task_cache.popitem(last=False)
                task_cache[req_id] = current_result
                yield f"data: {json.dumps({'type': 'done', 'result': current_result})}\n\n"

            if cur_state == "idle" and current_result is not None:
                yield "data: [DONE]\n\n"
                with stream_lock:
                    active_streams.pop(req_id, None)
                break

    @app.post("/vla/execute")
    async def execute_task(
        body: dict,
        x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    ):
        from unitree_lerobot.eval_robot.mcp_server.vla_controller import VLATask

        req_id = x_request_id or str(uuid.uuid4())
        if req_id in task_cache:
            cached = task_cache[req_id]

            async def cached_stream():
                yield f"data: {json.dumps({'type': 'ack', 'task_id': req_id})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'result': cached})}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(cached_stream(), media_type="text/event-stream")

        if allow_task_duration_override:
            try:
                requested_duration_s = float(body.get("duration_s", default_episode_duration_s))
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=422, detail="duration_s must be a number") from exc
            if requested_duration_s <= 0.0:
                raise HTTPException(status_code=422, detail="duration_s must be greater than zero")
        else:
            requested_duration_s = default_episode_duration_s
        effective_duration_s = requested_duration_s
        if max_task_duration_s > 0.0:
            effective_duration_s = min(requested_duration_s, max_task_duration_s)
        if effective_duration_s != requested_duration_s:
            logger.info(
                "Clamped task %s duration from %.2fs to configured maximum %.2fs.",
                req_id,
                requested_duration_s,
                effective_duration_s,
            )

        task = VLATask(
            task_id=req_id,
            task_text=body.get("task_text", ""),
            duration_s=effective_duration_s,
        )
        if not controller.submit_task(task):
            raise HTTPException(
                status_code=409,
                detail={"message": "VLA busy — current state", "status": controller.get_status()},
            )

        with stream_lock:
            active_streams[req_id] = -1

        return StreamingResponse(
            event_generator(req_id),
            media_type="text/event-stream",
            headers={"X-Request-Id": req_id},
        )

    @app.post("/vla/stop")
    async def stop_task():
        controller.stop_current()
        return {"ok": True, "state": controller.get_status()["state"]}

    @app.get("/vla/status")
    async def get_status():
        return controller.get_status()

    @app.get("/vla/health")
    async def health():
        return {"ok": True}

    app.mount("/mcp", mcp_app)
    logger.info("VLA Streamable HTTP MCP endpoint mounted at /mcp.")

    return app


def run_vla_server(vla_base: str = DEFAULT_VLA_BASE, port: int = 8765, config_path: str = None, cfg=None):
    configure_logging()
    logger.info("Preparing VLA controlled server on port %s with vla_base=%s", port, vla_base)
    try:
        import uvicorn
    except ImportError:
        raise RuntimeError("uvicorn not available — install with: pip install uvicorn")

    from lerobot.configs import parser
    from unitree_lerobot.eval_robot.eval_g1_mcp_controlled import run_eval_with_controller
    from unitree_lerobot.eval_robot.mcp_server.vla_controller import VLAController
    from unitree_lerobot.eval_robot.utils.utils import EvalRealConfig

    controller = VLAController()

    def run_eval(c: VLAController):
        nonlocal cfg
        if cfg is None and config_path:
            cfg = parser.load_yaml(config_path, EvalRealConfig)
        elif cfg is None:
            cfg = EvalRealConfig()
        run_eval_with_controller(cfg, c)

    if cfg is None and config_path:
        logger.info("Loading eval config from %s", config_path)
        cfg = parser.load_yaml(config_path, EvalRealConfig)
    elif cfg is None:
        logger.info("Using default EvalRealConfig.")
        cfg = EvalRealConfig()
    default_duration = cfg.episode_duration_s
    logger.info(
        "Eval config ready: policy=%s repo_id=%s root=%s episode=%s send_real_robot=%s frequency=%s",
        getattr(cfg.policy, "pretrained_path", None),
        cfg.repo_id,
        cfg.root,
        cfg.episodes,
        cfg.send_real_robot,
        cfg.frequency,
    )

    app = create_vla_controlled_server(
        controller,
        run_eval,
        default_episode_duration_s=default_duration,
        vla_base=vla_base,
    )
    logger.info("Starting uvicorn HTTP server on 0.0.0.0:%s", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    configure_logging()
    from lerobot.configs import parser as lerobot_parser
    from unitree_lerobot.eval_robot.utils.utils import EvalRealConfig

    logger.info("Parsing VLA controlled server CLI arguments.")
    parser_arg = argparse.ArgumentParser(description="VLA Controlled Loop Server")
    parser_arg.add_argument("--vla-base", default=DEFAULT_VLA_BASE, help="VLA HTTP server base URL")
    parser_arg.add_argument("--port", type=int, default=8765, help="Port for HTTP server")
    parser_arg.add_argument("--config", type=str, default=None, help="Path to eval YAML config")
    args, _ = parser_arg.parse_known_args()

    if args.config:
        run_vla_server(vla_base=args.vla_base, port=args.port, config_path=args.config)
    else:
        saved_argv = sys.argv

        def main(cfg: EvalRealConfig):
            run_vla_server(vla_base=args.vla_base, port=args.port, cfg=cfg)

        wrapped = lerobot_parser.wrap()(main)
        filtered = [
            arg
            for arg in saved_argv[1:]
            if not arg.startswith(("--vla-base=", "--port=", "--config="))
        ]
        sys.argv = [saved_argv[0]] + filtered

        try:
            wrapped()
        finally:
            sys.argv = saved_argv
