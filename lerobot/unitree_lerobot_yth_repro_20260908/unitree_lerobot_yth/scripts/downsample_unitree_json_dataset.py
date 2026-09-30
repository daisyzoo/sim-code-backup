#!/usr/bin/env python3

"""
Downsample a Unitree JSON dataset by frame stride and rewrite fps metadata.

Input:
    source_root/
      task_a/
        episode_0000/
      task_b/
        episode_0000/

Output:
    output_root/
      task_a/
        episode_0000/
      task_b/
        episode_0000/

Only ``data.json`` is rewritten. Media folders are symlinked or copied as-is.
This is sufficient because the converted dataset only reads the frame paths
referenced by the retained samples.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
from pathlib import Path

import tyro


@dataclasses.dataclass(frozen=True)
class Args:
    source_root: Path
    output_root: Path
    stride: int = 2
    target_fps: float = 10.0
    media_mode: str = "symlink"
    overwrite: bool = False


def ensure_empty_dir(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"Output path already exists: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def link_or_copy(src: Path, dst: Path, media_mode: str) -> None:
    if dst.exists() or dst.is_symlink():
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink()

    if media_mode == "symlink":
        os.symlink(src, dst, target_is_directory=src.is_dir())
        return
    if media_mode == "copy":
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return

    raise ValueError(f"Unsupported media_mode: {media_mode}")


def iter_task_dirs(source_root: Path) -> list[Path]:
    return sorted(path for path in source_root.iterdir() if path.is_dir())


def iter_episode_dirs(task_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in task_dir.iterdir()
        if path.is_dir() and path.name.startswith("episode_") and (path / "data.json").is_file()
    )


def rewrite_payload(payload: dict, stride: int, target_fps: float) -> tuple[dict, int, int]:
    rewritten = json.loads(json.dumps(payload))
    original_frames = payload.get("data", [])
    kept_frames = []

    for new_idx, sample in enumerate(original_frames[::stride]):
        sample_copy = json.loads(json.dumps(sample))
        sample_copy["idx"] = new_idx
        kept_frames.append(sample_copy)

    rewritten["data"] = kept_frames

    image_info = rewritten.setdefault("info", {}).setdefault("image", {})
    image_info["fps"] = float(target_fps)

    depth_info = rewritten.setdefault("info", {}).get("depth")
    if isinstance(depth_info, dict):
        depth_info["fps"] = float(target_fps)

    return rewritten, len(original_frames), len(kept_frames)


def main(args: Args) -> None:
    if args.stride <= 0:
        raise ValueError(f"stride must be > 0, got {args.stride}")
    if args.target_fps <= 0:
        raise ValueError(f"target_fps must be > 0, got {args.target_fps}")
    if not args.source_root.is_dir():
        raise FileNotFoundError(f"Source root not found: {args.source_root}")

    ensure_empty_dir(args.output_root, args.overwrite)

    total_episodes = 0
    total_input_frames = 0
    total_output_frames = 0

    for task_dir in iter_task_dirs(args.source_root):
        dst_task_dir = args.output_root / task_dir.name
        dst_task_dir.mkdir(parents=True, exist_ok=True)

        for episode_dir in iter_episode_dirs(task_dir):
            payload = json.loads((episode_dir / "data.json").read_text(encoding="utf-8"))
            rewritten, in_frames, out_frames = rewrite_payload(payload, args.stride, args.target_fps)

            dst_episode_dir = dst_task_dir / episode_dir.name
            dst_episode_dir.mkdir(parents=True, exist_ok=True)
            (dst_episode_dir / "data.json").write_text(
                json.dumps(rewritten, ensure_ascii=False, indent=4),
                encoding="utf-8",
            )

            for child in episode_dir.iterdir():
                if child.name == "data.json":
                    continue
                link_or_copy(child, dst_episode_dir / child.name, args.media_mode)

            total_episodes += 1
            total_input_frames += in_frames
            total_output_frames += out_frames

    print("Downsampled dataset:")
    print(f"  source_root:        {args.source_root}")
    print(f"  output_root:        {args.output_root}")
    print(f"  stride:             {args.stride}")
    print(f"  target_fps:         {args.target_fps}")
    print(f"  total_episodes:     {total_episodes}")
    print(f"  total_input_frames: {total_input_frames}")
    print(f"  total_output_frames:{total_output_frames}")


if __name__ == "__main__":
    main(tyro.cli(Args))
