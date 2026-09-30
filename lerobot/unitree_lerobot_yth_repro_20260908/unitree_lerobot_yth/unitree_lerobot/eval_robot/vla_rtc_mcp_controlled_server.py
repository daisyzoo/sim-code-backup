"""Controlled HTTP/MCP server for continuous PI0.5 RTC execution."""

import argparse
import logging
import sys

from unitree_lerobot.eval_robot.vla_mcp_controlled_server import (
    DEFAULT_VLA_BASE,
    configure_logging,
    create_vla_controlled_server,
)

logger = logging.getLogger("vla_rtc_mcp_controlled")
logger.setLevel(logging.INFO)


def run_vla_rtc_server(
    vla_base: str = DEFAULT_VLA_BASE,
    port: int = 8765,
    config_path: str | None = None,
    cfg=None,
) -> None:
    configure_logging()
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("uvicorn not available — install with: pip install uvicorn") from exc

    from lerobot.configs import parser
    from unitree_lerobot.eval_robot.eval_g1_rtc_mcp_controlled import (
        EvalRealRTCMCPConfig,
        run_rtc_eval_with_controller,
    )
    from unitree_lerobot.eval_robot.mcp_server.vla_controller import VLAController

    if cfg is None and config_path:
        logger.info("Loading RTC MCP eval config from %s", config_path)
        cfg = parser.load_yaml(config_path, EvalRealRTCMCPConfig)
    elif cfg is None:
        cfg = EvalRealRTCMCPConfig()

    controller = VLAController()

    def run_eval(active_controller: VLAController) -> None:
        run_rtc_eval_with_controller(cfg, active_controller)

    logger.info(
        "RTC MCP config ready: policy=%s frequency=%.1fHz default_duration=%.1fs "
        "max_duration=%.1fs inference_timeout=%.1fs send_real_robot=%s",
        getattr(cfg.policy, "pretrained_path", None),
        cfg.frequency,
        cfg.episode_duration_s,
        cfg.max_episode_wall_time_s,
        cfg.rtc_inference_timeout_s,
        cfg.send_real_robot,
    )
    app = create_vla_controlled_server(
        controller,
        run_eval,
        default_episode_duration_s=cfg.episode_duration_s,
        vla_base=vla_base,
        mcp_default_duration_s=cfg.episode_duration_s,
        max_task_duration_s=cfg.max_episode_wall_time_s,
        allow_task_duration_override=False,
    )
    logger.info("Starting continuous RTC MCP server on 0.0.0.0:%s", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    configure_logging()
    from lerobot.configs import parser as lerobot_parser
    from unitree_lerobot.eval_robot.eval_g1_rtc_mcp_controlled import EvalRealRTCMCPConfig

    argument_parser = argparse.ArgumentParser(description="Continuous PI0.5 RTC MCP server")
    argument_parser.add_argument("--vla-base", default=DEFAULT_VLA_BASE)
    argument_parser.add_argument("--port", type=int, default=8765)
    argument_parser.add_argument("--config", type=str, default=None)
    args, _ = argument_parser.parse_known_args()

    if args.config:
        run_vla_rtc_server(vla_base=args.vla_base, port=args.port, config_path=args.config)
    else:
        saved_argv = sys.argv

        def main(parsed_cfg: EvalRealRTCMCPConfig) -> None:
            run_vla_rtc_server(vla_base=args.vla_base, port=args.port, cfg=parsed_cfg)

        wrapped = lerobot_parser.wrap()(main)
        sys.argv = [saved_argv[0]] + [
            arg
            for arg in saved_argv[1:]
            if not arg.startswith(("--vla-base=", "--port=", "--config="))
        ]
        try:
            wrapped()
        finally:
            sys.argv = saved_argv
