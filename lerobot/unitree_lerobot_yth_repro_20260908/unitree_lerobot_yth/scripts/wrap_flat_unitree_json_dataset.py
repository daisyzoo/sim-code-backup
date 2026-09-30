#!/usr/bin/env python3

"""
Wrap a flat Unitree JSON dataset into the task/episode layout expected by
the existing conversion scripts.

Input:
    source_root/
      episode_0000/
      episode_0001/

Output:
    output_root/
      task_name/
        episode_0000/ -> symlink/copy
        episode_0001/ -> symlink/copy
"""

from __future__ import annotations

import dataclasses
import os
import shutil
from pathlib import Path

import tyro


@dataclasses.dataclass(frozen=True)
class Args:
    source_root: Path
    output_root: Path
    task_name: str
    mode: str = "symlink"
    overwrite: bool = False


def ensure_empty_dir(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"Output path already exists: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def iter_episode_dirs(source_root: Path) -> list[Path]:
    return sorted(
        path
        for path in source_root.iterdir()
        if path.is_dir() and path.name.startswith("episode_") and (path / "data.json").is_file()
    )


def link_or_copy(src: Path, dst: Path, mode: str) -> None:
    if mode == "symlink":
        os.symlink(src, dst, target_is_directory=True)
        return
    if mode == "copy":
        shutil.copytree(src, dst)
        return
    raise ValueError(f"Unsupported mode: {mode}")


def main(args: Args) -> None:
    if not args.source_root.is_dir():
        raise FileNotFoundError(f"Source root not found: {args.source_root}")

    ensure_empty_dir(args.output_root, args.overwrite)
    task_root = args.output_root / args.task_name
    task_root.mkdir(parents=True, exist_ok=True)

    episode_dirs = iter_episode_dirs(args.source_root)
    if not episode_dirs:
        raise FileNotFoundError(f"No episode_xxxx directories found under: {args.source_root}")

    for episode_dir in episode_dirs:
        link_or_copy(episode_dir, task_root / episode_dir.name, args.mode)

    print("Wrapped dataset:")
    print(f"  source_root:   {args.source_root}")
    print(f"  output_root:   {args.output_root}")
    print(f"  task_name:     {args.task_name}")
    print(f"  mode:          {args.mode}")
    print(f"  total_episodes:{len(episode_dirs)}")


if __name__ == "__main__":
    main(tyro.cli(Args))
