import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from unitree_lerobot.utils.convert_unitree_json_to_lerobot import (
    extract_detailed_task_segments,
    write_detailed_task_annotations,
)


class DetailedTaskConversionTest(unittest.TestCase):
    def test_extract_strips_editor_only_fields(self):
        episode = {
            "data": [{"idx": index} for index in range(6)],
            "detailed_task": {
                "action_config": [
                    {
                        "start_frame": 1,
                        "end_frame": 4,
                        "hotkey": "2",
                        "color": "#2196f3",
                        "action_text": "pour water",
                        "language_memory": "The cup has been picked up.",
                    }
                ]
            },
        }
        self.assertEqual(
            extract_detailed_task_segments(episode, episode_length=6),
            [
                {
                    "start_frame": 1,
                    "end_frame": 4,
                    "action_text": "pour water",
                    "language_memory": "The cup has been picked up.",
                }
            ],
        )

    def test_write_uses_final_enumerated_episode_indices(self):
        annotated = {
            "data": [{"idx": index} for index in range(3)],
            "detailed_task": {
                "action_config": [
                    {
                        "start_frame": 0,
                        "end_frame": 2,
                        "action_text": "pick up the cup",
                    }
                ]
            },
        }
        unannotated = {"data": [{"idx": 0}]}
        fake_dataset = SimpleNamespace(
            episodes_data_cached=[unannotated, annotated]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = write_detailed_task_annotations(Path(temp_dir), fake_dataset)
            self.assertIsNotNone(output_path)
            records = [
                json.loads(line)
                for line in output_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(records[0], {"episode_index": 0, "action_config": []})
        self.assertEqual(records[1]["episode_index"], 1)
        self.assertEqual(records[1]["action_config"][0]["end_frame"], 2)

    def test_invalid_overlap_is_rejected_before_writing(self):
        episode = {
            "data": [{"idx": index} for index in range(5)],
            "detailed_task": {
                "action_config": [
                    {"start_frame": 0, "end_frame": 3, "action_text": "one"},
                    {"start_frame": 2, "end_frame": 5, "action_text": "two"},
                ]
            },
        }
        with self.assertRaisesRegex(ValueError, "overlapping"):
            extract_detailed_task_segments(episode, episode_length=5)


if __name__ == "__main__":
    unittest.main()
