"""Distributed held-out loss; never prepares a padded distributed sampler."""
import copy
import json
import logging
import os
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Subset


class HeldoutValidation:
    def __init__(self, cfg, accelerator):
        from lerobot.datasets.factory import make_dataset

        self.accelerator = accelerator
        self.output = Path(cfg.output_dir)
        from lerobot.utils.pi05_training import read_split, apply_training_stats
        split = read_split(os.environ["PI05_SHARED_SPLIT_FILE"])
        validation_cfg = copy.deepcopy(cfg)
        validation_cfg.dataset.episodes = split["validation"]
        validation_cfg.dataset.image_transforms.enable = False
        dataset = make_dataset(validation_cfg)
        apply_training_stats(validation_cfg, dataset)
        # Each frame appears exactly once globally, including uneven last batches.
        indices = range(accelerator.process_index, len(dataset), accelerator.num_processes)
        self.loader = DataLoader(Subset(dataset, indices), batch_size=1,
                                 shuffle=False, num_workers=0)
        self.expected_count = sum(
            dataset.meta.episodes[ep]["dataset_to_index"]
            - dataset.meta.episodes[ep]["dataset_from_index"]
            for ep in split["validation"]
        )
        if len(dataset) != self.expected_count:
            raise ValueError(f"Validation dataset leaked rows: {len(dataset)}/{self.expected_count}")

    def run(self, policy, preprocessor, step):
        accelerator = self.accelerator
        model = accelerator.unwrap_model(policy)
        was_training = model.training
        py_rng, np_rng = random.getstate(), np.random.get_state()
        if accelerator.device.type == "cuda":
            device_index = accelerator.device.index
            devices = [torch.cuda.current_device() if device_index is None else device_index]
        else:
            devices = []
        totals = torch.zeros(2, dtype=torch.float64, device=accelerator.device)
        try:
            with torch.random.fork_rng(devices=devices), torch.no_grad():
                torch.manual_seed(42000 + accelerator.process_index)
                random.seed(42000 + accelerator.process_index)
                np.random.seed(42000 + accelerator.process_index)
                model.eval()
                for batch in self.loader:
                    count = batch["action"].shape[0]
                    with accelerator.autocast():
                        loss, _ = model(preprocessor(batch))
                    if not torch.isfinite(loss).all():
                        raise RuntimeError("Non-finite PI0.5 held-out loss")
                    totals[0] += loss.detach().double() * count
                    totals[1] += count
        finally:
            model.train(was_training)
            random.setstate(py_rng)
            np.random.set_state(np_rng)
        totals = accelerator.reduce(totals, reduction="sum")
        count = int(totals[1].item())
        if count != self.expected_count or count == 0:
            raise RuntimeError(f"Validation coverage mismatch: {count}/{self.expected_count}")
        result = {"step": step, "validation/loss": (totals[0] / totals[1]).item(),
                  "validation/frames": count,
                  "metric_note": "native stochastic flow loss, not cross-model action MAE"}
        if accelerator.is_main_process:
            self.output.mkdir(parents=True, exist_ok=True)
            with (self.output / "validation.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result) + "\n")
            logging.info("PI0.5 held-out validation: %s", result)
        return result
