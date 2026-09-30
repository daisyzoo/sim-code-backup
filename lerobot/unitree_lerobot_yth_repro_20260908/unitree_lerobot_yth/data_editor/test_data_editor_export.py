import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5.QtWidgets import QApplication, QMessageBox

from data_editor_CN import (
    DatasetPlayer,
    RightPalmEeProjector,
    export_episode_frames,
    load_subtask_yaml,
    remap_subtask_segments,
    trajectory_sample_positions,
    validate_subtask_segments,
)


class TrajectorySamplePositionsTest(unittest.TestCase):
    def test_samples_three_points_per_second_for_three_seconds(self):
        samples = trajectory_sample_positions(
            current_index=100,
            total_frames=300,
            fps=15.0,
        )

        self.assertEqual(len(samples), 18)
        self.assertEqual([position for _, position in samples[:9]], list(range(55, 100, 5)))
        self.assertEqual([position for _, position in samples[9:]], list(range(105, 150, 5)))
        self.assertAlmostEqual(samples[0][0], -3.0)
        self.assertAlmostEqual(samples[-1][0], 3.0)

    def test_episode_boundary_only_returns_available_side(self):
        samples = trajectory_sample_positions(
            current_index=0,
            total_frames=300,
            fps=15.0,
        )

        self.assertEqual(len(samples), 9)
        self.assertTrue(all(relative_seconds > 0 for relative_seconds, _ in samples))
        self.assertEqual([position for _, position in samples], list(range(5, 50, 5)))


class RightPalmEeProjectorTest(unittest.TestCase):
    def test_verified_episode_0010_frame_zero_projection(self):
        projector = RightPalmEeProjector()
        frame_record = {
            "idx": 0,
            "states": {
                "right_arm": {
                    "qpos": [-0.205146, 0.036228, 0.03328, 0.295579, 0.279316]
                },
                "body": {"qpos": [-0.001192, 0.0, 0.0]},
            },
        }

        projection = projector.project_frame(frame_record)

        self.assertEqual(projection["pixels"].shape, (4, 2))
        self.assertTrue(np.all(projection["points_in_optical"][:, 2] > 0.0))
        np.testing.assert_allclose(
            projection["pixels"][0],
            np.array([507.03, 396.90]),
            atol=0.08,
        )

    def test_world_trajectory_uses_current_camera_extrinsic(self):
        projector = RightPalmEeProjector()
        right_arm_q = [-0.205146, 0.036228, 0.03328, 0.295579, 0.279316]

        def frame_record(frame_id, waist_yaw):
            return {
                "idx": frame_id,
                "states": {
                    "right_arm": {"qpos": right_arm_q},
                    "body": {"qpos": [waist_yaw, 0.0, 0.0]},
                },
            }

        current_geometry = projector.compute_frame_geometry(frame_record(0, 0.0))
        future_geometry = projector.compute_frame_geometry(frame_record(1, 0.3))
        current_pixel = projector.project_geometry(current_geometry)["pixels"][0]
        future_own_camera_pixel = projector.project_geometry(future_geometry)["pixels"][0]
        future_in_current_camera_pixel = projector.project_world_points(
            future_geometry["points_in_world"][:1],
            current_geometry,
        )["pixels"][0]

        # 腰和相机一起转动，在各自相机坐标下看起来几乎没有移动。
        np.testing.assert_allclose(future_own_camera_pixel, current_pixel, atol=1e-8)
        # 使用当前相机投影 future world 点后，腰部转动必须表现为图像位移。
        self.assertGreater(
            np.linalg.norm(future_in_current_camera_pixel - current_pixel),
            100.0,
        )


class ExportEpisodeFramesTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "episode_0000"
        self.source.mkdir()

        frames = []
        for idx in range(5):
            colors = {
                "color_0": f"colors/{idx:06d}_color_0.jpg",
                "color_1": f"colors/{idx:06d}_color_1.jpg",
            }
            depths = {"depth_0": f"depths/{idx:06d}_depth_0.png"}
            audios = {"mic_0": f"audios/audio_{idx:06d}_mic_0.npy"}

            for relative_path in [*colors.values(), *depths.values(), *audios.values()]:
                media_path = self.source / relative_path
                media_path.parent.mkdir(parents=True, exist_ok=True)
                media_path.write_bytes(f"frame-{idx}:{relative_path}".encode())

            frames.append(
                {
                    "idx": idx,
                    "colors": colors,
                    "depths": depths,
                    "audios": audios,
                    "states": {
                        "left_arm": {"qpos": [idx, idx + 0.1]},
                        "right_arm": {"qpos": [idx + 0.2]},
                    },
                    "actions": {"left_arm": {"qpos": [idx + 1.0]}},
                    "custom_frame_info": {"force": idx * 3, "valid": True},
                }
            )

        self.source_json = {
            "info": {"image": {"fps": 20}},
            "text": {"goal": "pick object"},
            "detailed_task": {
                "schema_version": 1,
                "action_config": [
                    {
                        "start_frame": 0,
                        "end_frame": 2,
                        "hotkey": "1",
                        "action_text": "pick up the cup",
                        "language_memory": "",
                        "color": "#4caf50",
                    },
                    {
                        "start_frame": 2,
                        "end_frame": 5,
                        "hotkey": "2",
                        "action_text": "pour water",
                        "language_memory": "The cup has been picked up.",
                        "color": "#2196f3",
                    },
                ],
            },
            "data": frames,
        }
        (self.source / "data.json").write_text(
            json.dumps(self.source_json, ensure_ascii=False), encoding="utf-8"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_exports_all_frame_data_and_referenced_media(self):
        destination = self.root / "episode_0001"

        exported_count = export_episode_frames(
            self.source, destination, frame_ids=[1, 2, 3]
        )

        self.assertEqual(exported_count, 3)
        exported = json.loads((destination / "data.json").read_text(encoding="utf-8"))
        self.assertEqual(exported["info"], self.source_json["info"])
        self.assertEqual(exported["text"], self.source_json["text"])
        self.assertEqual([item["idx"] for item in exported["data"]], [0, 1, 2])
        self.assertEqual(
            exported["detailed_task"]["action_config"],
            [
                {
                    "start_frame": 0,
                    "end_frame": 1,
                    "action_text": "pick up the cup",
                    "language_memory": "",
                    "hotkey": "1",
                    "color": "#4caf50",
                },
                {
                    "start_frame": 1,
                    "end_frame": 3,
                    "action_text": "pour water",
                    "language_memory": "The cup has been picked up.",
                    "hotkey": "2",
                    "color": "#2196f3",
                },
            ],
        )

        for new_idx, old_idx in enumerate([1, 2, 3]):
            old_item = self.source_json["data"][old_idx]
            new_item = exported["data"][new_idx]
            self.assertEqual(new_item["states"], old_item["states"])
            self.assertEqual(new_item["actions"], old_item["actions"])
            self.assertEqual(new_item["custom_frame_info"], old_item["custom_frame_info"])

            for media_field in ("colors", "depths", "audios"):
                for media_key, new_relative_path in new_item[media_field].items():
                    old_relative_path = old_item[media_field][media_key]
                    self.assertTrue((destination / new_relative_path).is_file())
                    self.assertEqual(
                        (destination / new_relative_path).read_bytes(),
                        (self.source / old_relative_path).read_bytes(),
                    )

        original_after_export = json.loads(
            (self.source / "data.json").read_text(encoding="utf-8")
        )
        self.assertEqual(original_after_export, self.source_json)

    def test_missing_media_does_not_leave_partial_episode(self):
        destination = self.root / "episode_0002"
        (self.source / "colors/000002_color_0.jpg").unlink()

        with self.assertRaisesRegex(RuntimeError, "关联媒体文件不存在"):
            export_episode_frames(self.source, destination, frame_ids=[1, 2])

        self.assertFalse(destination.exists())
        self.assertEqual(
            list(self.root.glob(".episode_0002.exporting-*")),
            [],
        )

    def test_editor_export_restores_cursor_and_selected_range(self):
        app = QApplication.instance() or QApplication([])
        player = DatasetPlayer(str(self.root))
        player.timer.stop()
        player.range_slider.set_selected_range(1, 3)
        player.current_frame_index = 2
        player.show_frame(2)
        self.assertTrue(player.prev_frame_btn.autoRepeat())
        self.assertTrue(player.next_frame_btn.autoRepeat())
        player.step_frame(-1)
        self.assertEqual(player.range_slider.current_frame, 1)
        player.step_frame(1)
        self.assertEqual(player.range_slider.current_frame, 2)
        self.assertEqual(player.range_slider.get_selected_range(), (1, 3))
        self.assertTrue(player.fast_prev_frame_shortcut.autoRepeat())
        self.assertTrue(player.fast_next_frame_shortcut.autoRepeat())
        player.set_current_as_range_boundary(is_start=True)
        self.assertEqual(player.range_slider.get_selected_range(), (2, 3))
        self.assertEqual(player.start_frame_spin.value(), 2)
        player.show_frame(4)
        player.set_current_as_range_boundary(is_start=False)
        self.assertEqual(player.range_slider.get_selected_range(), (2, 4))
        self.assertEqual(player.end_frame_spin.value(), 4)
        player.range_slider.set_selected_range(1, 3)
        player.show_frame(2)

        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes), patch.object(
            QMessageBox, "information", return_value=QMessageBox.Ok
        ):
            player.export_selected_frames_as_episode()

        self.assertTrue((self.root / "episode_0001" / "data.json").is_file())
        self.assertEqual(player.current_episode_name, "episode_0000")
        self.assertEqual(player.range_slider.current_frame, 2)
        self.assertEqual(player.current_frame_index, 2)
        self.assertEqual(player.range_slider.get_selected_range(), (1, 3))
        self.assertEqual(player.start_frame_spin.value(), 1)
        self.assertEqual(player.end_frame_spin.value(), 3)
        self.assertFalse(player.is_playing)
        player.close()
        app.processEvents()

    def test_hotkey_annotation_writes_half_open_segments(self):
        config_path = self.root / "subtasks.yaml"
        config_path.write_text(
            """
version: 1
subtasks:
  "1":
    action_text: pick up the cup
    color: "#4CAF50"
  "2":
    action_text: pour water
    language_memory: The cup has been picked up.
    color: "#2196F3"
""".strip(),
            encoding="utf-8",
        )
        app = QApplication.instance() or QApplication([])
        player = DatasetPlayer(str(self.root))
        player.timer.stop()
        player.subtask_segments = []
        player.save_current_subtask_segments()
        player.load_subtask_config(config_path)

        player.show_frame(0)
        player.mark_annotation_start()
        player.show_frame(2)
        player.annotate_subtask_hotkey("1")
        player.show_frame(4)
        player.annotate_subtask_hotkey("2")
        player.mark_annotation_end()

        saved = json.loads((self.source / "data.json").read_text(encoding="utf-8"))
        self.assertEqual(
            saved["detailed_task"]["action_config"],
            [
                {
                    "start_frame": 0,
                    "end_frame": 3,
                    "action_text": "pick up the cup",
                    "language_memory": "",
                    "hotkey": "1",
                    "color": "#4caf50",
                },
                {
                    "start_frame": 3,
                    "end_frame": 5,
                    "action_text": "pour water",
                    "language_memory": "The cup has been picked up.",
                    "hotkey": "2",
                    "color": "#2196f3",
                },
            ],
        )
        self.assertEqual(player.subtask_anchor_position, 5)
        player.close()
        app.processEvents()

    def test_destructive_trim_remaps_saved_subtasks(self):
        app = QApplication.instance() or QApplication([])
        player = DatasetPlayer(str(self.root))
        player.timer.stop()

        player.delete_and_renumber_frames(delete_frame_ids=[1, 2])

        saved = json.loads((self.source / "data.json").read_text(encoding="utf-8"))
        self.assertEqual([item["idx"] for item in saved["data"]], [0, 1, 2])
        self.assertEqual(
            [
                (item["start_frame"], item["end_frame"], item["action_text"])
                for item in saved["detailed_task"]["action_config"]
            ],
            [(0, 1, "pick up the cup"), (1, 3, "pour water")],
        )
        player.close()
        app.processEvents()


