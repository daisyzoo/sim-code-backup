"""Persistent, terminal-driven PI0.5 RTC experiment runner.

This runner intentionally does not expose an HTTP/MCP endpoint.  It loads the
policy and preprocessing stack once, then lets an operator change runtime
evaluation / RTC settings between runs without reloading model weights.
"""

import json
import logging
from contextlib import nullcontext
from dataclasses import asdict, fields
from datetime import datetime
from pathlib import Path
from typing import Any

import torch

from lerobot.configs import parser
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.processor.rename_processor import rename_stats
from lerobot.utils.utils import get_safe_torch_device, init_logging
from unitree_lerobot.eval_robot import eval_g1 as base_eval
from unitree_lerobot.eval_robot.eval_g1_rtc import EvalRealRTCConfig, predict_action_rtc
from unitree_lerobot.eval_robot.pi05_rtc_runtime import PI05RTCPolicyAdapter


logger = logging.getLogger(__name__)

_MODES = {"rtc_guided", "rtc_no_guidance", "sync_chunk"}
_LOAD_TIME_FIELDS = {
    "policy",
    "repo_id",
    "root",
    "episodes",
    "tokenizer_name_override",
}
_RUNNER_OWNED_FIELDS = {
    "persistent_runner_managed",
    "persistent_confirm_after_ready",
    "interactive_single_task",
    "interactive_task_selection",
    "rtc_enabled",
    "rtc_guidance_enabled",
    "rtc_execution_log_path",
}
_MENU_SECTIONS = {
    "Experiment / robot": (
        "frequency",
        "task_override",
        "motion",
        "send_real_robot",
        "arm_tau_mode",
        "constant_target_duration_s",
        "action_smoothing_enabled",
        "action_smoothing_arm_cutoff_hz",
        "action_smoothing_waist_cutoff_hz",
        "action_smoothing_chunk_blend_frames",
        "action_velocity_limits",
        "action_acceleration_limits",
    ),
    "RTC / scheduling": (
        "rtc_execution_horizon",
        "rtc_use_autograd_jacobian",
        "rtc_max_guidance_weight",
        "rtc_prefix_attention_schedule",
        "rtc_queue_threshold",
        "rtc_max_actions_during_inference",
        "rtc_inference_timeout_s",
        "rtc_latency_window",
        "rtc_snapshot_dir",
        "max_episode_wall_time_s",
        "run_until_q",
        "episode_duration_s",
    ),
}
_MENU_SETTABLE_FIELDS = frozenset(
    field_name for field_names in _MENU_SECTIONS.values() for field_name in field_names
)


def _coerce(value: str, current: Any) -> Any:
    """Parse a terminal value according to the existing runtime field type."""
    if isinstance(current, bool):
        normalized = value.strip().lower()
        if normalized not in {"true", "false"}:
            raise ValueError("expected true or false")
        return normalized == "true"
    if isinstance(current, int) and not isinstance(current, bool):
        return int(value)
    if isinstance(current, float):
        return float(value)
    if isinstance(current, (dict, list)):
        return json.loads(value)
    return value


def _safe_filename_piece(value: Any) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in str(value))


def _new_log_path(cfg: EvalRealRTCConfig, mode: str) -> Path:
    log_dir = Path("outputs/rtc_execution_logs/persistent_debug")
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    pieces = [
        timestamp,
        f"mode-{mode}",
        f"hz-{cfg.frequency:g}",
        f"guide-{str(cfg.rtc_guidance_enabled).lower()}",
        f"jac-{str(cfg.rtc_use_autograd_jacobian).lower()}",
        f"h-{cfg.rtc_execution_horizon}",
        f"maxact-{cfg.rtc_max_actions_during_inference}",
        f"q-{cfg.rtc_queue_threshold}",
        f"sched-{_safe_filename_piece(cfg.rtc_prefix_attention_schedule)}",
        f"gw-{cfg.rtc_max_guidance_weight:g}",
    ]
    return log_dir / ("_".join(pieces) + ".jsonl")


