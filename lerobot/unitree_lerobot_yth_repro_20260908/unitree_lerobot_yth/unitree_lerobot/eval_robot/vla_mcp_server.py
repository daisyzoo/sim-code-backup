"""VLA MCP Server — wraps vla_server HTTP endpoints as MCP tools for OpenClaw."""

import logging
import sys
from typing import Optional

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

logger = logging.getLogger("vla_mcp")
logger.setLevel(logging.INFO)

# Default target where vla_server runs
DEFAULT_VLA_BASE = "http://localhost:8765"


def create_vla_mcp(vla_base: str = DEFAULT_VLA_BASE) -> "FastMCP":
    """Build and return a FastMCP server that exposes VLA tools."""
    if not _MCP_AVAILABLE:
        raise RuntimeError(
            "MCP not available — install with: pip install mcp[fastmcp]"
        )
    if httpx is None:
        raise RuntimeError(
            "httpx not available — install with: pip install httpx"
        )

    mcp = FastMCP("vla-controller")

    @mcp.tool()
    async def vla_execute(
        task_text: str,
        duration_s: float = 10.0,
        request_id: Optional[str] = None,
    ) -> str:
        """Execute a VLA skill on the robot.

        Args:
            task_text: Natural language task description.
                       Examples: "wave hand", "pick up the red cup", "turn left"
            duration_s: Maximum execution time in seconds (default 10.0).
            request_id: Optional idempotency key — reuse to avoid duplicate execution.

        Returns:
            JSON string with execution result: {"task_id", "steps", "completed"}
        """
        headers = {}
        if request_id:
            headers["X-Request-Id"] = request_id

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=300.0)
        ) as client:
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
                        logger.debug("SSE line: %s", raw)

        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=10.0)) as client:
            status = await client.get(f"{vla_base}/vla/status")

        last = status.json().get("last_result")
        if last:
            import json as _json
            return _json.dumps(last)
        return '{"error": "no result returned"}'

    @mcp.tool()
    async def vla_stop() -> str:
        """Emergency stop — abort the current VLA episode immediately."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=10.0)) as client:
            r = await client.post(f"{vla_base}/vla/stop")
            return r.json()

    @mcp.tool()
    async def vla_status() -> dict:
        """Query the current VLA state."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=10.0)) as client:
            r = await client.get(f"{vla_base}/vla/status")
            return r.json()

    return mcp


def run_vla_server(
    vla_base: str = DEFAULT_VLA_BASE,
    port: int = 8765,
    config_path: str = None,
    cfg: "EvalRealConfig" = None,
):
    """Run the VLA HTTP server with the controlled eval loop.

    Args:
        vla_base: Base URL for the VLA HTTP server (default http://localhost:8765).
        port: Port for the HTTP server to listen on.
        config_path: Path to a YAML config file for eval (e.g. configs/g1_23_pi05_eval.yaml).
        cfg: Directly pass an EvalRealConfig object (takes precedence over config_path).
    """
    try:
        import uvicorn
    except ImportError:
        raise RuntimeError(
            "uvicorn not available — install with: pip install uvicorn"
        )
    from unitree_lerobot.eval_robot.mcp_server.vla_server import create_vla_server
    from unitree_lerobot.eval_robot.mcp_server.vla_controller import VLAController
    from unitree_lerobot.eval_robot.eval_g1_mcp import run_eval_with_controller
    from lerobot.configs import parser
    from unitree_lerobot.eval_robot.utils.utils import EvalRealConfig

    controller = VLAController()

    def run_eval(c: VLAController):
        nonlocal cfg
        if cfg is None and config_path:
            cfg = parser.load_yaml(config_path, EvalRealConfig)
        elif cfg is None:
            cfg = EvalRealConfig()
        run_eval_with_controller(cfg, c)

    # Resolve cfg before creating the app so we can pass episode_duration_s
    if cfg is None and config_path:
        cfg = parser.load_yaml(config_path, EvalRealConfig)
    elif cfg is None:
        cfg = EvalRealConfig()
    default_duration = cfg.episode_duration_s

    app = create_vla_server(controller, run_eval, default_episode_duration_s=default_duration)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


# ---------------------------------------------------------------------------
# Entry point: python -m unitree_lerobot.eval_robot.vla_mcp_server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    from unitree_lerobot.eval_robot.utils.utils import EvalRealConfig
    from lerobot.configs import parser as lerobot_parser

    parser_arg = argparse.ArgumentParser(description="VLA MCP Server")
    parser_arg.add_argument("--vla-base", default=DEFAULT_VLA_BASE, help="VLA HTTP server base URL")
    parser_arg.add_argument("--port", type=int, default=8765, help="Port for HTTP server")
    parser_arg.add_argument("--config", type=str, default=None, help="Path to eval YAML config")
    args, _ = parser_arg.parse_known_args()

    if args.config:
        run_vla_server(vla_base=args.vla_base, port=args.port, config_path=args.config)
    else:
        # Mimic the same flow as eval_g1.py: parse CLI args with @parser.wrap()
        # but keep our own --vla-base/--port handled separately above.
        saved_argv = sys.argv

        def main(cfg: EvalRealConfig):
            run_vla_server(vla_base=args.vla_base, port=args.port, cfg=cfg)

        wrapped = lerobot_parser.wrap()(main)

        # Reconstruct sys.argv: drop --vla-base, --port, --config from known args,
        # leaving only the config-class arguments (--policy.path, --repo_id, etc.)
        filtered = [
            arg for arg in saved_argv[1:]
            if not arg.startswith(("--vla-base=", "--port=", "--config="))
        ]
        sys.argv = [saved_argv[0]] + filtered

        try:
            wrapped()
        finally:
            sys.argv = saved_argv