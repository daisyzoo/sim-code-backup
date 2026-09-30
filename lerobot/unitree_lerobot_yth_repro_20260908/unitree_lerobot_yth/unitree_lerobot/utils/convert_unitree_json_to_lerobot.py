"""
Script Json to Lerobot.

# --raw-dir     Corresponds to the directory of your JSON dataset
# --repo-id     Your unique repo ID on Hugging Face Hub
# --robot_type  The type of the robot used in the dataset (e.g., Unitree_Z1_Single, Unitree_Z1_Dual, Unitree_G1_Dex1, Unitree_G1_Dex3, Unitree_G1_Brainco, Unitree_G1_Inspire)
# --push_to_hub Whether or not to upload the dataset to Hugging Face Hub (true or false)

python unitree_lerobot/utils/convert_unitree_json_to_lerobot.py \
    --raw-dir $HOME/datasets/g1_grabcube_double_hand \
    --repo-id your_name/g1_grabcube_double_hand \
    --robot_type Unitree_G1_Dex3 \
    --push_to_hub
"""

import os
import cv2
import tqdm
import tyro
import json
import glob
import dataclasses
import shutil
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Literal
import re

from lerobot.utils.constants import HF_LEROBOT_HOME
from lerobot.datasets.lerobot_dataset import LeRobotDataset

from unitree_lerobot.utils.constants import ROBOT_CONFIGS


@dataclasses.dataclass(frozen=True)
class DatasetConfig:
    use_videos: bool = True
    tolerance_s: float = 0.0001
    image_writer_processes: int = 10
    image_writer_threads: int = 5
    video_backend: str | None = None


DEFAULT_DATASET_CONFIG = DatasetConfig()


def extract_detailed_task_segments(episode_data: dict, episode_length: int) -> list[dict]:
    """Validate raw data.json annotations and return InternVLA JSONL fields."""
    detailed_task = episode_data.get("detailed_task", {})
    if detailed_task in (None, ""):
        return []
    if not isinstance(detailed_task, dict):
        raise ValueError("data.json detailed_task must be a dictionary")
    raw_segments = detailed_task.get("action_config", [])
    if not isinstance(raw_segments, list):
        raise ValueError("data.json detailed_task.action_config must be a list")

    segments = []
    for raw_segment in raw_segments:
        if not isinstance(raw_segment, dict):
            raise ValueError("each detailed_task.action_config item must be a dictionary")
        start = int(raw_segment["start_frame"])
        end = int(raw_segment["end_frame"])
        action_text = str(raw_segment.get("action_text", "")).strip()
        language_memory = str(raw_segment.get("language_memory", "")).strip()
        if start < 0 or end <= start or end > episode_length:
            raise ValueError(
                f"invalid subtask interval [{start}, {end}) for episode length {episode_length}"
            )
        if not action_text:
            raise ValueError(f"subtask interval [{start}, {end}) has empty action_text")
        segments.append(
            {
                "start_frame": start,
                "end_frame": end,
                "action_text": action_text,
                "language_memory": language_memory,
            }
        )

    segments.sort(key=lambda item: (item["start_frame"], item["end_frame"]))
    for previous, current in zip(segments, segments[1:]):
        if current["start_frame"] < previous["end_frame"]:
            raise ValueError(
                "overlapping subtask intervals: "
                f"[{previous['start_frame']}, {previous['end_frame']}) and "
                f"[{current['start_frame']}, {current['end_frame']})"
            )
    return segments


