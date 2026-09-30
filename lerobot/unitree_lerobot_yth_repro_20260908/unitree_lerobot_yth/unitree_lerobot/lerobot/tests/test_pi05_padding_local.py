"""CPU tests: real PI0.5 loss reduction and real processor steps, without VLM weights."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import torch
from lerobot.policies.pi05.modeling_pi05 import PI05Policy
from lerobot.policies.pi05.configuration_pi05 import PI05Config
from lerobot.policies.pi05.processor_pi05 import make_pi05_pre_post_processors
from lerobot.configs.types import FeatureType, NormalizationMode, PolicyFeature
from lerobot.utils.constants import OBS_LANGUAGE_TOKENS, OBS_LANGUAGE_ATTENTION_MASK


class PaddingTest(unittest.TestCase):
    def run_loss(self, padding, prediction):
        cfg = SimpleNamespace(debug_numerics_once=False, mask_action_padding=True, use_frame_loss_weights=False,
                              output_features={"action": SimpleNamespace(shape=(11,))})
        fake = SimpleNamespace(config=cfg, _preprocess_images=lambda batch: ([], []),
                               prepare_action=lambda batch: batch["action"],
                               model=SimpleNamespace(forward=lambda *args: prediction.square()))
        batch = {"action": torch.zeros_like(prediction),
                 OBS_LANGUAGE_TOKENS: torch.zeros(1, 1), OBS_LANGUAGE_ATTENTION_MASK: torch.ones(1, 1)}
        if padding is not None:
            batch["action_is_pad"] = padding
        return PI05Policy.forward(fake, batch)

    def test_tail_padding_zero_direct_gradient(self):
        padding = torch.ones(1, 50, dtype=torch.bool)
        padding[:, :3] = False
        prediction = torch.ones(1, 50, 32, requires_grad=True)
        loss, _ = self.run_loss(padding, prediction)
        self.assertEqual(loss.item(), 1.0)
        loss.backward()
        self.assertTrue(torch.all(prediction.grad[:, :3, :11] > 0))
        self.assertTrue(torch.all(prediction.grad[:, 3:] == 0))
        self.assertTrue(torch.all(prediction.grad[:, :, 11:] == 0))

    def test_real_stationary_actions_still_supervised(self):
        prediction = torch.ones(1, 50, 11, requires_grad=True)
        loss, _ = self.run_loss(torch.zeros(1, 50, dtype=torch.bool), prediction)
        loss.backward()
        self.assertTrue(torch.all(prediction.grad > 0))

    def test_missing_and_invalid_mask_rejected(self):
        prediction = torch.ones(1, 50, 11)
        with self.assertRaises(KeyError):
            self.run_loss(None, prediction)
        with self.assertRaises(ValueError):
            self.run_loss(torch.zeros(1, 49, dtype=torch.bool), prediction)

    def test_processor_preserves_mask(self):
        cfg = PI05Config(device="cpu", input_features={"observation.state": PolicyFeature(FeatureType.STATE, (11,))},
                         output_features={"action": PolicyFeature(FeatureType.ACTION, (11,))},
                         normalization_mapping={"STATE": NormalizationMode.IDENTITY, "ACTION": NormalizationMode.IDENTITY, "VISUAL": NormalizationMode.IDENTITY})
        def tokenize(text, **kwargs):
            return {"input_ids": torch.ones(len(text), 5, dtype=torch.long),
                    "attention_mask": torch.ones(len(text), 5, dtype=torch.long)}
        with patch("lerobot.processor.tokenizer_processor.AutoTokenizer.from_pretrained", return_value=tokenize):
            preprocessor, _ = make_pi05_pre_post_processors(cfg)
        padding = torch.ones(1, 50, dtype=torch.bool)
        padding[:, :3] = False
        result = preprocessor({"observation.state": torch.zeros(1, 11),
                               "action": torch.zeros(1, 50, 11),
                               "action_is_pad": padding.clone(), "task": ["Sort packages."]})
        self.assertEqual(result["action_is_pad"].dtype, torch.bool)
        self.assertTrue(torch.equal(result["action_is_pad"], padding))


if __name__ == "__main__":
    unittest.main()
