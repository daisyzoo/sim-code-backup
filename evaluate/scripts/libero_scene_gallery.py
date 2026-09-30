#!/usr/bin/env python3
"""Render official LIBERO scenes into a gallery (no trained policy)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

EVAL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EVAL_ROOT / "scripts"))
from libero_eval_demo import (  # noqa: E402
    dummy_eval,
    render_suite_catalog,
)

os.environ.setdefault("LIBERO_CONFIG_PATH", str(EVAL_ROOT / "libero_runtime"))
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

OUT = EVAL_ROOT / "outputs" / "libero_scene_gallery"
GALLERIES = [
    ("libero_spatial", "厨房台：同一组物体，只改碗的空间关系"),
    ("libero_object", "客厅桌：同一技能，把不同包装食品放进篮子"),
    ("libero_goal", "厨房台：物体摆放固定，只改目标（开抽屉/开火/放碗）"),
    ("libero_10", "长程：厨房 / 客厅 / 书桌混在一起"),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for suite, note in GALLERIES:
        dest = OUT / suite
        dest.mkdir(parents=True, exist_ok=True)
        print(f"\n=== {suite} ===", flush=True)
        rows, sheet = render_suite_catalog(suite, dest, camera_size=320)
        eval_result = dummy_eval(
            suite_name=suite,
            task_id=0,
            n_episodes=1,
            max_steps=16,
            out_dir=dest,
            camera_size=320,
        )
        index.append(
            {
                "suite": suite,
                "note": note,
                "n_tasks": len(rows),
                "contact_sheet": str(sheet.relative_to(OUT)),
                "video": eval_result.get("video"),
                "language_ep0": eval_result.get("language"),
                "tasks": rows,
            }
        )

    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# LIBERO 现成场景效果",
        "",
        "全部是官方 BDDL + 官方 init state 的第三人称 `agentview`。视频是全零动作，机械臂基本不动，用来看场景本身。",
        "",
    ]
    for item in index:
        lines += [
            f"## {item['suite']}",
            "",
            item["note"],
            "",
            f"![{item['suite']}]({item['contact_sheet']})",
            "",
            f"短视频（task 0）：`{item['suite']}/rollout/{Path(item['video']).name if item['video'] else ''}`",
            "",
        ]
        for row in item["tasks"]:
            lines.append(f"- `{row['task_id']}` {row['language']}")
        lines.append("")
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[done] {OUT}", flush=True)


if __name__ == "__main__":
    main()
