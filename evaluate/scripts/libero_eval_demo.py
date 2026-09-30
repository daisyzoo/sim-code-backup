#!/usr/bin/env python3
"""Run the official LIBERO scene eval demo (README Task section, plus a suite catalog).

This is an environment / protocol smoke test, not a trained-policy leaderboard run.
It uses dummy zero actions, so success rate is expected to be 0. The point is to
load public BDDL scenes, official init states, and the OffScreenRenderEnv loop.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

EVAL_ROOT = Path(__file__).resolve().parents[1]
LIBERO_ROOT = EVAL_ROOT / "LIBERO"
OUT_DEFAULT = EVAL_ROOT / "outputs" / "libero_eval_demo"

os.environ.setdefault("LIBERO_CONFIG_PATH", str(EVAL_ROOT / "libero_runtime"))
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

sys.path.insert(0, str(LIBERO_ROOT))


def _to_uint8_hwc(img):
    import numpy as np

    arr = np.asarray(img)
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype("uint8")
    if arr.ndim == 3 and arr.shape[0] in (1, 3) and arr.shape[-1] not in (1, 3):
        arr = np.transpose(arr, (1, 2, 0))
    return arr


def _flip_ud(img):
    import numpy as np

    return np.ascontiguousarray(img[::-1])


def _save_jpg(path: Path, img) -> None:
    import cv2

    path.parent.mkdir(parents=True, exist_ok=True)
    bgr = img[..., ::-1]
    cv2.imwrite(str(path), bgr)


def _contact_sheet(images, cols: int = 5):
    import numpy as np

    if not images:
        raise ValueError("no images")
    h, w = images[0].shape[:2]
    rows = (len(images) + cols - 1) // cols
    canvas = np.zeros((rows * h, cols * w, 3), dtype=images[0].dtype)
    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        canvas[r * h : (r + 1) * h, c * w : (c + 1) * w] = im
    return canvas


def _load_init_states(task_suite, task_id: int):
    return task_suite.get_task_init_states(task_id)


def _obs_image(obs, key: str = "agentview_image"):
    if key in obs:
        img = obs[key]
    else:
        candidates = [k for k in obs if "image" in k]
        if not candidates:
            raise KeyError(f"no image in obs keys={list(obs.keys())}")
        img = obs[candidates[0]]
        key = candidates[0]
    return _flip_ud(_to_uint8_hwc(img)), key


def catalog_suites():
    from libero.libero import benchmark

    benchmark_dict = benchmark.get_benchmark_dict()
    suites = {}
    for name in ["libero_spatial", "libero_object", "libero_goal", "libero_10", "libero_90"]:
        if name not in benchmark_dict:
            continue
        suite = benchmark_dict[name]()
        suites[name] = [
            {
                "task_id": i,
                "name": suite.get_task(i).name,
                "language": suite.get_task(i).language,
            }
            for i in range(suite.n_tasks)
        ]
    return suites


def render_suite_catalog(suite_name: str, out_dir: Path, camera_size: int = 256):
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv

    suite = benchmark.get_benchmark_dict()[suite_name]()
    frames = []
    rows = []
    for task_id in range(suite.n_tasks):
        task = suite.get_task(task_id)
        bddl = os.path.join(get_libero_path("bddl_files"), task.problem_folder, task.bddl_file)
        env = OffScreenRenderEnv(
            bddl_file_name=bddl,
            camera_heights=camera_size,
            camera_widths=camera_size,
        )
        env.seed(0)
        env.reset()
        init_states = _load_init_states(suite, task_id)
        obs = env.set_init_state(init_states[0])
        img, key = _obs_image(obs)
        frame_path = out_dir / "catalog" / f"{task_id:02d}_{task.name}.jpg"
        _save_jpg(frame_path, img)
        frames.append(img)
        rows.append(
            {
                "task_id": task_id,
                "name": task.name,
                "language": task.language,
                "init_states": int(len(init_states)),
                "frame": str(frame_path.relative_to(out_dir)),
                "image_key": key,
            }
        )
        env.close()
        print(f"[catalog] {suite_name} {task_id}: {task.language}", flush=True)

    sheet = _contact_sheet(frames, cols=min(5, len(frames)))
    sheet_path = out_dir / f"{suite_name}_init_contact_sheet.jpg"
    _save_jpg(sheet_path, sheet)
    return rows, sheet_path


def dummy_eval(
    suite_name: str,
    task_id: int,
    n_episodes: int,
    max_steps: int,
    out_dir: Path,
    camera_size: int = 256,
):
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv

    suite = benchmark.get_benchmark_dict()[suite_name]()
    task = suite.get_task(task_id)
    bddl = os.path.join(get_libero_path("bddl_files"), task.problem_folder, task.bddl_file)
    env = OffScreenRenderEnv(
        bddl_file_name=bddl,
        camera_heights=camera_size,
        camera_widths=camera_size,
        horizon=max(max_steps + 10, 50),
    )
    env.seed(0)
    init_states = _load_init_states(suite, task_id)
    dummy_action = [0.0] * 7
    episodes = []
    video_frames = []

    for ep in range(n_episodes):
        env.reset()
        init_state_id = ep % len(init_states)
        obs = env.set_init_state(init_states[init_state_id])
        img, _ = _obs_image(obs)
        _save_jpg(out_dir / "rollout" / f"ep{ep:02d}_step000.jpg", img)
        if ep == 0:
            video_frames.append(img)
        success = False
        done = False
        last_reward = 0.0
        for step in range(max_steps):
            obs, reward, done, info = env.step(dummy_action)
            last_reward = float(reward)
            success = bool(env.check_success())
            img, _ = _obs_image(obs)
            if step in {max_steps // 2, max_steps - 1}:
                _save_jpg(out_dir / "rollout" / f"ep{ep:02d}_step{step + 1:03d}.jpg", img)
            if ep == 0 and step % 2 == 1:
                video_frames.append(img)
            if success or done:
                break
        episodes.append(
            {
                "episode": ep,
                "init_state_id": int(init_state_id),
                "steps": step + 1,
                "success": success,
                "done": bool(done),
                "last_reward": last_reward,
            }
        )
        print(
            f"[eval] ep={ep} init={init_state_id} success={success} steps={step + 1}",
            flush=True,
        )

    env.close()
    if video_frames:
        try:
            import imageio

            mp4 = out_dir / "rollout" / "dummy_policy_ep00.mp4"
            mp4.parent.mkdir(parents=True, exist_ok=True)
            imageio.mimsave(str(mp4), video_frames, fps=10)
            video_rel = str(mp4.relative_to(out_dir))
        except Exception as exc:  # noqa: BLE001
            video_rel = f"mp4_failed: {exc}"
    else:
        video_rel = None

    n_ok = sum(1 for e in episodes if e["success"])
    return {
        "suite": suite_name,
        "task_id": task_id,
        "task_name": task.name,
        "language": task.language,
        "policy": "dummy_zero_action",
        "n_episodes": n_episodes,
        "max_steps": max_steps,
        "successes": n_ok,
        "success_rate": n_ok / max(n_episodes, 1),
        "episodes": episodes,
        "video": video_rel,
        "note": "dummy policy is expected to fail; this checks the official eval loop",
    }


def parse_args():
    p = argparse.ArgumentParser(description="LIBERO official scene eval demo")
    p.add_argument("--suite", default="libero_spatial")
    p.add_argument("--task-id", type=int, default=0)
    p.add_argument("--n-episodes", type=int, default=2)
    p.add_argument("--max-steps", type=int, default=20)
    p.add_argument("--camera-size", type=int, default=256)
    p.add_argument("--skip-catalog", action="store_true")
    p.add_argument("--out", type=Path, default=OUT_DEFAULT)
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()

    suites = catalog_suites()
    catalog_rows = None
    sheet_path = None
    if not args.skip_catalog:
        catalog_rows, sheet_path = render_suite_catalog(
            args.suite, out_dir, camera_size=args.camera_size
        )
    eval_result = dummy_eval(
        suite_name=args.suite,
        task_id=args.task_id,
        n_episodes=args.n_episodes,
        max_steps=args.max_steps,
        out_dir=out_dir,
        camera_size=args.camera_size,
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.time() - started, 2),
        "libero_root": str(LIBERO_ROOT),
        "config_path": os.environ.get("LIBERO_CONFIG_PATH"),
        "mujoco_gl": os.environ.get("MUJOCO_GL"),
        "suites": {k: len(v) for k, v in suites.items()},
        "suite_tasks": suites,
        "catalog": catalog_rows,
        "contact_sheet": None
        if sheet_path is None
        else str(sheet_path.relative_to(out_dir)),
        "dummy_eval": eval_result,
    }
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# LIBERO 评测 demo 结果",
        "",
        f"- 时间: `{report['generated_at']}`",
        f"- 耗时: `{report['elapsed_sec']}s`",
        f"- 套件任务数: `{report['suites']}`",
        f"- dummy 评测: `{eval_result['suite']}` task `{eval_result['task_id']}`",
        f"- 指令: {eval_result['language']}",
        f"- 成功率: **{eval_result['success_rate']:.0%}** ({eval_result['successes']}/{eval_result['n_episodes']})，策略为全零动作，预期失败",
        "",
    ]
    if sheet_path is not None:
        md_lines += [
            "## Spatial 十任务初始场景",
            "",
            f"![contact sheet]({sheet_path.name})",
            "",
        ]
        for row in catalog_rows or []:
            md_lines.append(f"- `{row['task_id']}` {row['language']}")
        md_lines.append("")
    md_lines += [
        "## Dummy rollout",
        "",
        f"视频: `{eval_result.get('video')}`",
        "",
        "完整 JSON 见 `report.json`。",
        "",
    ]
    (out_dir / "README.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[done] wrote {report_path}", flush=True)


if __name__ == "__main__":
    main()
