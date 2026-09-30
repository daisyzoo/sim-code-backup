"""Keep shipping-label cuboids flush on their parent parcels."""

from __future__ import annotations

import torch
from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.utils.math import quat_apply

# pick_demo albedos already include the real shipping labels. Keep the cuboids in
# the scene graph (tests / env fields) but do not stick a second decal on top.
PHOTO_LABELS_BAKED = True

# (parcel, label, local xyz offset from parcel center → label center)
# z = half_parcel_h + half_label_h + 0.2 mm so the sticker sits on the top face
# with no visible air gap; xy stays inset so the sticker never overhangs.
LABEL_ATTACHMENTS: tuple[tuple[str, str, tuple[float, float, float]], ...] = (
    ("parcel_box", "parcel_box_label", (0.0, 0.0, 0.025 / 2 + 0.0015 / 2 + 0.0002)),
    ("parcel_box_b", "parcel_box_b_label", (0.0, 0.0, 0.025 / 2 + 0.0015 / 2 + 0.0002)),
    ("mailer", "mailer_label", (0.0, 0.0, 0.030 / 2 + 0.0015 / 2 + 0.0002)),
    ("mailer_b", "mailer_b_label", (0.0, 0.0, 0.035 / 2 + 0.0015 / 2 + 0.0002)),
    ("mailer_c", "mailer_c_label", (0.0, 0.0, 0.025 / 2 + 0.0015 / 2 + 0.0002)),
    ("mailer_d", "mailer_d_label", (0.0, 0.0, 0.025 / 2 + 0.0015 / 2 + 0.0002)),
)


def sync_shipping_labels(env: ManagerBasedRLEnv) -> None:
    """Copy each parcel's world pose and place its label on the top face."""
    if PHOTO_LABELS_BAKED:
        return
    for parcel, label, local_xyz in LABEL_ATTACHMENTS:
        try:
            parent = env.scene[parcel]
            sticker = env.scene[label]
        except (KeyError, AttributeError):
            continue
        if not hasattr(parent, "data") or not hasattr(sticker, "write_root_pose_to_sim_index"):
            continue
        pos = parent.data.root_pos_w
        quat = parent.data.root_quat_w
        if hasattr(pos, "torch"):
            pos = pos.torch
        if hasattr(quat, "torch"):
            quat = quat.torch
        offset = torch.tensor(local_xyz, dtype=torch.float32, device=pos.device).unsqueeze(0).repeat(pos.shape[0], 1)
        world = pos + quat_apply(quat, offset)
        root = torch.cat([world, quat], dim=-1)
        sticker.write_root_pose_to_sim_index(root_pose=root)
        if hasattr(sticker, "write_root_velocity_to_sim_index"):
            zero = torch.zeros((pos.shape[0], 6), dtype=torch.float32, device=pos.device)
            sticker.write_root_velocity_to_sim_index(root_velocity=zero)
