#!/usr/bin/env python3

"""
Prepare a Unitree JSON dataset from multiple source directories with optional task-level repetition.

Example output layout:

    output_root/
      right_hand_cup_pick/
        episode_0000/
        episode_0001/
      right_hand_lift_bag/
        episode_0000/
        episode_0001/

Each task may pull episodes from one or more source directories. The script rewrites
the text fields in ``data.json`` and either symlinks or copies the media assets.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
from pathlib import Path

import tyro


EPISODE_DIR_RE = re.compile(r"^episode_(\d+)$")


@dataclasses.dataclass(frozen=True)
class TaskSource:
    name: str
    output_task_dir: str
    source_dirs: list[Path]
    goal: str
    desc: str = ""
    steps: str = ""
    repeat: int = 1


@dataclasses.dataclass(frozen=True)
class PrepareSpec:
    output_root: Path
    tasks: list[TaskSource]
    media_mode: str = "symlink"
    overwrite: bool = False


def load_spec(spec_path: Path) -> PrepareSpec:
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    tasks = [
        TaskSource(
            name=item["name"],
            output_task_dir=item["output_task_dir"],
            source_dirs=[Path(path) for path in item["source_dirs"]],
            goal=item["goal"],
            desc=item.get("desc", ""),
            steps=item.get("steps", ""),
            repeat=int(item.get("repeat", 1)),
        )
        for item in data["tasks"]
    ]
    return PrepareSpec(
        output_root=Path(data["output_root"]),
        tasks=tasks,
        media_mode=data.get("media_mode", "symlink"),
        overwrite=bool(data.get("overwrite", False)),
    )


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


def rewrite_text_fields(payload: dict, task_source: TaskSource) -> dict:
    updated = json.loads(json.dumps(payload))
    updated.setdefault("text", {})
    updated["text"]["goal"] = task_source.goal
    if task_source.desc:
        updated["text"]["desc"] = task_source.desc
    if task_source.steps:
        updated["text"]["steps"] = task_source.steps
    return updated


def parse_episode_index(episode_dir: Path) -> int | None:
    match = EPISODE_DIR_RE.fullmatch(episode_dir.name)
    if match is None:
        return None
    return int(match.group(1))


def iter_valid_episode_dirs(source_dir: Path) -> list[Path]:
    valid_dirs: list[tuple[int, Path]] = []
    for path in source_dir.iterdir():
        if not path.is_dir():
            continue
        episode_index = parse_episode_index(path)
        if episode_index is None:
            continue
        if not (path / "data.json").is_file():
            continue
        valid_dirs.append((episode_index, path))
    valid_dirs.sort(key=lambda item: item[0])
    return [path for _, path in valid_dirs]


def prepare_dataset(spec: PrepareSpec) -> None:
    ensure_empty_dir(spec.output_root, spec.overwrite)

    task_summary: dict[str, int] = {}
    source_summary: dict[str, dict[str, int]] = {}

    for task in spec.tasks:
        if task.repeat <= 0:
            raise ValueError(f"repeat must be > 0 for task {task.name}, got {task.repeat}")
        if not task.source_dirs:
            raise ValueError(f"task {task.name} has no source_dirs")

        task_output_dir = spec.output_root / task.output_task_dir
        task_output_dir.mkdir(parents=True, exist_ok=True)

        canonical_episode_dirs: list[Path] = []
        skipped_noncanonical_total = 0
        total_dirs_seen = 0

        for source_dir in task.source_dirs:
            if not source_dir.is_dir():
                raise FileNotFoundError(f"Source task directory not found: {source_dir}")

            valid_dirs = iter_valid_episode_dirs(source_dir)
            if not valid_dirs:
                raise FileNotFoundError(f"No canonical episode directories found in: {source_dir}")

            total_dir_count = sum(1 for path in source_dir.iterdir() if path.is_dir())
            total_dirs_seen += total_dir_count
            skipped_noncanonical_total += total_dir_count - len(valid_dirs)
            canonical_episode_dirs.extend(valid_dirs)

        output_index = 0
        for _ in range(task.repeat):
            for episode_dir in canonical_episode_dirs:
                payload = json.loads((episode_dir / "data.json").read_text(encoding="utf-8"))
                payload = rewrite_text_fields(payload, task)

                dst_episode_dir = task_output_dir / f"episode_{output_index:04d}"
                dst_episode_dir.mkdir(parents=True, exist_ok=True)
                (dst_episode_dir / "data.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=4),
                    encoding="utf-8",
                )

                for child in episode_dir.iterdir():
                    if child.name == "data.json":
                        continue
                    link_or_copy(child, dst_episode_dir / child.name, spec.media_mode)

                output_index += 1

        task_summary[task.output_task_dir] = output_index
        source_summary[task.output_task_dir] = {
            "input_episodes": len(canonical_episode_dirs),
            "repeat": task.repeat,
            "output_episodes": output_index,
            "source_dirs": len(task.source_dirs),
            "skipped_noncanonical": skipped_noncanonical_total,
            "total_dirs_seen": total_dirs_seen,
        }

    print("Prepared weighted multisource dataset:")
    print(f"  output_root: {spec.output_root}")
    print(f"  media_mode:  {spec.media_mode}")
    for task_name in sorted(task_summary):
        summary = source_summary[task_name]
        print(f"  {task_name}: input_episodes={summary['input_episodes']}")
        print(f"  {task_name}: repeat={summary['repeat']}")
        print(f"  {task_name}: output_episodes={summary['output_episodes']}")
        print(f"  {task_name}: source_dirs={summary['source_dirs']}")
        print(f"  {task_name}: skipped_noncanonical={summary['skipped_noncanonical']}")


@dataclasses.dataclass(frozen=True)
class Args:
    spec_path: Path


def main() -> None:
    args = tyro.cli(Args)
    spec = load_spec(args.spec_path)
    prepare_dataset(spec)


if __name__ == "__main__":
    main()
