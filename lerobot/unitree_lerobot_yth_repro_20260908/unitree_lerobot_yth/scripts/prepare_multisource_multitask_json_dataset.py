#!/usr/bin/env python3

"""
Prepare a multitask Unitree JSON dataset from multiple source task directories.

Input:
    source_task_a/
      episode_0001/
      episode_0004/
    source_task_b/
      episode_0006/
      episode_0007_trash/

Output:
    output_root/
      task_a/
        episode_0000/
        episode_0001/
      task_b/
        episode_0000/
        episode_0001/

The script rewrites the text fields in ``data.json`` and either symlinks or copies
the media assets. Source data is left unchanged.
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
    source_dir: Path
    output_task_dir: str
    goal: str
    desc: str = ""
    steps: str = ""


@dataclasses.dataclass(frozen=True)
class PrepareSpec:
    output_root: Path
    task_sources: list[TaskSource]
    media_mode: str = "symlink"
    overwrite: bool = False


def load_spec(spec_path: Path) -> PrepareSpec:
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    task_sources = [
        TaskSource(
            name=item["name"],
            source_dir=Path(item["source_dir"]),
            output_task_dir=item["output_task_dir"],
            goal=item["goal"],
            desc=item.get("desc", ""),
            steps=item.get("steps", ""),
        )
        for item in data["task_sources"]
    ]
    return PrepareSpec(
        output_root=Path(data["output_root"]),
        task_sources=task_sources,
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

    summary: dict[str, int] = {}
    skipped_noncanonical: dict[str, int] = {}

    for task_source in spec.task_sources:
        if not task_source.source_dir.is_dir():
            raise FileNotFoundError(f"Source task directory not found: {task_source.source_dir}")

        task_output_dir = spec.output_root / task_source.output_task_dir
        task_output_dir.mkdir(parents=True, exist_ok=True)

        canonical_episode_dirs = iter_valid_episode_dirs(task_source.source_dir)
        if not canonical_episode_dirs:
            raise FileNotFoundError(f"No canonical episode directories found in: {task_source.source_dir}")

        total_episode_dirs = sum(1 for path in task_source.source_dir.iterdir() if path.is_dir())
        skipped_noncanonical[task_source.output_task_dir] = total_episode_dirs - len(canonical_episode_dirs)

        for new_index, episode_dir in enumerate(canonical_episode_dirs):
            payload = json.loads((episode_dir / "data.json").read_text(encoding="utf-8"))
            payload = rewrite_text_fields(payload, task_source)

            dst_episode_dir = task_output_dir / f"episode_{new_index:04d}"
            dst_episode_dir.mkdir(parents=True, exist_ok=True)
            (dst_episode_dir / "data.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=4),
                encoding="utf-8",
            )

            for child in episode_dir.iterdir():
                if child.name == "data.json":
                    continue
                link_or_copy(child, dst_episode_dir / child.name, spec.media_mode)

        summary[task_source.output_task_dir] = len(canonical_episode_dirs)

    print("Prepared multisource multitask dataset:")
    print(f"  output_root: {spec.output_root}")
    print(f"  media_mode:  {spec.media_mode}")
    for task_name, count in sorted(summary.items()):
        print(f"  {task_name}: {count} episodes")
        print(f"  {task_name}: skipped_noncanonical={skipped_noncanonical[task_name]}")


@dataclasses.dataclass(frozen=True)
class Args:
    spec_path: Path
    output_root: Path | None = None


def main() -> None:
    args = tyro.cli(Args)
    spec = load_spec(args.spec_path)
    if args.output_root is not None:
        spec = dataclasses.replace(spec, output_root=args.output_root)
    prepare_dataset(spec)


if __name__ == "__main__":
    main()
