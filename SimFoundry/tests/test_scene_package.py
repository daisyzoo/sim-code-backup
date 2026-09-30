from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simfoundry.adapter.backends.mesh import FromLibraryBackend
from simfoundry.adapter.backends.stubs import DepthAnythingBackend, UnimplementedBackendError
from simfoundry.adapter.backends.vlm import StubVlmBackend
from simfoundry.adapter.pipeline import build_placeholder_kitchen
from simfoundry.data.schema import TrajectoryEpisode, load_episode, save_episode
from simfoundry.data.scripted import scripted_action
from simfoundry.embodiment import EMBODIMENT_ID, G1_23DOF_JOINT_NAMES
from simfoundry.scene_bridge.transforms import world_pose
from simfoundry.scene_bridge.usda import package_to_usda
from simfoundry.scene_package import filter_tasks, load_named_scene, load_scene_package


class ScenePackageTests(unittest.TestCase):
    def test_placeholder_scene_contract(self) -> None:
        package = load_named_scene("kitchen_counter_placeholder")
        self.assertEqual(package.scene_id, "kitchen_counter_placeholder")
        meta = json.loads((Path(package.root) / "meta.json").read_text())
        self.assertNotIn("robot_dof", meta)
        names = [o.name for o in package.objects]
        self.assertEqual(names, ["counter", "cup", "bowl", "plate", "bottle"])
        self.assertTrue(package.objects[0].kinematic)
        stump = filter_tasks(package, "stump")
        self.assertEqual(
            {t.task_id for t in stump},
            {"approach_counter", "reach_cup", "push_cup_to_bowl", "pick_cup"},
        )
        self.assertTrue(any(t.requires_ee == "dexhand" for t in package.tasks))
        cup = next(o for o in package.objects if o.name == "cup")
        world = world_pose(package.table_frame, cup)
        self.assertGreater(world.pos[2], package.table_frame.pos[2])

    def test_stump_filter_drops_grasp(self) -> None:
        package = load_named_scene("kitchen_counter_placeholder")
        stump_ids = {t.task_id for t in filter_tasks(package, "stump")}
        self.assertNotIn("place_cup_in_bowl", stump_ids)
        self.assertIn("push_cup_to_bowl", stump_ids)

    def test_from_library_and_vlm_stubs(self) -> None:
        cup = FromLibraryBackend().generate(None, semantic="cup")
        self.assertEqual(cup.kind, "usd")
        self.assertEqual(cup.primitive["shape"], "usd")
        self.assertTrue(str(cup.primitive["usd_path"]).endswith("025_mug.usd"))
        tasks = StubVlmBackend().propose_tasks({})
        ids = {t.task_id for t in tasks}
        self.assertIn("push_cup_to_bowl", ids)
        self.assertIn("place_cup_in_bowl", ids)
        with self.assertRaises(UnimplementedBackendError):
            DepthAnythingBackend().infer(None)

    def test_pipeline_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = build_placeholder_kitchen(tmp, scene_id="kitchen_counter_placeholder")
            reloaded = load_scene_package(package.root)
            self.assertEqual(
                [o.semantic for o in reloaded.objects],
                ["counter", "cup", "bowl", "plate", "bottle"],
            )
            usda = package_to_usda(reloaded)
            self.assertIn("#usda 1.0", usda)
            self.assertIn('def Xform "cup"', usda)
            self.assertNotIn("robot_dof", usda)

    def test_trajectory_schema(self) -> None:
        t = 5
        episode = TrajectoryEpisode(
            rgb=np.zeros((t, 3, 480, 640), dtype=np.uint8),
            q=np.zeros((t, 23), dtype=np.float32),
            action=np.stack([scripted_action("push_cup_to_bowl", i, t) for i in range(t)]),
            instruction="Push the cup toward the bowl on the kitchen counter.",
            scene_id="kitchen_counter_placeholder",
            task_id="push_cup_to_bowl",
            embodiment_id=EMBODIMENT_ID,
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = save_episode(episode, Path(tmp) / "ep.npz")
            loaded = load_episode(path)
        self.assertEqual(loaded.q.shape, (5, 23))
        self.assertEqual(loaded.rgb.shape, (5, 3, 480, 640))
        self.assertEqual(loaded.joint_names, G1_23DOF_JOINT_NAMES)
        with self.assertRaises(KeyError):
            scripted_action("place_cup_in_bowl", 0, 10)

    def test_lerobot_v21_export(self) -> None:
        from simfoundry.data.lerobot_v21 import IMAGE_KEY, export_episodes_to_lerobot

        t = 4
        # Non-zero pattern so video encoder has content.
        rgb = np.zeros((t, 3, 480, 640), dtype=np.uint8)
        rgb[:, 0, :, :] = 40
        rgb[:, 1, :, :] = 80
        rgb[:, 2, :, :] = 120
        episode = TrajectoryEpisode(
            rgb=rgb,
            q=np.linspace(0, 1, t * 23, dtype=np.float32).reshape(t, 23),
            action=np.stack([scripted_action("push_cup_to_bowl", i, t) for i in range(t)]),
            instruction="Push the cup toward the bowl on the kitchen counter.",
            scene_id="kitchen_counter_placeholder",
            task_id="push_cup_to_bowl",
            embodiment_id=EMBODIMENT_ID,
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "lerobot"
            result = export_episodes_to_lerobot([episode], out, fps=30.0, overwrite=True)
            self.assertEqual(result.num_episodes, 1)
            self.assertEqual(result.num_frames, 4)
            info = json.loads((out / "meta" / "info.json").read_text())
            self.assertEqual(info["codebase_version"], "v2.1")
            self.assertEqual(info["robot_type"], EMBODIMENT_ID)
            self.assertIn(IMAGE_KEY, info["features"])
            self.assertEqual(info["features"][IMAGE_KEY]["shape"], [480, 640, 3])
            self.assertTrue((out / "data" / "chunk-000" / "episode_000000.parquet").is_file())
            video = out / "videos" / "chunk-000" / IMAGE_KEY / "episode_000000.mp4"
            self.assertTrue(video.is_file())
            self.assertGreater(video.stat().st_size, 0)
            tasks = (out / "meta" / "tasks.jsonl").read_text().strip().splitlines()
            self.assertEqual(len(tasks), 1)
            side = json.loads((out / "meta" / "simfoundry.json").read_text())
            self.assertEqual(side["camera"]["key"], IMAGE_KEY)

    def test_indoor_lab_connected_world(self) -> None:
        package = load_named_scene("indoor_lab_g1_23")
        self.assertEqual(package.scene_id, "indoor_lab_g1_23")
        names = {o.name for o in package.objects}
        self.assertTrue(
            {
                "hall_wall_left",
                "door",
                "wall_button",
                "person",
                "counter",
                "cup",
                "lab_bench",
                "floor_marker",
            }.issubset(names)
        )
        ids = {t.task_id for t in package.tasks}
        self.assertIn("wave_hello", ids)
        self.assertIn("enter_and_push_cup", ids)
        self.assertTrue(all(t.requires_ee == "stump" for t in package.tasks))
        door = next(o for o in package.objects if o.name == "door")
        counter = next(o for o in package.objects if o.name == "counter")
        self.assertGreater(counter.pos[0], door.pos[0])
        self.assertGreater(door.pos[0], 0.0)
        usda = package_to_usda(package)
        self.assertIn('def Xform "door"', usda)
        self.assertIn('def Xform "lab_bench"', usda)
        wave = scripted_action("wave_hello", 20, 40)
        self.assertEqual(wave.shape, (23,))
        self.assertGreater(float(np.abs(wave).sum()), 0.0)
        from simfoundry.data.scripted import walking_gait

        gait = walking_gait(0.2, amplitude=1.0)
        self.assertEqual(gait.shape, (23,))
        self.assertGreater(float(np.abs(gait[:12]).sum()), 0.0)
        door = scripted_action("push_door", 20, 40)
        self.assertGreater(float(np.abs(door).sum()), 0.0)
        press = scripted_action("press_table_switch", 20, 40)
        self.assertGreater(float(np.abs(press).sum()), 0.0)

    def test_sorting_station_independent(self) -> None:
        kitchen = load_named_scene("kitchen_counter_placeholder")
        self.assertEqual([o.name for o in kitchen.objects], ["counter", "cup", "bowl", "plate", "bottle"])

        package = load_named_scene("sorting_station_g1_23")
        self.assertEqual(package.scene_id, "sorting_station_g1_23")
        meta = json.loads((Path(package.root) / "meta.json").read_text())
        self.assertNotIn("robot_dof", meta)
        names = [o.name for o in package.objects]
        self.assertIn("table", names)
        self.assertIn("table_edge_wear", names)
        self.assertIn("parcel_box", names)
        self.assertIn("parcel_box_label", names)
        self.assertIn("mailer", names)
        self.assertIn("mailer_label", names)
        self.assertIn("mailer_b", names)
        self.assertIn("mailer_d", names)
        self.assertIn("yellow_chair", names)
        self.assertIn("equipment_wrap", names)
        self.assertIn("bin_mailer", names)
        self.assertIn("backdrop_panel", names)
        self.assertIn("pc_tower", names)
        self.assertIn("metal_rack", names)
        self.assertNotIn("cup", names)
        self.assertNotIn("counter", names)

        table = next(o for o in package.objects if o.name == "table")
        self.assertEqual(table.size, (0.60, 1.50, 0.025))
        self.assertAlmostEqual(package.table_frame.pos[2], 0.7375)
        self.assertLess(package.table_frame.pos[0], 0.70)
        self.assertTrue(table.kinematic)
        # Powder-blue desk from real capture (not oversaturated cyan).
        self.assertGreater(table.color[2], table.color[0])
        self.assertGreater(table.color[1], table.color[0])
        self.assertLess(table.color[2], 0.90)
        box_obj = next(o for o in package.objects if o.name == "parcel_box")
        mailer_obj = next(o for o in package.objects if o.name == "mailer")
        self.assertEqual(box_obj.size, (0.14, 0.09, 0.045))
        self.assertEqual(mailer_obj.size, (0.15, 0.145, 0.04))
        self.assertGreater(box_obj.color[0], 0.70)
        self.assertGreater(box_obj.color[1], 0.50)
        self.assertLess(box_obj.color[2], 0.50)
        self.assertLess(max(mailer_obj.color), 0.08)
        mailer_b = next(o for o in package.objects if o.name == "mailer_b")
        self.assertEqual(mailer_b.size, (0.12, 0.075, 0.035))
        self.assertLess(max(mailer_b.color), 0.10)
        parcels = ROOT / "assets" / "textures" / "sorting_station" / "parcels"
        manifest = json.loads((parcels / "manifest.json").read_text())
        for obj_name, filename in manifest["object_to_file"].items():
            self.assertTrue((parcels / filename).is_file(), msg=f"missing photo for {obj_name}")
            self.assertIn(obj_name, names)

        stump = filter_tasks(package, "stump")
        self.assertEqual(
            {t.task_id for t in stump},
            {"approach_table", "push_box_to_bin", "nudge_mailer_to_bin", "sweep_parcels_apart", "pick_cube", "wait_no_package"},
        )
        self.assertTrue(any(t.requires_ee == "dexhand" for t in package.tasks))
        self.assertNotIn("pick_box_into_bin", {t.task_id for t in stump})

        push = scripted_action("push_box_to_bin", 20, 40)
        self.assertEqual(push.shape, (23,))
        self.assertGreater(float(np.abs(push).sum()), 0.0)
        sweep = scripted_action("sweep_parcels_apart", 20, 40)
        self.assertGreater(float(np.abs(sweep).sum()), 0.0)
        idle = scripted_action("approach_table", 0, 10)
        self.assertTrue(np.allclose(idle, 0.0))

        box = FromLibraryBackend().generate(None, semantic="parcel_box")
        self.assertEqual(box.kind, "primitive")
        self.assertEqual(box.primitive["size"], [0.13, 0.08, 0.025])
        mailer = FromLibraryBackend().generate(None, semantic="mailer")
        self.assertEqual(mailer.primitive["size"], [0.15, 0.15, 0.030])
        klt = FromLibraryBackend().generate(None, semantic="klt_bin")
        self.assertEqual(klt.kind, "primitive")
        self.assertEqual(klt.primitive["size"], [0.38, 0.28, 0.17])
        self.assertLess(max(klt.primitive["color"]), 0.12)

        usda = package_to_usda(package)
        self.assertIn('def Xform "table"', usda)
        self.assertIn('def Xform "parcel_box"', usda)
        self.assertIn('def Xform "mailer_label"', usda)
        self.assertIn('def Xform "mailer_b"', usda)
        self.assertIn('def Xform "backdrop_panel"', usda)
        self.assertIn('def Xform "bin_box"', usda)

        indoor = load_named_scene("indoor_lab_g1_23")
        self.assertEqual(indoor.scene_id, "indoor_lab_g1_23")
        self.assertIn("door", {o.name for o in indoor.objects})

    def test_parcel_photo_pools(self) -> None:
        from simfoundry.scene_bridge.parcel_photos import choose_parcel_albedos, load_photo_pools

        pools = load_photo_pools()
        self.assertEqual(len(pools["box"]), 4)
        self.assertEqual(len(pools["mailer"]), 5)
        for path in (*pools["box"], *pools["mailer"]):
            self.assertTrue(path.is_file())
            self.assertEqual(path.suffix, ".png")
            self.assertTrue(path.name.startswith("box_") or path.name.startswith("mailer_"))
            self.assertTrue((path.parent / f"{path.stem}_n.png").is_file())
        a = choose_parcel_albedos(np.random.default_rng(0))
        b = choose_parcel_albedos(np.random.default_rng(0))
        self.assertEqual(a["parcel_box"], b["parcel_box"])
        self.assertEqual(a["mailer"], b["mailer"])
        self.assertTrue(a["parcel_box"].name.startswith("box_"))
        self.assertTrue(a["mailer"].name.startswith("mailer_"))
        self.assertIn(a["parcel_box"], pools["box"])
        self.assertIn(a["mailer"], pools["mailer"])

    def test_unitree_json_export_matches_real_layout(self) -> None:
        from simfoundry.data.unitree_json import export_episode_unitree_json, _split_23

        t = 3
        rgb = np.zeros((t, 3, 480, 640), dtype=np.uint8)
        rgb[:, 0] = 10
        rgb[:, 1] = 20
        rgb[:, 2] = 30
        q = np.linspace(0, 1, t * 23, dtype=np.float32).reshape(t, 23)
        act = q.copy()
        episode = TrajectoryEpisode(
            rgb=rgb,
            q=q,
            action=act,
            instruction="Push the kraft box toward the black bin.",
            scene_id="sorting_station_g1_23",
            task_id="push_box_to_bin",
            embodiment_id="g1_edu_23_u1_rubber",
        )
        with tempfile.TemporaryDirectory() as tmp:
            ep_dir = export_episode_unitree_json(episode, Path(tmp) / "task", fps=15.0)
            self.assertTrue((ep_dir / "data.json").is_file())
            colors = list((ep_dir / "colors").glob("*_color_0.jpg"))
            self.assertEqual(len(colors), 3)
            payload = json.loads((ep_dir / "data.json").read_text())
            self.assertEqual(payload["info"]["image"]["width"], 640)
            self.assertEqual(payload["info"]["image"]["height"], 480)
            self.assertEqual(payload["info"]["image"]["fps"], 15.0)
            self.assertEqual(len(payload["info"]["joint_names"]["left_arm"]), 5)
            self.assertEqual(len(payload["data"]), 3)
            fr = payload["data"][1]
            self.assertEqual(fr["colors"]["color_0"], "colors/000001_color_0.jpg")
            self.assertEqual(len(fr["states"]["left_arm"]["qpos"]), 5)
            self.assertEqual(len(fr["states"]["right_arm"]["qpos"]), 5)
            self.assertEqual(len(fr["states"]["body"]["qpos"]), 3)
            self.assertAlmostEqual(fr["states"]["body"]["qpos"][0], float(q[1, 12]), places=5)
            split = _split_23(q[1])
            self.assertEqual(split["left_arm"]["qpos"], fr["states"]["left_arm"]["qpos"])


if __name__ == "__main__":
    unittest.main()