class SubtaskAnnotationHelpersTest(unittest.TestCase):
    def test_yaml_short_form_and_default_color(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "subtasks.yaml"
            config_path.write_text(
                'subtasks:\n  "1": pick up the cup\n', encoding="utf-8"
            )
            definitions = load_subtask_yaml(config_path)
        self.assertEqual(definitions["1"]["action_text"], "pick up the cup")
        self.assertEqual(definitions["1"]["color"], "#4caf50")

    def test_overlap_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "不能重叠"):
            validate_subtask_segments(
                [
                    {"start_frame": 0, "end_frame": 5, "action_text": "one"},
                    {"start_frame": 4, "end_frame": 8, "action_text": "two"},
                ],
                frame_count=10,
            )

    def test_deleted_middle_frames_remap_and_preserve_unlabelled_gap(self):
        segments = [
            {"start_frame": 0, "end_frame": 4, "action_text": "one"},
            {"start_frame": 6, "end_frame": 9, "action_text": "two"},
        ]
        # Keep old positions 0, 1, 4, 5, 6, 8, 9. Old positions 4 and 5
        # remain unlabelled and therefore form a two-frame gap in the result.
        remapped = remap_subtask_segments(segments, [0, 1, 4, 5, 6, 8, 9])
        self.assertEqual(
            [(item["start_frame"], item["end_frame"]) for item in remapped],
            [(0, 2), (4, 6)],
        )


if __name__ == "__main__":
    unittest.main()
