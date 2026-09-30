"""Arm keyframes for sorting-station push/sort (11 DoF teleop).

Visual ground truth: ``demo/real_ref_frames/1_t0.5.jpg`` — both arms forward
ABOVE the blue table. Tuned absolute rest in ``g1_assets`` keeps palm_z ≈
TABLE_TOP + 0.12 with hand over the parcels (x≈0.35).

Offsets are relative to that hover. Prefer shoulder roll for lateral push.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Side = Literal["left", "right"]


@dataclass(frozen=True)
class ArmKeyframe:
    pitch: float = 0.0
    roll: float = 0.0
    yaw: float = 0.0
    elbow: float = 0.0
    wrist: float = 0.0

    def lerp(self, other: ArmKeyframe, t: float) -> ArmKeyframe:
        t = max(0.0, min(1.0, t))
        return ArmKeyframe(
            pitch=self.pitch + (other.pitch - self.pitch) * t,
            roll=self.roll + (other.roll - self.roll) * t,
            yaw=self.yaw + (other.yaw - self.yaw) * t,
            elbow=self.elbow + (other.elbow - self.elbow) * t,
            wrist=self.wrist + (other.wrist - self.wrist) * t,
        )


# Idle already sits over the parcel (±Y). Press down onto the parcel, then roll
# laterally so PhysX contact (not kinematic teleport) produces Δy.
# Negative pitch = reach +X (onto mid-table). Single-parcel rests sit near x≈0.40.
RIGHT_REACH = ArmKeyframe(-0.10, -0.04, 0.02, 0.12, -0.05)
RIGHT_CONTACT = ArmKeyframe(-0.16, -0.08, 0.0, 0.22, -0.10)
RIGHT_DRIVE = ArmKeyframe(-0.14, -0.28, -0.04, 0.18, -0.10)
RIGHT_RETRACT = ArmKeyframe(0.0, 0.0, 0.0, 0.0, 0.0)

LEFT_REACH = ArmKeyframe(-0.10, 0.04, -0.02, 0.12, 0.05)
LEFT_CONTACT = ArmKeyframe(-0.16, 0.08, 0.0, 0.22, 0.10)
LEFT_DRIVE = ArmKeyframe(-0.14, 0.28, 0.04, 0.18, 0.10)

ZERO = ArmKeyframe()

SWEEP_ROLL = 0.40

STUMP_SHOULDER_SCALE = 1.0
CONTACT_ELBOW_SCALE = 1.0
DRIVE_ELBOW_SCALE = 1.0

RIGHT_CONTACT_SIM = RIGHT_CONTACT
RIGHT_DRIVE_SIM = RIGHT_DRIVE
LEFT_CONTACT_SIM = LEFT_CONTACT
LEFT_DRIVE_SIM = LEFT_DRIVE


def clamp_above_table(kf: ArmKeyframe) -> ArmKeyframe:
    """Keep stump palms above TABLE_TOP (no deep pitch dive / extreme elbow)."""
    return ArmKeyframe(
        # Negative offset dives the hand; allow a press onto the ~3 cm parcel.
        pitch=max(kf.pitch, -0.45),
        roll=kf.roll,
        yaw=kf.yaw,
        elbow=min(max(kf.elbow, -0.15), 0.35),
        wrist=kf.wrist,
    )
