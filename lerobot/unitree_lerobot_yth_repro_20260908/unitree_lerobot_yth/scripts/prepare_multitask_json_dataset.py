#!/usr/bin/env python3

"""
Prepare a multitask Unitree JSON dataset by relabeling task text per episode range.

The script reads episode folders from a flat source directory:

    source_task_dir/
      episode_0003/
      episode_0005/
      ...

and writes a new directory tree compatible with convert_unitree_json_to_lerobot.py:

    output_root/
      left_hand_dock_cup/
        episode_0003/
          data.json
          colors -> /path/to/source/colors
          ...
      right_hand_dock_bottle/
        episode_0068/
          data.json
          colors -> /path/to/source/colors
          ...

The original dataset remains unchanged.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
from pathlib import Path

import tyro


@dataclasses.dataclass(frozen=True)
class TaskRule:
    name: str
    output_task_dir: str
    episode_start: int
    episode_end: int
    goal: str
    desc: str = ""
    steps: str = ""


@dataclasses.dataclass(frozen=True)
class RelabelSpec:
    source_task_dir: Path
    output_root: Path
    task_rules: list[TaskRule]
    media_mode: str = "symlink"
    overwrite: bool = False
    keep_unmatched: bool = False
    unmatched_task_dir: str = "unmatched"


def load_spec(spec_path: Path) -> RelabelSpec:
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    task_rules = [TaskRule(**rule) for rule in data["task_rules"]]
    return RelabelSpec(
        source_task_dir=Path(data["source_task_dir"]),
        output_root=Path(data["output_root"]),
        task_rules=task_rules,
        media_mode=data.get("media_mode", "symlink"),
        overwrite=bool(data.get("overwrite", False)),
        keep_unmatched=bool(data.get("keep_unmatched", False)),
        unmatched_task_dir=data.get("unmatched_task_dir", "unmatched"),
    )


def iter_episode_dirs(source_task_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in source_task_dir.iterdir()
        if path.is_dir() and path.name.startswith("episode_")
    )


def parse_episode_index(episode_dir: Path) -> int:
    try:
        return int(episode_dir.name.split("_")[1])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"Invalid episode directory name: {episode_dir.name}") from exc


def match_rule(episode_index: int, task_rules: list[TaskRule]) -> TaskRule | None:
    for rule in task_rules:
        if rule.episode_start <= episode_index <= rule.episode_end:
            return rule
    return None


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


def rewrite_text_fields(payload: dict, rule: TaskRule) -> dict:
    updated = json.loads(json.dumps(payload))
    updated.setdefault("text", {})
    updated["text"]["goal"] = rule.goal
    if rule.desc:
        updated["text"]["desc"] = rule.desc
    if rule.steps:
        updated["text"]["steps"] = rule.steps
    return updated


def prepare_dataset(spec: RelabelSpec) -> None:
    ensure_empty_dir(spec.output_root, spec.overwrite)

    episode_dirs = iter_episode_dirs(spec.source_task_dir)
    if not episode_dirs:
        raise FileNotFoundError(f"No episode_* directories found in: {spec.source_task_dir}")

    summary: dict[str, int] = {}
    skipped = 0

    for episode_dir in episode_dirs:
        episode_index = parse_episode_index(episode_dir)
        rule = match_rule(episode_index, spec.task_rules)
        if rule is None:
            if not spec.keep_unmatched:
                skipped += 1
                continue
            task_dir = spec.output_root / spec.unmatched_task_dir
            task_name = spec.unmatched_task_dir
            payload = json.loads((episode_dir / "data.json").read_text(encoding="utf-8"))
        else:
            task_dir = spec.output_root / rule.output_task_dir
            task_name = rule.output_task_dir
            payload = rewrite_text_fields(
                json.loads((episode_dir / "data.json").read_text(encoding="utf-8")),
                rule,
            )

        dst_episode_dir = task_dir / episode_dir.name
        dst_episode_dir.mkdir(parents=True, exist_ok=True)
        (dst_episode_dir / "data.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

        for child in episode_dir.iterdir():
            if child.name == "data.json":
                continue
            link_or_copy(child, dst_episode_dir / child.name, spec.media_mode)

        summary[task_name] = summary.get(task_name, 0) + 1

    print("Prepared multitask dataset:")
    print(f"  source_task_dir: {spec.source_task_dir}")
    print(f"  output_root:     {spec.output_root}")
    print(f"  media_mode:      {spec.media_mode}")
    for task_name, count in sorted(summary.items()):
        print(f"  {task_name}: {count} episodes")
    print(f"  skipped_unmatched: {skipped}")


@dataclasses.dataclass(frozen=True)
class Args:
    spec_path: Path


def main() -> None:
    args = tyro.cli(Args)
    spec = load_spec(args.spec_path)
    prepare_dataset(spec)


if __name__ == "__main__":
    main()
