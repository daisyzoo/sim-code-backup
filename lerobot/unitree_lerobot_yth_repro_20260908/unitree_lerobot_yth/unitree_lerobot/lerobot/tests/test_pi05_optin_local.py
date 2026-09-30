import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch
from lerobot.utils.pi05_training import apply_training_stats, audit_parameters


class OptInTest(unittest.TestCase):
    def test_disabled_helpers_do_not_touch_legacy_task(self):
        with patch.dict(os.environ, {}, clear=True):
            apply_training_stats(None, None)
            audit_parameters(None, None, None, False)

    def test_stats_accept_six_and_eleven_dimensions(self):
        for dim in (6, 11):
            with self.subTest(dim=dim), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "split.json").write_text(json.dumps({"train": [0], "validation": [1]}))
                stats = {field: [0.0] * dim for field in ("min", "max", "mean", "std", "q01", "q99")}
                stats["count"] = [2]
                (root / "stats.json").write_text(json.dumps({"episode_indices": [0], "action": stats, "observation.state": stats}))
                dataset = SimpleNamespace(meta=SimpleNamespace(
                    episodes=[{"dataset_from_index": 0, "dataset_to_index": 2}],
                    features={key: {"shape": [dim]} for key in ("action", "observation.state")}, stats={}),
                    hf_dataset={"episode_index": [1]})
                with patch.dict(os.environ, {"PI05_TRAIN_STATS_FILE": str(root / "stats.json"), "PI05_SHARED_SPLIT_FILE": str(root / "split.json")}, clear=True):
                    apply_training_stats(SimpleNamespace(dataset=SimpleNamespace(episodes=[1])), dataset)
                self.assertEqual(dataset.meta.stats["action"]["mean"].shape, (dim,))

    def test_lora_audit_not_forced_into_expert_mode(self):
        model = torch.nn.Linear(2, 1)
        model.config = SimpleNamespace(lora_rank=16, train_expert_only=False)
        optimizer = torch.optim.AdamW(model.parameters())
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"PI05_PARAMETER_AUDIT": "1"}, clear=True):
            audit_parameters(model, optimizer, directory, True)
            report = json.loads((Path(directory) / "trainable_parameters.json").read_text())
            self.assertEqual(report["trainable_parameters"], 3)
            with patch.dict(os.environ, {"PI05_REQUIRE_EXPERT_ONLY": "1"}):
                with self.assertRaises(ValueError):
                    audit_parameters(model, optimizer, directory, True)


if __name__ == "__main__":
    unittest.main()