def write_detailed_task_annotations(dataset_root: Path, json_dataset: "JsonDataset") -> Path | None:
    """Write final episode-indexed annotations after conversion assigns indices."""
    records = []
    has_annotations = False
    for episode_index, episode_data in enumerate(json_dataset.episodes_data_cached):
        episode_length = len(episode_data.get("data", []))
        try:
            segments = extract_detailed_task_segments(episode_data, episode_length)
        except (KeyError, TypeError, ValueError) as exc:
            episode_path = (
                json_dataset.episode_paths[episode_index]
                if hasattr(json_dataset, "episode_paths")
                else f"episode_index={episode_index}"
            )
            raise ValueError(f"Invalid detailed task annotations in {episode_path}: {exc}") from exc
        has_annotations = has_annotations or bool(segments)
        records.append(
            {"episode_index": episode_index, "action_config": segments}
        )

    if not has_annotations:
        return None

    annotations_path = Path(dataset_root) / "meta" / "episodes_detailed_task.jsonl"
    annotations_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = annotations_path.with_name(f".{annotations_path.name}.tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, annotations_path)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise

    print(f"==> Wrote detailed subtask annotations: {annotations_path}")
    return annotations_path


class JsonDataset:
    def __init__(self, data_dirs: Path, robot_type: str) -> None:
        """
        Initialize the dataset for loading and processing HDF5 files containing robot manipulation data.

        Args:
            data_dirs: Path to directory containing training data
        """
        assert data_dirs is not None, "Data directory cannot be None"
        assert robot_type is not None, "Robot type cannot be None"
        self.data_dirs = data_dirs
        self.json_file = "data.json"

        # Initialize paths and cache
        self._init_paths()
        self._init_cache()
        self.json_state_data_name = ROBOT_CONFIGS[robot_type].json_state_data_name
        self.json_action_data_name = ROBOT_CONFIGS[robot_type].json_action_data_name
        self.camera_to_image_key = ROBOT_CONFIGS[robot_type].camera_to_image_key
        self.fps = self._infer_fps()

    def _init_paths(self) -> None:
        """Initialize episode and task paths."""

        self.episode_paths = []
        self.task_paths = []

        for task_path in glob.glob(os.path.join(self.data_dirs, "*")):
            if os.path.isdir(task_path):
                episode_paths = glob.glob(os.path.join(task_path, "*"))
                if episode_paths:
                    self.task_paths.append(task_path)
                    self.episode_paths.extend(episode_paths)

        self.episode_paths = sorted(self.episode_paths)
        self.episode_ids = list(range(len(self.episode_paths)))

    def __len__(self) -> int:
        """Return the number of episodes in the dataset."""
        return len(self.episode_paths)

    def _init_cache(self) -> list:
        """Initialize data cache if enabled."""

        self.episodes_data_cached = []
        for episode_path in tqdm.tqdm(self.episode_paths, desc="Loading Cache Json"):
            json_path = os.path.join(episode_path, self.json_file)
            with open(json_path, encoding="utf-8") as jsonf:
                self.episodes_data_cached.append(json.load(jsonf))

        print(f"==> Cached {len(self.episodes_data_cached)} episodes")

        return self.episodes_data_cached

    def _infer_fps(self) -> int:
        """Infer dataset FPS from metadata and ensure it is consistent across episodes."""

        fps_values = []
        for episode_data in self.episodes_data_cached:
            image_info = episode_data.get("info", {}).get("image", {})
            fps = image_info.get("fps")
            if fps is not None:
                fps_values.append(float(fps))

        if not fps_values:
            return 30

        reference_fps = fps_values[0]
        for fps in fps_values[1:]:
            if not np.isclose(fps, reference_fps):
                raise ValueError(f"Inconsistent FPS found in dataset: {fps_values}")

        return int(round(reference_fps))

    def _extract_data(self, episode_data: dict, key: str, parts: list[str]) -> np.ndarray:
        """
        Extract data from episode dictionary for specified parts.

        Args:
            episode_data: Dictionary containing episode data
            key: Data key to extract ('states' or 'actions')
            parts: List of parts to include ('left_arm', 'right_arm')

        Returns:
            Concatenated numpy array of the requested data
        """
        result = []
        for sample_data in episode_data["data"]:
            data_array = np.array([], dtype=np.float32)
            for part in parts:
                qpos = self._resolve_data_path(sample_data[key], part)
                if qpos is None:
                    raise ValueError(f"qpos is None for part: {part}")
                if isinstance(qpos, list):
                    qpos = np.array(qpos, dtype=np.float32).flatten()
                else:
                    qpos = np.array([qpos], dtype=np.float32).flatten()
                data_array = np.concatenate([data_array, qpos])
            result.append(data_array)
        return np.array(result)

    def _resolve_data_path(self, data: dict, path: str):
        """Resolve nested dict/list values from a dot path with optional list indexing."""

        current = data
        for token in path.split("."):
            match = re.fullmatch(r"([^\[]+)(?:\[(\d+)\])?", token)
            if match is None:
                raise ValueError(f"Invalid path token: {token}")

            key, index_str = match.groups()
            if not isinstance(current, dict) or key not in current:
                raise ValueError(f"Missing key '{key}' while resolving path: {path}")

            current = current[key]
            if current is None:
                return None

            if index_str is not None:
                if not isinstance(current, list):
                    raise ValueError(f"Expected list at '{key}' while resolving path: {path}")
                index = int(index_str)
                if index >= len(current):
                    raise IndexError(f"Index {index} out of range for path: {path}")
                current = current[index]

        return current

    def _parse_images(self, episode_path: str, episode_data) -> dict[str, list[np.ndarray]]:
        """Load and stack images for a given camera key."""

        images = defaultdict(list)

        keys = episode_data["data"][0]["colors"].keys()
        cameras = [key for key in keys if "depth" not in key]

        for camera in cameras:
            image_key = self.camera_to_image_key.get(camera)
            if image_key is None:
                continue

            for sample_data in episode_data["data"]:
                relative_path = sample_data["colors"].get(camera)
                if not relative_path:
                    continue

                image_path = os.path.join(episode_path, relative_path)
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Image path does not exist: {image_path}")

                image = cv2.imread(image_path)
                if image is None:
                    raise RuntimeError(f"Failed to read image: {image_path}")

                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                images[image_key].append(image_rgb)

        return images

    def get_item(
        self,
        index: int | None = None,
    ) -> dict:
        """Get a training sample from the dataset."""

        file_path = np.random.choice(self.episode_paths) if index is None else self.episode_paths[index]
        episode_data = self.episodes_data_cached[index]

        # Load state and action data
        action = self._extract_data(episode_data, "actions", self.json_action_data_name)
        state = self._extract_data(episode_data, "states", self.json_state_data_name)
        episode_length = len(state)
        state_dim = state.shape[1] if len(state.shape) == 2 else state.shape[0]
        action_dim = action.shape[1] if len(action.shape) == 2 else state.shape[0]

        # Load task description
        task = episode_data.get("text", {}).get("goal", "")

        # Load camera images
        cameras = self._parse_images(file_path, episode_data)

        # Extract camera configuration
        cam_height, cam_width = next(img for imgs in cameras.values() if imgs for img in imgs).shape[:2]
        data_cfg = {
            "camera_names": list(cameras.keys()),
            "cam_height": cam_height,
            "cam_width": cam_width,
            "state_dim": state_dim,
            "action_dim": action_dim,
        }

        return {
            "episode_index": index,
            "episode_length": episode_length,
            "state": state,
            "action": action,
            "cameras": cameras,
            "task": task,
            "data_cfg": data_cfg,
        }


def create_empty_dataset(
    repo_id: str,
    robot_type: str,
    fps: int,
    mode: Literal["video", "image"] = "video",
    root: Path | None = None,
    *,
    has_velocity: bool = False,
    has_effort: bool = False,
    dataset_config: DatasetConfig = DEFAULT_DATASET_CONFIG,
) -> LeRobotDataset:
    motors = ROBOT_CONFIGS[robot_type].motors
    cameras = ROBOT_CONFIGS[robot_type].cameras

    features = {
        "observation.state": {
            "dtype": "float32",
            "shape": (len(motors),),
            "names": [
                motors,
            ],
        },
        "action": {
            "dtype": "float32",
            "shape": (len(motors),),
            "names": [
                motors,
            ],
        },
    }

    if has_velocity:
        features["observation.velocity"] = {
            "dtype": "float32",
            "shape": (len(motors),),
            "names": [
                motors,
            ],
        }

    if has_effort:
        features["observation.effort"] = {
            "dtype": "float32",
            "shape": (len(motors),),
            "names": [
                motors,
            ],
        }

    for cam in cameras:
        features[f"observation.images.{cam}"] = {
            "dtype": mode,
            "shape": (480, 640, 3),
            "names": [
                "height",
                "width",
                "channel",
            ],
        }

    dataset_root = Path(root) if root is not None else Path(HF_LEROBOT_HOME / repo_id)
    if dataset_root.exists():
        shutil.rmtree(dataset_root)

    return LeRobotDataset.create(
        repo_id=repo_id,
        fps=fps,
        robot_type=robot_type,
        features=features,
        root=dataset_root,
        use_videos=dataset_config.use_videos,
        tolerance_s=dataset_config.tolerance_s,
        image_writer_processes=dataset_config.image_writer_processes,
        image_writer_threads=dataset_config.image_writer_threads,
        video_backend=dataset_config.video_backend,
    )


def populate_dataset(
    dataset: LeRobotDataset,
    raw_dir: Path,
    robot_type: str,
    json_dataset: JsonDataset | None = None,
) -> LeRobotDataset:
    if json_dataset is None:
        json_dataset = JsonDataset(raw_dir, robot_type)
    for i in tqdm.tqdm(range(len(json_dataset))):
        episode = json_dataset.get_item(i)

        state = episode["state"]
        action = episode["action"]
        cameras = episode["cameras"]
        task = episode["task"]
        episode_length = episode["episode_length"]

        num_frames = episode_length
        for i in range(num_frames):
            frame = {
                "observation.state": state[i],
                "action": action[i],
            }

            for camera, img_array in cameras.items():
                frame[f"observation.images.{camera}"] = img_array[i]

            frame["task"] = task

            dataset.add_frame(frame)
        dataset.save_episode()

    return dataset


def json_to_lerobot(
    raw_dir: Path,
    repo_id: str,
    robot_type: str,  # e.g., Unitree_Z1_Single, Unitree_Z1_Dual, Unitree_G1_Dex1, Unitree_G1_Dex3, Unitree_G1_Brainco, Unitree_G1_Inspire
    root: Path | None = None,
    *,
    push_to_hub: bool = False,
    mode: Literal["video", "image"] = "video",
    dataset_config: DatasetConfig = DEFAULT_DATASET_CONFIG,
):
    dataset_root = Path(root) if root is not None else Path(HF_LEROBOT_HOME / repo_id)
    if dataset_root.exists():
        shutil.rmtree(dataset_root)

    json_dataset = JsonDataset(raw_dir, robot_type)
    dataset = create_empty_dataset(
        repo_id,
        robot_type=robot_type,
        fps=json_dataset.fps,
        mode=mode,
        root=dataset_root,
        has_effort=False,
        has_velocity=False,
        dataset_config=dataset_config,
    )
    dataset = populate_dataset(dataset, raw_dir, robot_type=robot_type, json_dataset=json_dataset)
    write_detailed_task_annotations(dataset.root, json_dataset)

    if push_to_hub:
        dataset.push_to_hub(upload_large_folder=True)


def local_push_to_hub(
    repo_id: str,
    root_path: Path,
):
    dataset = LeRobotDataset(repo_id=repo_id, root=root_path)
    dataset.push_to_hub(upload_large_folder=True)


if __name__ == "__main__":
    tyro.cli(json_to_lerobot)
