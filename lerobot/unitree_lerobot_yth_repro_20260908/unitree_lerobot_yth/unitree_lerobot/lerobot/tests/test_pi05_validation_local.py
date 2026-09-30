import json
import random
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

from lerobot.utils.pi05_validation import HeldoutValidation


class Model(torch.nn.Module):
    def forward(self, batch):
        random.random()
        np.random.rand()
        torch.rand(1)
        return batch["action"].mean(), {}


class ValidationTest(unittest.TestCase):
    def test_full_coverage_mean_and_rng_restore(self):
        from contextlib import nullcontext
        accelerator = SimpleNamespace(
            device=torch.device("cpu"), process_index=0, is_main_process=True,
            unwrap_model=lambda model: model, autocast=nullcontext,
            reduce=lambda value, reduction: value)
        with tempfile.TemporaryDirectory() as directory:
            validator = HeldoutValidation.__new__(HeldoutValidation)
            validator.accelerator = accelerator
            validator.output = Path(directory)
            validator.expected_count = 3
            validator.loader = [{"action": torch.tensor([[float(i)]])} for i in (1, 2, 3)]
            model = Model().train()
            random.seed(12)
            np.random.seed(12)
            torch.manual_seed(12)
            expected = (random.random(), np.random.rand(), torch.rand(1))
            random.seed(12)
            np.random.seed(12)
            torch.manual_seed(12)
            result = validator.run(model, lambda batch: batch, 10)
            self.assertEqual(result["validation/loss"], 2.0)
            self.assertEqual(result["validation/frames"], 3)
            self.assertTrue(model.training)
            self.assertEqual(random.random(), expected[0])
            self.assertEqual(np.random.rand(), expected[1])
            self.assertTrue(torch.equal(torch.rand(1), expected[2]))
            self.assertEqual(json.loads((Path(directory) / "validation.jsonl").read_text())["step"], 10)

    def test_uneven_eight_rank_partition(self):
        partitions = [list(range(rank, 1873, 8)) for rank in range(8)]
        self.assertEqual(sorted(sum(partitions, [])), list(range(1873)))


if __name__ == "__main__":
    unittest.main()
