"""Quality gates for sorting-station teleop collection.

Only episodes that pass all checks should be written to disk:
  - active palm stays above the table (no table penetration)
  - active hand contacts the target parcel during the push phase
  - parcel finishes stably inside the correct lateral sorting area
    (+Y left / −Y right) while remaining on the table
  - episode length near 120 frames with per-episode jitter (not a fixed horizon)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import torch
from isaaclab.utils.math import quat_apply

from simfoundry.calibration.sorting_station import TABLE_TOP_Z

TABLE_Y_HALF = 0.75
MIN_TOUCH_FRAMES = 3
# A sort means crossing a world-coordinate lateral zone, not reaching an
# off-camera bin. The boundary stays inside the 1.5 m-wide tabletop and can
# be overlaid in diagnostics without leaking a marker into training images.
# Success is reaching the visible left/right work area, not an off-camera bin.
# A 15 cm centre gate puts the outer edge of either 14--15 cm package beyond
# 22 cm and remains reachable by the non-crossing five-DoF arm.
MIN_PUSH_DISPLACEMENT_Y = 0.15
SORTING_ZONE_Y = 0.15
SORTING_ZONE_STABLE_FRAMES = 10
# Analytic parcel cores removed the previous 7--11 cm persistent drift, but a
# zero-action reset still shows a damped contact ring of up to ~3 cm.  Reject
# motion beyond that measured physics floor rather than selecting only lucky
# solver phases.
MAX_WRONG_WAY_EXCURSION_Y = 0.035
MIN_PARCEL_START_X = 0.35
MAX_PARCEL_START_ABS_Y = 0.04
MIN_ACTIVE_HAND_DY = 0.08
MAX_INACTIVE_HAND_DY = 0.13
OFFTABLE_XY = 2.5
PARCEL_DROP_Z = TABLE_TOP_Z - 0.10
# Waiting clips used to contribute only about 4% of training frames, despite
# being 20% of episodes. Give the no-package class enough temporal weight to
# teach an actual stationary action without duplicating files in conversion.
WAIT_MIN_FRAMES = 50
WAIT_MAX_FRAMES = 70
WAIT_TARGET_FRAMES = 60
WAIT_FRAME_JITTER = 10
MAX_WAIT_PALM_SPREAD = 0.07
# Black-hand centroid of the official rubber-hand STL (x>=0.088 m).
PALM_OFFSET = (0.20, 0.0, 0.007)
TOUCH_XY = 0.13
TOUCH_Z = 0.10
# The full black-hand half-height (~4.9 cm) is inset to 85% for collision.
PALM_COLLISION_HALF_Z = 0.049
TABLE_PENETRATION_TOLERANCE = 0.004
MIN_FRAMES = 105
MAX_FRAMES = 175
TARGET_FRAMES = 160
FRAME_JITTER = 15

HandSide = Literal["left", "right"]
PushDir = Literal["left", "right"]

_HAND_PATTERNS: dict[HandSide, tuple[str, ...]] = {
    "left": ("left_wrist_roll_rubber_hand", "left_wrist_roll_link", "left_rubber_hand"),
    "right": ("right_wrist_roll_rubber_hand", "right_wrist_roll_link", "right_rubber_hand"),
}

_TASK_SPEC: dict[str, dict[str, str]] = {
    "push_box_to_bin": {"parcel": "parcel_box", "hand": "right", "push": "right"},
    "nudge_mailer_to_bin": {"parcel": "mailer", "hand": "left", "push": "left"},
    "sweep_parcels_apart": {"parcel": "both", "hand": "both", "push": "both"},
    "wait_no_package": {"parcel": "none", "hand": "none", "push": "none"},
}


@dataclass
class SortingStepSnapshot:
    palm_left: tuple[float, float, float]
    palm_right: tuple[float, float, float]
    wrist_left: tuple[float, float, float]
    wrist_right: tuple[float, float, float]
    box_x: float
    box_y: float
    box_z: float
    mailer_x: float
    mailer_y: float
    mailer_z: float
    phase: float


@dataclass
class SortingQualityReport:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    touch_frames: int = 0
    push_delta_y: float = 0.0
    table_pen_frames: int = 0
    stable_zone_frames: int = 0
    wrong_way_excursion_y: float = 0.0
    length: int = 0


def sample_sorting_horizon(rng: np.random.Generator) -> int:
    """Pose-gated lift/cross/press/sweep plus a stable hold."""
    lo = max(MIN_FRAMES, TARGET_FRAMES - FRAME_JITTER)
    hi = min(MAX_FRAMES, TARGET_FRAMES + FRAME_JITTER)
    return int(rng.integers(lo, hi + 1))


def sample_wait_horizon(rng: np.random.Generator) -> int:
    """Empty-table wait clips match real waiting_no_package length (~1–2 s)."""
    lo = max(WAIT_MIN_FRAMES, WAIT_TARGET_FRAMES - WAIT_FRAME_JITTER)
    hi = min(WAIT_MAX_FRAMES, WAIT_TARGET_FRAMES + WAIT_FRAME_JITTER)
    return int(rng.integers(lo, hi + 1))


def resolve_hand_indices(robot) -> dict[HandSide, int]:
    out: dict[HandSide, int] = {}
    for side, patterns in _HAND_PATTERNS.items():
        for pattern in patterns:
            ids, _names = robot.find_bodies(pattern)
            if ids:
                idx = ids[0]
                out[side] = int(idx.item() if hasattr(idx, "item") else idx)
                break
        if side not in out:
            ids, _ = robot.find_bodies(f".*{side}.*wrist.*")
            if ids:
                idx = ids[0]
                out[side] = int(idx.item() if hasattr(idx, "item") else idx)
    if len(out) < 2:
        raise RuntimeError(f"could not resolve U1 hand bodies: {out}")
    return out


def wrist_xyz(robot, hand_idx: int, env_idx: int = 0) -> tuple[float, float, float]:
    p = robot.data.body_pos_w[env_idx, hand_idx]
    if hasattr(p, "torch"):
        p = p.torch
    return (float(p[0]), float(p[1]), float(p[2]))


def palm_xyz(robot, hand_idx: int, env_idx: int = 0) -> tuple[float, float, float]:
    p = robot.data.body_pos_w[env_idx, hand_idx]
    q = robot.data.body_quat_w[env_idx, hand_idx]
    if hasattr(p, "torch"):
        p = p.torch
    if hasattr(q, "torch"):
        q = q.torch
    offset = torch.tensor(PALM_OFFSET, dtype=torch.float32, device=p.device)
    palm = p + quat_apply(q.unsqueeze(0), offset.unsqueeze(0))[0]
    return (float(palm[0]), float(palm[1]), float(palm[2]))


def parcel_xyz(env, name: str, env_idx: int = 0) -> tuple[float, float, float]:
    p = env.scene[name].data.root_pos_w[env_idx]
    if hasattr(p, "torch"):
        p = p.torch
    return (float(p[0]), float(p[1]), float(p[2]))


def _touching(
    palm: tuple[float, float, float],
    wrist: tuple[float, float, float],
    obj_x: float,
    obj_y: float,
    obj_z: float,
) -> bool:
    dx = palm[0] - obj_x
    dy = palm[1] - obj_y
    horiz = (dx * dx + dy * dy) ** 0.5
    return horiz < TOUCH_XY and abs(palm[2] - obj_z) < TOUCH_Z


def capture_step(
    env,
    robot,
    hand_idx: dict[HandSide, int],
    *,
    step: int,
    horizon: int,
    phase_bias: float = 0.0,
) -> SortingStepSnapshot:
    phase = min(1.0, max(0.0, step / max(horizon - 1, 1) + phase_bias))
    pl = palm_xyz(robot, hand_idx["left"])
    pr = palm_xyz(robot, hand_idx["right"])
    wl = wrist_xyz(robot, hand_idx["left"])
    wr = wrist_xyz(robot, hand_idx["right"])
    bx, by, bz = parcel_xyz(env, "parcel_box")
    mx, my, mz = parcel_xyz(env, "mailer")
    return SortingStepSnapshot(
        palm_left=pl,
        palm_right=pr,
        wrist_left=wl,
        wrist_right=wr,
        box_x=bx,
        box_y=by,
        box_z=bz,
        mailer_x=mx,
        mailer_y=my,
        mailer_z=mz,
        phase=phase,
    )


def _table_penetration(palm: tuple[float, float, float]) -> bool:
    """Detect the actual palm collision core crossing the tabletop."""
    return palm[2] - PALM_COLLISION_HALF_Z < TABLE_TOP_Z - TABLE_PENETRATION_TOLERANCE


def _active_hands(task_id: str) -> tuple[HandSide, ...]:
    spec = _TASK_SPEC.get(task_id)
    if spec is None:
        return ("left", "right")
    hand = spec["hand"]
    if hand == "none":
        return ()
    if hand == "both":
        return ("left", "right")
    return (hand,)  # type: ignore[return-value]


def evaluate_episode(
    task_id: str,
    trail: list[SortingStepSnapshot],
    *,
    horizon: int,
) -> SortingQualityReport:
    reasons: list[str] = []
    if task_id == "wait_no_package":
        return _eval_wait(trail)

    if len(trail) < MIN_FRAMES:
        reasons.append(f"too short T={len(trail)} < {MIN_FRAMES}")
    if len(trail) > MAX_FRAMES:
        reasons.append(f"too long T={len(trail)} > {MAX_FRAMES}")

    active = _active_hands(task_id)
    table_pen = 0
    for s in trail:
        if s.phase < 0.34:
            continue
        for side in active:
            palm = s.palm_left if side == "left" else s.palm_right
            if _table_penetration(palm):
                table_pen += 1
                break
    if table_pen > 0:
        reasons.append(f"table penetration in {table_pen} frames")

    spec = _TASK_SPEC.get(task_id)
    if spec is None:
        return SortingQualityReport(passed=len(reasons) == 0, reasons=reasons, length=len(trail))

    if task_id == "sweep_parcels_apart":
        box_ok = _eval_single_push(
            trail,
            hand="right",
            parcel_key="box",
            push_dir="right",
        )
        mail_ok = _eval_single_push(
            trail,
            hand="left",
            parcel_key="mailer",
            push_dir="left",
        )
        if not box_ok[0]:
            reasons.append(f"box: {box_ok[1]}")
        if not mail_ok[0]:
            reasons.append(f"mailer: {mail_ok[1]}")
        box_wrong = _wrong_way_excursion(trail, parcel_key="box", push_dir="right")
        mail_wrong = _wrong_way_excursion(trail, parcel_key="mailer", push_dir="left")
        if box_wrong > MAX_WRONG_WAY_EXCURSION_Y:
            reasons.append(
                f"box wrong-way excursion={box_wrong:.3f} > {MAX_WRONG_WAY_EXCURSION_Y}"
            )
        if mail_wrong > MAX_WRONG_WAY_EXCURSION_Y:
            reasons.append(
                f"mailer wrong-way excursion={mail_wrong:.3f} > {MAX_WRONG_WAY_EXCURSION_Y}"
            )
        return SortingQualityReport(
            passed=len(reasons) == 0,
            reasons=reasons,
            touch_frames=box_ok[2] + mail_ok[2],
            push_delta_y=min(box_ok[3], mail_ok[3]),
            table_pen_frames=table_pen,
            stable_zone_frames=min(box_ok[4], mail_ok[4]),
            wrong_way_excursion_y=max(box_wrong, mail_wrong),
            length=len(trail),
        )

    hand = spec["hand"]  # type: ignore[assignment]
    parcel_key = "box" if spec["parcel"] == "parcel_box" else "mailer"
    push_dir = spec["push"]  # type: ignore[assignment]
    ok, msg, touches, dy, stable_frames = _eval_single_push(
        trail, hand=hand, parcel_key=parcel_key, push_dir=push_dir
    )
    if not ok:
        reasons.append(msg)
    wrong_way = _wrong_way_excursion(trail, parcel_key=parcel_key, push_dir=push_dir)
    if wrong_way > MAX_WRONG_WAY_EXCURSION_Y:
        reasons.append(f"wrong-way excursion={wrong_way:.3f} > {MAX_WRONG_WAY_EXCURSION_Y}")
    hand_ok, hand_msg = _eval_hand_exit(trail, hand=hand, push_dir=push_dir)
    if not hand_ok:
        reasons.append(hand_msg)
    parcel_ok, parcel_msg = _eval_single_parcel(trail, parcel_key=parcel_key)
    if not parcel_ok:
        reasons.append(parcel_msg)
    return SortingQualityReport(
        passed=len(reasons) == 0,
        reasons=reasons,
        touch_frames=touches,
        push_delta_y=dy,
        table_pen_frames=table_pen,
        stable_zone_frames=stable_frames,
        wrong_way_excursion_y=wrong_way,
        length=len(trail),
    )


def _wrong_way_excursion(
    trail: list[SortingStepSnapshot],
    *,
    parcel_key: Literal["box", "mailer"],
    push_dir: PushDir,
) -> float:
    ys = [s.box_y if parcel_key == "box" else s.mailer_y for s in trail]
    if not ys:
        return 0.0
    start_y = ys[0]
    if push_dir == "right":
        return max(0.0, max(ys) - start_y)
    return max(0.0, start_y - min(ys))


def _eval_single_push(
    trail: list[SortingStepSnapshot],
    *,
    hand: HandSide,
    parcel_key: Literal["box", "mailer"],
    push_dir: PushDir,
) -> tuple[bool, str, int, float, int]:
    if parcel_key == "box":
        xs = [s.box_x for s in trail]
        ys = [s.box_y for s in trail]
    else:
        xs = [s.mailer_x for s in trail]
        ys = [s.mailer_y for s in trail]
    if xs[0] < MIN_PARCEL_START_X:
        return (
            False,
            f"{parcel_key} starts too close to table front x={xs[0]:.3f} < {MIN_PARCEL_START_X:.2f}",
            0,
            0.0,
            0,
        )
    y0 = ys[0]
    # Peak displacement in the commanded direction (end pose may rebound slightly).
    if push_dir == "left":
        y_peak = max(ys)
        delta = y_peak - y0
        y_out = y_peak
    else:
        y_peak = min(ys)
        delta = y0 - y_peak
        y_out = y_peak

    touches = 0
    for s in trail:
        if s.phase < 0.35:
            continue
        palm = s.palm_left if hand == "left" else s.palm_right
        wrist = s.wrist_left if hand == "left" else s.wrist_right
        if parcel_key == "box":
            obj_x, obj_y, obj_z = s.box_x, s.box_y, s.box_z
        else:
            obj_x, obj_y, obj_z = s.mailer_x, s.mailer_y, s.mailer_z
        if _touching(palm, wrist, obj_x, obj_y, obj_z):
            touches += 1

    if parcel_key == "box":
        zs = [s.box_z for s in trail]
    else:
        zs = [s.mailer_z for s in trail]
    dropped = min(zs) < PARCEL_DROP_Z

    def _in_target_zone(y: float) -> bool:
        return y >= SORTING_ZONE_Y if push_dir == "left" else y <= -SORTING_ZONE_Y

    stable_frames = 0
    for y in reversed(ys):
        if not _in_target_zone(y):
            break
        stable_frames += 1

    if touches < MIN_TOUCH_FRAMES:
        return False, f"{hand} touch frames {touches} < {MIN_TOUCH_FRAMES}", touches, delta, stable_frames
    if dropped:
        return False, f"{parcel_key} dropped below table (z_min={min(zs):.3f})", touches, delta, stable_frames
    if delta < MIN_PUSH_DISPLACEMENT_Y:
        return False, f"push Δy={delta:.3f} < {MIN_PUSH_DISPLACEMENT_Y}", touches, delta, stable_frames
    if stable_frames < SORTING_ZONE_STABLE_FRAMES:
        side = "left" if push_dir == "left" else "right"
        return (
            False,
            f"{parcel_key} not stable in {side} zone |y|>={SORTING_ZONE_Y:.2f} "
            f"({stable_frames} < {SORTING_ZONE_STABLE_FRAMES} final frames; peak={y_out:.3f})",
            touches,
            delta,
            stable_frames,
        )
    return True, "ok", touches, delta, stable_frames


def _eval_hand_exit(
    trail: list[SortingStepSnapshot],
    *,
    hand: HandSide,
    push_dir: PushDir,
) -> tuple[bool, str]:
    """Active hand must sweep out with the parcel; the other hand stays near rest."""
    inactive: HandSide = "right" if hand == "left" else "left"
    push_steps = [s for s in trail if s.phase >= 0.45]
    if not push_steps:
        return False, "no push-phase frames for hand check"

    def _palm_y(s: SortingStepSnapshot, side: HandSide) -> float:
        return s.palm_left[1] if side == "left" else s.palm_right[1]

    y0_active = _palm_y(trail[0], hand)
    y0_inactive = _palm_y(trail[0], inactive)
    ys_active = [_palm_y(s, hand) for s in push_steps]
    ys_inactive = [_palm_y(s, inactive) for s in push_steps]

    if push_dir == "left":
        active_dy = max(ys_active) - y0_active
    else:
        active_dy = y0_active - min(ys_active)

    if active_dy < MIN_ACTIVE_HAND_DY:
        return False, f"{hand} hand Δy={active_dy:.3f} < {MIN_ACTIVE_HAND_DY} (must exit with parcel)"
    inactive_spread = max(
        max(ys_inactive) - y0_inactive,
        y0_inactive - min(ys_inactive),
    )
    if inactive_spread > MAX_INACTIVE_HAND_DY:
        return (
            False,
            f"{inactive} hand moved too much (spread={inactive_spread:.3f} > {MAX_INACTIVE_HAND_DY})",
        )

    # Active hand must move further in push direction than the inactive one.
    if push_dir == "left":
        inactive_push_dy = max(0.0, max(ys_inactive) - y0_inactive)
    else:
        inactive_push_dy = max(0.0, y0_inactive - min(ys_inactive))
    if inactive_push_dy > 0.5 * active_dy:
        return (
            False,
            f"{inactive} hand moved more than active ({inactive_push_dy:.3f} vs {active_dy:.3f})",
        )
    return True, "ok"


def _eval_single_parcel(
    trail: list[SortingStepSnapshot],
    *,
    parcel_key: Literal["box", "mailer"],
) -> tuple[bool, str]:
    """Inactive parcel must stay off-table (single-parcel mode)."""
    if parcel_key == "box":
        ys = [s.box_y for s in trail[:8]]
        other = [s.mailer_y for s in trail[:8]]
        other_name = "mailer"
    else:
        ys = [s.mailer_y for s in trail[:8]]
        other = [s.box_y for s in trail[:8]]
        other_name = "parcel_box"
    if max(abs(y) for y in other) > OFFTABLE_XY:
        return True, "ok"
    return False, f"inactive {other_name} still on table (y≈{other[0]:.2f})"


def _eval_parcel_stayed_on_table(
    trail: list[SortingStepSnapshot],
    *,
    parcel_key: Literal["box", "mailer"],
) -> tuple[bool, str]:
    """Active parcel must stay on the tabletop (no floor drop)."""
    zs = [s.box_z if parcel_key == "box" else s.mailer_z for s in trail]
    z_min = min(zs)
    z_end = zs[-1]
    if z_min < PARCEL_DROP_Z:
        return False, f"{parcel_key} dropped z_min={z_min:.3f} < {PARCEL_DROP_Z:.3f}"
    if z_end < PARCEL_DROP_Z + 0.02:
        return False, f"{parcel_key} ended low z={z_end:.3f}"
    return True, "ok"


def _eval_wait(trail: list[SortingStepSnapshot]) -> SortingQualityReport:
    reasons: list[str] = []
    if len(trail) < WAIT_MIN_FRAMES:
        reasons.append(f"wait too short T={len(trail)} < {WAIT_MIN_FRAMES}")
    if len(trail) > WAIT_MAX_FRAMES:
        reasons.append(f"wait too long T={len(trail)} > {WAIT_MAX_FRAMES}")

    def _spread(get_y) -> float:
        ys = [get_y(s) for s in trail]
        return max(ys) - min(ys)

    left_spread = _spread(lambda s: s.palm_left[1])
    right_spread = _spread(lambda s: s.palm_right[1])
    if left_spread > MAX_WAIT_PALM_SPREAD:
        reasons.append(f"left palm moved {left_spread:.3f} > {MAX_WAIT_PALM_SPREAD}")
    if right_spread > MAX_WAIT_PALM_SPREAD:
        reasons.append(f"right palm moved {right_spread:.3f} > {MAX_WAIT_PALM_SPREAD}")

    box_off = max(abs(s.box_y) for s in trail) > OFFTABLE_XY
    mail_off = max(abs(s.mailer_y) for s in trail) > OFFTABLE_XY
    if not box_off:
        reasons.append(f"box still on table y≈{trail[0].box_y:.2f}")
    if not mail_off:
        reasons.append(f"mailer still on table y≈{trail[0].mailer_y:.2f}")
    return SortingQualityReport(
        passed=len(reasons) == 0,
        reasons=reasons,
        touch_frames=0,
        push_delta_y=0.0,
        table_pen_frames=0,
        length=len(trail),
    )
