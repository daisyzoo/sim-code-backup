#!/usr/bin/env python3
"""Convert official Unitree G1 (+ Inspire FTP) URDF → local USD.

Source: SimFoundry/third_party/unitree_ros/robots/g1_description/
(from https://github.com/unitreerobotics/unitree_ros)

    conda activate env_isaaclab
    export OMNI_KIT_ACCEPT_EULA=yes
    cd /home/user/Documents/zoo/sim/IsaacLab
    ./isaaclab.sh -p ../SimFoundry/scripts/convert_g1_urdf.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G1_DESC = ROOT / "third_party" / "unitree_ros" / "robots" / "g1_description"
OUT_DIR = ROOT / "assets" / "robots"

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Convert Unitree G1 URDF to USD.")
parser.add_argument(
    "--urdf",
    type=str,
    default=str(G1_DESC / "g1_29dof_rev_1_0_with_inspire_hand_FTP.urdf"),
)
parser.add_argument(
    "--out-name",
    type=str,
    default="g1_29dof_inspire_ftp",
    help="Output folder / usda stem under assets/robots/.",
)
parser.add_argument("--fix-base", action=argparse.BooleanOptionalAction, default=True)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from isaaclab.sim.converters import UrdfConverter, UrdfConverterCfg  # noqa: E402


def main() -> None:
    urdf = Path(args_cli.urdf).resolve()
    if not urdf.is_file():
        raise SystemExit(f"URDF not found: {urdf}")

    out_dir = (OUT_DIR / args_cli.out_name).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    usd_path = out_dir / f"{args_cli.out_name}.usd"

    cfg = UrdfConverterCfg(
        asset_path=str(urdf),
        usd_dir=str(out_dir),
        usd_file_name=usd_path.name,
        fix_base=bool(args_cli.fix_base),
        merge_fixed_joints=True,
        force_usd_conversion=True,
        self_collision=False,
        collision_from_visuals=False,
        joint_drive=UrdfConverterCfg.JointDriveCfg(
            gains=UrdfConverterCfg.JointDriveCfg.PDGainsCfg(stiffness=None, damping=None)
        ),
    )
    converter = UrdfConverter(cfg)
    usd = Path(converter.usd_path)
    print(f"converted → {usd}")
    geom = usd.parent / "payloads" / "geometries.usd"
    total = sum(p.stat().st_size for p in usd.parent.rglob("*") if p.is_file())
    if geom.is_file():
        print(f"geometry  → {geom} ({geom.stat().st_size / 1e6:.1f} MB)")
    print(f"bundle    → {total / 1e6:.1f} MB under {usd.parent}")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
