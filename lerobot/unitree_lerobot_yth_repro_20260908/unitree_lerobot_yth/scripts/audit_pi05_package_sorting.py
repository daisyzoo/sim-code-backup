"""CPU regression test using actual parquet rows and episode boundary queries."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unitree_lerobot/lerobot/src"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    args = parser.parse_args()
    os.environ["PI05_TRAIN_STATS_FILE"] = str(args.root / "meta/train_only_stats.json")
    os.environ["PI05_SHARED_SPLIT_FILE"] = str(args.split)
    from lerobot.utils.pi05_training import apply_training_stats
    from types import SimpleNamespace
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    split = json.loads(args.split.read_text())
    observed = {}
    selections = {"train": split["train"], "validation": split["validation"],
                  "noncontiguous": [split["train"][2], split["validation"][-1]]}
    for label, episodes in selections.items():
        ds = LeRobotDataset("local/package_sorting_unified", root=args.root,
                            episodes=episodes, video_backend="pyav")
        if label != "noncontiguous":
            apply_training_stats(SimpleNamespace(dataset=SimpleNamespace(episodes=episodes)), ds)
        ds.delta_indices = {"action": [-1, 0, 49]}
        actual_episodes = {int(value) for value in ds.hf_dataset["episode_index"]}
        assert actual_episodes == set(episodes), (label, actual_episodes)
        expected_count = sum(ds.meta.episodes[ep]["dataset_to_index"]
                             - ds.meta.episodes[ep]["dataset_from_index"] for ep in episodes)
        assert len(ds) == expected_count, (label, len(ds), expected_count)
        indices = {int(value) for value in ds.hf_dataset["index"]}
        assert len(indices) == expected_count
        observed[label] = indices
        for episode, (start, end) in ds._episode_row_bounds.items():
            for idx in (start, end - 1):
                query, padding = ds._get_query_indices(idx, episode)
                assert query["action"] == [max(start, min(end - 1, idx + d)) for d in (-1, 0, 49)]
                assert padding["action_is_pad"].tolist() == [idx+d < start or idx+d >= end for d in (-1, 0, 49)]
                assert all(int(ds.hf_dataset[q]["episode_index"]) == episode for q in query["action"])
        # Actually decode boundary samples and load their temporal action windows.
        for idx in (0, len(ds)-1):
            sample = ds[idx]
            assert int(sample["episode_index"]) in set(episodes)
            assert sample["action"].shape == (3, 11)
        if label != "noncontiguous":
            assert int(ds.meta.stats["action"]["count"][0]) == 45698
        ds.delta_indices = {"action": list(range(50))}
        tail = ds[len(ds)-1]
        assert tail["action"].shape == (50, 11)
        assert tail["action_is_pad"].tolist() == [False] + [True] * 49
        print(f"PASS {label}: episodes={len(episodes)} frames={len(ds)}; boundaries, decoded samples and training stats OK", flush=True)
    assert not observed["train"] & observed["validation"]
    assert len(observed["train"] | observed["validation"]) == 47571
    print("PASS: actual train/validation frame sets are disjoint and cover all 47571 frames")


if __name__ == "__main__":
    main()