def _write_log_header(path: Path, cfg: EvalRealRTCConfig, mode: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "record_type": "rtc_run_config",
        "created_local_time": datetime.now().astimezone().isoformat(),
        "execution_mode": mode,
        "description": (
            "native synchronous PI0.5 chunks (infer 50 actions, then execute them)"
            if mode == "sync_chunk"
            else "asynchronous RTC action queue"
        ),
        "config": asdict(cfg),
    }
    path.write_text(json.dumps(record, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


class PersistentRTCDebugRunner:
    def __init__(self, cfg: EvalRealRTCConfig) -> None:
        self.cfg = cfg
        self.mode = "rtc_guided" if cfg.rtc_guidance_enabled else "rtc_no_guidance"
        self.cfg.persistent_runner_managed = True
        # Reuse eval_policy's single-task prompt as a post-ready confirmation.
        # It is opt-in so existing persistent debug launchers keep their old
        # behavior; the sorting launcher enables it explicitly.
        self.cfg.interactive_single_task = bool(cfg.persistent_confirm_after_ready)
        self.cfg.interactive_task_selection = False
        self.cfg.run_until_q = True

        self.device = get_safe_torch_device(cfg.policy.device, log=True)
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True

        logger.info("Persistent debug runner: loading dataset metadata and PI0.5 once.")
        self.dataset = LeRobotDataset(
            repo_id=cfg.repo_id,
            root=cfg.root if cfg.root else None,
            episodes=[cfg.episodes],
        )
        self.policy = make_policy(cfg=cfg.policy, ds_meta=self.dataset.meta)
        self.policy.eval()
        if hasattr(self.policy, "model") and hasattr(self.policy.model, "gradient_checkpointing_disable"):
            self.policy.model.gradient_checkpointing_disable()

        overrides = {
            "device_processor": {"device": cfg.policy.device},
            "rename_observations_processor": {"rename_map": cfg.rename_map},
        }
        if cfg.tokenizer_name_override:
            overrides["tokenizer_processor"] = {
                "tokenizer_name": cfg.tokenizer_name_override,
                "local_files_only": True,
            }
        self.preprocessor, self.postprocessor = make_pre_post_processors(
            policy_cfg=cfg.policy,
            pretrained_path=cfg.policy.pretrained_path,
            dataset_stats=rename_stats(self.dataset.meta.stats, cfg.rename_map),
            preprocessor_overrides=overrides,
        )
        logger.info("Persistent debug runner ready. Model weights remain resident until you quit.")

    def show(self) -> None:
        print("\nMode:", self.mode)
        print("Use: set <field> <value>")
        for section_name, field_names in _MENU_SECTIONS.items():
            print(f"\n{section_name}:")
            for field_name in field_names:
                print(f"  {field_name} = {getattr(self.cfg, field_name)!r}")
        print("\nMode is changed with: mode rtc_guided | rtc_no_guidance | sync_chunk")
        print("Other startup/model/robot fields are intentionally hidden and fixed for this process.")

    def set_value(self, field_name: str, raw_value: str) -> None:
        if field_name not in _MENU_SETTABLE_FIELDS:
            raise ValueError(
                f"{field_name} is not exposed by this debug menu; use show for available fields"
            )
        current = getattr(self.cfg, field_name)
        setattr(self.cfg, field_name, _coerce(raw_value, current))
        # Validate the RTC-specific subset immediately, before robot motion.
        self.cfg.make_rtc_config()
        print(f"Updated {field_name} = {getattr(self.cfg, field_name)!r}")

    def set_mode(self, mode: str) -> None:
        if mode not in _MODES:
            raise ValueError("mode must be one of: " + ", ".join(sorted(_MODES)))
        self.mode = mode
        self.cfg.rtc_enabled = mode != "sync_chunk"
        self.cfg.rtc_guidance_enabled = mode == "rtc_guided"
        print(f"Updated mode = {mode}")

    def run(self) -> None:
        cfg = self.cfg
        cfg.rtc_enabled = self.mode != "sync_chunk"
        cfg.rtc_guidance_enabled = self.mode == "rtc_guided"
        cfg.rtc_execution_log_path = str(_new_log_path(cfg, self.mode))
        _write_log_header(Path(cfg.rtc_execution_log_path), cfg, self.mode)
        print(f"\nStarting {self.mode}; log: {cfg.rtc_execution_log_path}")
        print("During motion, press q to stop this run. The model stays loaded afterwards.")

        adapter = None
        original_predict_action = base_eval.predict_action
        try:
            if self.mode == "sync_chunk":
                self.policy.reset()
                base_eval.eval_policy(cfg, self.dataset, self.policy, self.preprocessor, self.postprocessor)
                return

            cfg.make_rtc_config()
            adapter = PI05RTCPolicyAdapter(
                self.policy,
                self.postprocessor,
                cfg.make_rtc_config(),
                cfg.frequency,
                max_episode_wall_time_s=0.0,
                snapshot_dir=cfg.rtc_snapshot_dir,
            )
            base_eval.predict_action = predict_action_rtc
            base_eval.eval_policy(cfg, self.dataset, adapter, self.preprocessor, self.postprocessor)
        finally:
            base_eval.predict_action = original_predict_action
            if adapter is not None:
                adapter.close()

    def menu(self) -> None:
        print(
            "\nPersistent PI0.5 RTC debug menu\n"
            "  show                         show all runtime fields\n"
            "  mode <rtc_guided|rtc_no_guidance|sync_chunk>\n"
            "  set <field> <value>          change a runtime field\n"
            "  run                          execute once; q stops that run\n"
            "  help                         print this menu\n"
            "  quit                         unload model and exit\n"
            "Only fields shown by `show` can be changed. Bool values: true/false."
        )
        while True:
            try:
                line = input("persistent-rtc> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            if not line:
                continue
            command, *rest = line.split(maxsplit=2)
            try:
                if command in {"quit", "q", "exit"}:
                    return
                if command in {"help", "h"}:
                    self.menu_help()
                elif command == "show":
                    self.show()
                elif command == "mode" and len(rest) == 1:
                    self.set_mode(rest[0])
                elif command == "set" and len(rest) == 2:
                    self.set_value(rest[0], rest[1])
                elif command in {"run", "r"}:
                    self.run()
                else:
                    print("Unknown or incomplete command. Type help.")
            except Exception as exc:
                logger.exception("Persistent debug command failed")
                print(f"Command failed: {exc}")

    @staticmethod
    def menu_help() -> None:
        print("show | mode <rtc_guided|rtc_no_guidance|sync_chunk> | set <field> <value> | run | quit")


@parser.wrap()
def main(cfg: EvalRealRTCConfig) -> None:
    runner = PersistentRTCDebugRunner(cfg)
    try:
        runner.menu()
    finally:
        logger.info("Persistent debug runner exiting; releasing resident model process.")


if __name__ == "__main__":
    init_logging()
    main()
