#!/usr/bin/env python3
"""Merge routing diagnostic artifacts into REPORT.md + conclusions.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_json(path: Path):
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _h10_mailer(summary_path: Path) -> dict | None:
    data = _read_json(summary_path)
    if not data:
        return None
    for row in data.get("summary", []):
        if row.get("task_id") == "mailer_only":
            tbh = row.get("touches_by_hand", {})
            return {
                "mailer_dy": row.get("mailer_xy_delta", [None, None])[1],
                "right_mailer_touches": tbh.get("right_mailer", 0),
                "left_mailer_touches": tbh.get("left_mailer", 0),
            }
    return None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("/home/user/Documents/zoo/sim/SimFoundry/demo/diagnostic_routing_verification"),
    )
    args = p.parse_args()
    out = args.out_dir

    open_loop = _read_json(out / "01_open_loop.json")
    val_loss = _read_json(out / "03_per_task_val_loss.json")
    clf = _read_json(out / "05_frame0_classifier.json")
    h10 = {
        "default": _h10_mailer(out / "02_h10_default/summary.json"),
        "oracle_mailer": _h10_mailer(out / "02_h10_oracle_mailer_prompt/summary.json"),
        "wrong_box": _h10_mailer(out / "02_h10_wrong_box_prompt/summary.json"),
        "mailer_only_train": _h10_mailer(out / "04_h10_mailer_only_train/summary.json"),
    }

    conclusions: list[str] = []

    if open_loop:
        c = open_loop["collapse_metrics"]
        if c.get("mailer_f0_pred_closer_to_box_than_mailer_gt"):
            conclusions.append(
                "① Open-loop：黑袋首帧预测更接近纸盒 GT → **模式坍缩到盒模板**。"
            )
        else:
            conclusions.append("① Open-loop：黑袋首帧预测更接近黑袋 GT（未坍缩到盒）。")
        pa = open_loop.get("mailer_f0_prompt_ablation", {})
        if pa.get("language_sensitive"):
            conclusions.append("① Open-loop prompt 消融：换 prompt 会改变输出 → 模型**能读语言**。")
        else:
            conclusions.append(
                "① Open-loop prompt 消融：oracle/wrong prompt 输出几乎相同 → 模型**几乎不用语言**。"
            )

    if val_loss and "_delta_mailer_minus_box" in val_loss:
        d = val_loss["_delta_mailer_minus_box"]
        if d > 0.001:
            conclusions.append(f"③ Val loss：mailer ({val_loss['nudge_mailer_to_bin']['mean_loss']:.4f}) > box ({val_loss['push_box_to_bin']['mean_loss']:.4f}) → 黑袋学得比盒差。")
        else:
            conclusions.append("③ Val loss：mailer 与 box 接近 → 离线 loss 看不出路由失败。")

    if clf:
        acc = clf.get("test_accuracy", 0)
        if acc >= 0.85:
            conclusions.append(f"⑤ 视觉分类 frame0 acc={acc:.1%} → **能看见**盒/袋，问题在 vision→action 绑定。")
        else:
            conclusions.append(f"⑤ 视觉分类 frame0 acc={acc:.1%} → 首帧视觉本身也难分。")

    if h10.get("oracle_mailer") and h10.get("wrong_box"):
        o, w = h10["oracle_mailer"], h10["wrong_box"]
        if o and w and o.get("right_mailer_touches") == w.get("right_mailer_touches"):
            conclusions.append("② Oracle h10：换 prompt 后黑袋选手/Δy 几乎不变 → **闭环不吃 prompt**。")
        elif o and o.get("left_mailer_touches", 0) > o.get("right_mailer_touches", 0):
            conclusions.append("② Oracle h10：正确短 prompt 使黑袋改走左手 → **语言路由可行但未在默认 prompt 下触发**。")

    m4 = h10.get("mailer_only_train")
    if m4:
        if m4.get("left_mailer_touches", 0) > m4.get("right_mailer_touches", 0) and (m4.get("mailer_dy") or 0) >= 0.20:
            conclusions.append("④ Mailer-only 重训：黑袋 h10 通过 → 盒任务干扰是主因之一。")
        elif m4.get("right_mailer_touches", 0) > 0:
            conclusions.append("④ Mailer-only 重训：黑袋仍走右手 → 非单纯 box 样本干扰，更像视觉/先验坍缩。")

    payload = {"h10_mailer": h10, "conclusions": conclusions}
    (out / "CONCLUSIONS.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# 路由失败诊断报告",
        "",
        f"输出目录：`{out}`",
        "",
        "## 结论摘要",
        "",
    ]
    for i, c in enumerate(conclusions, 1):
        lines.append(f"{i}. {c}")
    lines.extend(["", "## 详细结果", ""])
    if open_loop:
        c = open_loop["collapse_metrics"]
        lines.append("### ① Open-loop")
        lines.append(f"- mailer_f0 pred vs box_gt L2: {c['mailer_f0_pred_vs_box_gt_l2']:.3f}")
        lines.append(f"- mailer_f0 pred vs mailer_gt L2: {c['mailer_f0_pred_vs_mailer_gt_l2']:.3f}")
        lines.append(f"- {c['interpretation']}")
        pa = open_loop["mailer_f0_prompt_ablation"]
        lines.append(f"- prompt ablation L2(oracle vs wrong): {pa.get('oracle_vs_wrong_l2', 'n/a')}")
    if val_loss:
        lines.append("")
        lines.append("### ③ Per-task val loss")
        for task in ("push_box_to_bin", "nudge_mailer_to_bin", "wait_no_package"):
            if task in val_loss:
                lines.append(f"- {task}: mean={val_loss[task]['mean_loss']:.6f} n={val_loss[task]['frames']}")
    if clf:
        lines.append("")
        lines.append(f"### ⑤ Frame0 classifier acc={clf.get('test_accuracy', 0):.1%}")
    lines.append("")
    lines.append("### ② / ④ h10 黑袋段")
    for name, row in h10.items():
        if row:
            lines.append(
                f"- {name}: Δy={row.get('mailer_dy')} L_touch={row.get('left_mailer_touches')} R_touch={row.get('right_mailer_touches')}"
            )
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}/REPORT.md and CONCLUSIONS.json")


if __name__ == "__main__":
    main()
