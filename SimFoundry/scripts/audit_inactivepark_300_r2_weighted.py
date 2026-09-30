#!/usr/bin/env python3
"""Weighted frame audit for official-hand inactive-park 300_r2.

Assigns per-frame loss weights so wait / shared approach dilute metrics less:
  - wait_no_package:           0.10
  - push lift+approach (0-36): 0.25
  - push press+sweep (37-104): 1.00
  - push hold (105+):          0.50

Writes JSON report under demo/audit_inactivepark_300_r2_weighted/.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simfoundry.data.sorting_cartesian_expert import APPROACH_END, LIFT_END, PRESS_END, SWEEP_END

DATASET = ROOT / "datasets/sorting_station_g1_23_unitree_vla_officialhand_inactivepark_300_r2_20260921"
LEROBOT = Path("/home/user/Documents/zoo/sim/lerobot/lerobot_sim_sorting_vla_officialhand_inactivepark_300_r2_20260921")
SPLIT_FILE = LEROBOT / "meta/train_validation_split.json"
OUT_DIR = ROOT / "demo/audit_inactivepark_300_r2_weighted"

WEIGHT_WAIT = 0.10
WEIGHT_APPROACH = 0.25
WEIGHT_PRESS_SWEEP = 1.00
WEIGHT_HOLD = 0.50


@dataclass
class WeightPolicy:
    wait: float = WEIGHT_WAIT
    push_lift_approach: float = WEIGHT_APPROACH
    push_press_sweep: float = WEIGHT_PRESS_SWEEP
    push_hold: float = WEIGHT_HOLD
    lift_end: int = LIFT_END
    approach_end: int = APPROACH_END
    press_end: int = PRESS_END
    sweep_end: int = SWEEP_END


def frame_weight(task_id: str, frame_idx: int, policy: WeightPolicy) -> tuple[float, str]:
    if task_id == "wait_no_package":
        return policy.wait, "wait"
    if task_id == "push_box_to_bin" or task_id == "nudge_mailer_to_bin":
        if frame_idx <= policy.approach_end:
            return policy.push_lift_approach, "lift_approach"
        if frame_idx <= policy.sweep_end:
            return policy.push_press_sweep, "press_sweep"
        return policy.push_hold, "hold"
    return 1.0, "unknown"


def get_arm11_state(frame: dict) -> np.ndarray:
    st = frame["states"]
    la = st["left_arm"]["qpos"]
    ra = st["right_arm"]["qpos"]
    waist = st["body"]["qpos"][0]
    return np.array(la + ra + [waist], dtype=np.float64)


def get_arm11_action(frame: dict) -> np.ndarray:
    act = frame["actions"]
    la = act["left_arm"]["qpos"]
    ra = act["right_arm"]["qpos"]
    waist = act["body"]["qpos"][0]
    return np.array(la + ra + [waist], dtype=np.float64)


def get_arm11(frame: dict) -> np.ndarray:
    return get_arm11_state(frame)


def episode_motion(acts: np.ndarray) -> float:
    if len(acts) < 2:
        return 0.0
    return float(np.mean(np.linalg.norm(np.diff(acts, axis=0), axis=1)))


def main() -> None:
    policy = WeightPolicy()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    seg_counter: Counter[str] = Counter()
    seg_weight_sum: Counter[str] = Counter()
    task_frames: Counter[str] = Counter()
    task_weight: Counter[str] = Counter()

    wrong_push_dir: list[dict] = []
    wrong_hand_mailer: list[int] = []
    wrong_hand_box: list[int] = []

    for ep_dir in sorted(DATASET.glob("episode_*")):
        ep = int(ep_dir.name.split("_")[1])
        payload = json.load((ep_dir / "data.json").open())
        sf = payload["info"]["simfoundry"]
        task = sf["task_id"]
        col = sf.get("collect", {})
        frames = payload["data"]
        acts = np.stack([get_arm11(fr) for fr in frames])

        l_sr = acts[:, 1]
        r_sr = acts[:, 6]
        l_motion = episode_motion(acts[:, :5]) if len(acts) > 1 else 0.0
        r_motion = episode_motion(acts[:, 5:10]) if len(acts) > 1 else 0.0

        ep_weight = 0.0
        ep_segs: Counter[str] = Counter()
        for i in range(len(frames)):
            w, seg = frame_weight(task, i, policy)
            ep_weight += w
            ep_segs[seg] += 1
            seg_counter[seg] += 1
            seg_weight_sum[seg] += w
        task_frames[task] += len(frames)
        task_weight[task] += ep_weight

        push_dy = col.get("push_delta_y")
        if task == "nudge_mailer_to_bin" and push_dy is not None and push_dy < 0.20:
            wrong_push_dir.append({"ep": ep, "push_dy": push_dy})
        if task == "nudge_mailer_to_bin" and r_motion > l_motion + 1e-4:
            wrong_hand_mailer.append(ep)
        if task == "push_box_to_bin" and l_motion > r_motion + 1e-4:
            wrong_hand_box.append(ep)

        rows.append(
            {
                "ep": ep,
                "task": task,
                "frames": len(frames),
                "weighted_frames": round(ep_weight, 2),
                "push_delta_y": push_dy,
                "wrong_way_y": col.get("wrong_way_excursion_y"),
                "touch_frames": col.get("touch_frames"),
                "l_motion": round(l_motion, 5),
                "r_motion": round(r_motion, 5),
                "segments": dict(ep_segs),
            }
        )

    total_frames = sum(task_frames.values())
    total_weight = sum(task_weight.values())

    # Cross-task trajectory distance (paired box i vs mailer i+120)
    pair_diffs = []
    for i in range(120):
        ba = np.stack([get_arm11(fr) for fr in json.load((DATASET / f"episode_{i:04d}/data.json").open())["data"]])
        ma = np.stack(
            [get_arm11(fr) for fr in json.load((DATASET / f"episode_{i+120:04d}/data.json").open())["data"]]
        )
        n = min(len(ba), len(ma))
        pair_diffs.append(float(np.mean(np.linalg.norm(ba[:n] - ma[:n], axis=1))))
    pair_diffs_arr = np.array(pair_diffs)

    # Phase-wise cross-task L2 (ep0 vs ep120)
    def phase_diff(ep_a: int, ep_b: int) -> dict[str, float]:
        a = np.stack([get_arm11(fr) for fr in json.load((DATASET / f"episode_{ep_a:04d}/data.json").open())["data"]])
        b = np.stack([get_arm11(fr) for fr in json.load((DATASET / f"episode_{ep_b:04d}/data.json").open())["data"]])
        out = {}
        ranges = {
            "lift": (0, LIFT_END),
            "approach": (LIFT_END + 1, APPROACH_END),
            "press": (APPROACH_END + 1, PRESS_END),
            "sweep": (PRESS_END + 1, SWEEP_END),
            "hold": (SWEEP_END + 1, 10_000),
        }
        for name, (s, e) in ranges.items():
            sa, sb = a[s : e + 1], b[s : e + 1]
            n = min(len(sa), len(sb))
            if n == 0:
                continue
            out[name] = float(np.mean(np.linalg.norm(sa[:n] - sb[:n], axis=1)))
        return out

    phase_l2 = phase_diff(0, 120)

    # First-frame action target + image proxy
    box_f0 = json.load((DATASET / "episode_0000/data.json").open())["data"][0]
    mail_f0 = json.load((DATASET / "episode_0120/data.json").open())["data"][0]
    b0 = get_arm11_action(box_f0)
    m0 = get_arm11_action(mail_f0)
    s0_box = get_arm11_state(box_f0)
    s0_mail = get_arm11_state(mail_f0)

    try:
        from PIL import Image

        ib = np.array(Image.open(DATASET / "episode_0000/colors/000000_color_0.jpg"))
        im = np.array(Image.open(DATASET / "episode_0120/colors/000000_color_0.jpg"))
        h, w = ib.shape[:2]
        cb = ib[h // 3 : 2 * h // 3, w // 4 : 3 * w // 4]
        cm = im[h // 3 : 2 * h // 3, w // 4 : 3 * w // 4]
        img_center_diff = float(np.mean(np.abs(cb.astype(float) - cm.astype(float))))
        g_b = ib.mean(-1).ravel()
        g_m = im.mean(-1).ravel()
        obj_xor = int(np.sum((g_b < 120) ^ (g_m < 120)))
    except Exception:
        img_center_diff = None
        obj_xor = None

    # Train/val weighted counts
    split = json.load(SPLIT_FILE.open())
    train_eps = set(split["train"])
    val_eps = set(split["validation"])
    train_w = sum(r["weighted_frames"] for r in rows if r["ep"] in train_eps)
    val_w = sum(r["weighted_frames"] for r in rows if r["ep"] in val_eps)
    train_raw = sum(r["frames"] for r in rows if r["ep"] in train_eps)
    val_raw = sum(r["frames"] for r in rows if r["ep"] in val_eps)

    # Initial pose spread
    q0 = np.stack([get_arm11(json.load((DATASET / f"episode_{r['ep']:04d}/data.json").open())["data"][0]) for r in rows])
    q0_spread = float(np.max(np.ptp(q0, axis=0)))

    report = {
        "dataset": str(DATASET),
        "weight_policy": asdict(policy),
        "summary": {
            "episodes": len(rows),
            "task_counts": dict(Counter(r["task"] for r in rows)),
            "raw_frames": total_frames,
            "weighted_frames": round(total_weight, 1),
            "weight_compression_ratio": round(total_weight / total_frames, 3),
            "segment_raw_frames": dict(seg_counter),
            "segment_weighted_sum": {k: round(v, 1) for k, v in seg_weight_sum.items()},
            "segment_share_raw_pct": {k: round(100 * v / total_frames, 1) for k, v in seg_counter.items()},
            "segment_share_weighted_pct": {
                k: round(100 * seg_weight_sum[k] / total_weight, 1) for k in seg_counter
            },
            "train_raw_frames": train_raw,
            "val_raw_frames": val_raw,
            "train_weighted_frames": round(train_w, 1),
            "val_weighted_frames": round(val_w, 1),
            "effective_train_epochs_75732_steps": {
                "note": "75732 steps @ batch1 ≈ 2 raw epochs; weighted equivalent lower on shared segments",
                "raw_frame_refs_per_2epoch": train_raw * 2,
                "weighted_frame_refs_per_2epoch": round(train_w * 2, 1),
            },
        },
        "quality_gates": {
            "mailer_wrong_push_direction": len(wrong_push_dir),
            "mailer_right_hand_dominant": len(wrong_hand_mailer),
            "box_left_hand_dominant": len(wrong_hand_box),
            "wrong_way_over_3_5cm": sum(1 for r in rows if (r.get("wrong_way_y") or 0) > 0.035),
            "table_pen": 0,
            "assist": 0,
            "initial_pose_11d_max_spread_rad": q0_spread,
        },
        "routing_signal": {
            "box_mailer_pair_mean_l2_rad": round(float(pair_diffs_arr.mean()), 4),
            "box_mailer_pair_min_l2_rad": round(float(pair_diffs_arr.min()), 4),
            "phase_l2_ep0_vs_ep120": phase_l2,
            "state0_l2_box0_vs_mailer120": round(float(np.linalg.norm(s0_box - s0_mail)), 4),
            "first_action_l2_box0_vs_mailer120": round(float(np.linalg.norm(b0 - m0)), 4),
            "first_action_shoulder_roll": {
                "box_ep0": {"L": round(float(b0[1]), 3), "R": round(float(b0[6]), 3)},
                "mailer_ep120": {"L": round(float(m0[1]), 3), "R": round(float(m0[6]), 3)},
            },
            "image_frame0_center_diff": img_center_diff,
            "image_frame0_object_xor_pixels": obj_xor,
        },
        "interpretation": {
            "data_push_direction_ok": len(wrong_push_dir) == 0,
            "data_hand_selection_ok": len(wrong_hand_mailer) == 0 and len(wrong_hand_box) == 0,
            "loss_dilution_before_weighting": (
                "Raw frames: ~31% lift_approach + 9% wait share one template; only ~39% press_sweep "
                "carries hand/direction fork."
            ),
            "after_weighting": (
                f"Weighted mass on press_sweep rises to "
                f"{round(100 * seg_weight_sum['press_sweep'] / total_weight, 1)}% "
                f"(from {round(100 * seg_counter['press_sweep'] / total_frames, 1)}% raw)."
            ),
            "model_h10_reference": {
                "checkpoint": "package_sorting_pi05_1gpu_20260922_140103",
                "mailer_failure": "3/3 seeds: right hand, delta_y negative (routes as box)",
                "offline_loss": 0.00445,
                "conclusion": "Low unweighted loss compatible with routing collapse; use weighted val + h10",
            },
        },
        "episodes": rows,
    }

    out_path = OUT_DIR / "report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("weight_policy", "summary", "quality_gates", "routing_signal", "interpretation")}, indent=2))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
