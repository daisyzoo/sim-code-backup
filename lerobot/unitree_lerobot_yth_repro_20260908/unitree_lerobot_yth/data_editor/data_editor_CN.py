import os
import re
import sys
import json
import copy
import math
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pinocchio as pin
import yaml
from PyQt5.QtCore import Qt, QTimer, QRect, QPointF, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QPolygonF, QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
    QFrame,
    QFileDialog,
    QSpinBox,
    QShortcut,
)


MEDIA_FIELDS = ("colors", "depths", "audios")
DETAILED_TASK_KEY = "detailed_task"
ACTION_CONFIG_KEY = "action_config"
SUBTASK_DEFAULT_COLORS = (
    "#4CAF50",
    "#2196F3",
    "#FF9800",
    "#9C27B0",
    "#00ACC1",
    "#E91E63",
    "#8BC34A",
    "#795548",
    "#607D8B",
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
G1_23_URDF_PATH = PROJECT_ROOT / "unitree_lerobot/eval_robot/assets/g1/g1_body23.urdf"


def load_subtask_yaml(config_path):
    """加载并严格校验数字键 1～9 的 subtask 定义。"""
    config_path = Path(config_path).expanduser().resolve()
    if not config_path.is_file():
        raise RuntimeError(f"Subtask YAML 不存在：{config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f)
    if not isinstance(payload, dict):
        raise RuntimeError("Subtask YAML 顶层必须是字典。")
    raw_subtasks = payload.get("subtasks")
    if not isinstance(raw_subtasks, dict) or not raw_subtasks:
        raise RuntimeError("Subtask YAML 必须包含非空的 subtasks 字典。")

    definitions = {}
    for raw_hotkey, raw_definition in raw_subtasks.items():
        hotkey = str(raw_hotkey).strip()
        if hotkey not in {str(index) for index in range(1, 10)}:
            raise RuntimeError(f"Subtask 热键只能是 1～9，实际为：{raw_hotkey!r}")
        if hotkey in definitions:
            raise RuntimeError(f"Subtask YAML 中存在重复热键：{hotkey}")
        if isinstance(raw_definition, str):
            raw_definition = {"action_text": raw_definition}
        if not isinstance(raw_definition, dict):
            raise RuntimeError(f"热键 {hotkey} 的定义必须是字符串或字典。")

        action_text = str(raw_definition.get("action_text", "")).strip()
        if not action_text:
            raise RuntimeError(f"热键 {hotkey} 缺少非空 action_text。")
        language_memory = str(raw_definition.get("language_memory", "")).strip()
        default_color = SUBTASK_DEFAULT_COLORS[int(hotkey) - 1]
        color = str(raw_definition.get("color", default_color)).strip()
        parsed_color = QColor(color)
        if not parsed_color.isValid():
            raise RuntimeError(f"热键 {hotkey} 的颜色无效：{color!r}")
        definitions[hotkey] = {
            "hotkey": hotkey,
            "action_text": action_text,
            "language_memory": language_memory,
            "color": parsed_color.name(),
        }
    return definitions


def validate_subtask_segments(segments, frame_count=None):
    """返回排序后的规范标注，并拒绝越界、空文本及重叠区间。"""
    normalized = []
    for raw_segment in segments or []:
        if not isinstance(raw_segment, dict):
            raise RuntimeError("Subtask action_config 中的每一项都必须是字典。")
        start = int(raw_segment["start_frame"])
        end = int(raw_segment["end_frame"])
        action_text = str(raw_segment.get("action_text", "")).strip()
        if start < 0 or end <= start:
            raise RuntimeError(f"Subtask 区间无效：[{start}, {end})")
        if frame_count is not None and end > int(frame_count):
            raise RuntimeError(
                f"Subtask 区间 [{start}, {end}) 超出 Episode 帧数 {frame_count}。"
            )
        if not action_text:
            raise RuntimeError(f"Subtask 区间 [{start}, {end}) 的 action_text 为空。")

        hotkey = str(raw_segment.get("hotkey", "")).strip()
        color = str(raw_segment.get("color", "")).strip()
        if color and not QColor(color).isValid():
            raise RuntimeError(f"Subtask 区间 [{start}, {end}) 的颜色无效：{color!r}")
        segment = {
            "start_frame": start,
            "end_frame": end,
            "action_text": action_text,
            "language_memory": str(raw_segment.get("language_memory", "")).strip(),
        }
        if hotkey:
            segment["hotkey"] = hotkey
        if color:
            segment["color"] = QColor(color).name()
        normalized.append(segment)

    normalized.sort(key=lambda item: (item["start_frame"], item["end_frame"]))
    for previous, current in zip(normalized, normalized[1:]):
        if current["start_frame"] < previous["end_frame"]:
            raise RuntimeError(
                "Subtask 区间不能重叠："
                f"[{previous['start_frame']}, {previous['end_frame']}) 与 "
                f"[{current['start_frame']}, {current['end_frame']})"
            )
    return normalized


def get_episode_subtask_segments(json_obj, frame_count=None):
    detailed_task = json_obj.get(DETAILED_TASK_KEY, {})
    if detailed_task in (None, ""):
        return []
    if not isinstance(detailed_task, dict):
        raise RuntimeError(f"data.json 的 {DETAILED_TASK_KEY} 必须是字典。")
    return validate_subtask_segments(
        detailed_task.get(ACTION_CONFIG_KEY, []), frame_count=frame_count
    )


def set_episode_subtask_segments(json_obj, segments):
    normalized = validate_subtask_segments(segments)
    detailed_task = json_obj.get(DETAILED_TASK_KEY)
    if not isinstance(detailed_task, dict):
        detailed_task = {}
    detailed_task["schema_version"] = 1
    detailed_task[ACTION_CONFIG_KEY] = normalized
    json_obj[DETAILED_TASK_KEY] = detailed_task
    return normalized


def remap_subtask_segments(segments, kept_old_frame_positions):
    """将旧 episode 帧位置上的标注映射到筛选并重编号后的新 episode。"""
    kept_old_frame_positions = [int(position) for position in kept_old_frame_positions]
    remapped = []
    for segment in validate_subtask_segments(segments):
        matching_new_positions = [
            new_position
            for new_position, old_position in enumerate(kept_old_frame_positions)
            if segment["start_frame"] <= old_position < segment["end_frame"]
        ]
        if not matching_new_positions:
            continue

        run_start = matching_new_positions[0]
        run_end = run_start + 1
        for new_position in matching_new_positions[1:]:
            if new_position == run_end:
                run_end += 1
                continue
            remapped_segment = copy.deepcopy(segment)
            remapped_segment["start_frame"] = run_start
            remapped_segment["end_frame"] = run_end
            remapped.append(remapped_segment)
            run_start = new_position
            run_end = new_position + 1
        remapped_segment = copy.deepcopy(segment)
        remapped_segment["start_frame"] = run_start
        remapped_segment["end_frame"] = run_end
        remapped.append(remapped_segment)
    return validate_subtask_segments(remapped, frame_count=len(kept_old_frame_positions))


def write_json_atomically(path, payload):
    """同目录写临时文件后原子替换，避免标注过程中损坏 data.json。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise


class RightPalmEeProjector:
    """从 G1-23 右臂关节角计算掌心 EE，并投影到 D435i 彩色图像。"""

    RIGHT_ARM_JOINT_NAMES = (
        "right_shoulder_pitch_joint",
        "right_shoulder_roll_joint",
        "right_shoulder_yaw_joint",
        "right_elbow_joint",
        "right_wrist_roll_joint",
    )
    PALM_OFFSET_IN_WRIST = np.array(
        [0.12397328325, -0.000817559725, -0.008988775685],
        dtype=np.float64,
    )
    AXIS_LENGTH_METERS = 0.08
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_MATRIX = np.array(
        [
            [605.5006103515625, 0.0, 326.1470031738281],
            [0.0, 605.41357421875, 249.57150268554688],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    # URDF d435_link: X前、Y左、Z上；OpenCV optical: X右、Y下、Z前。
    R_OPTICAL_FROM_D435_LINK = np.array(
        [
            [0.0, -1.0, 0.0],
            [0.0, 0.0, -1.0],
            [1.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )

    def __init__(self, urdf_path=G1_23_URDF_PATH):
        self.urdf_path = Path(urdf_path)
        if not self.urdf_path.is_file():
            raise FileNotFoundError(f"G1-23 URDF 不存在：{self.urdf_path}")

        self.model = pin.buildModelFromUrdf(str(self.urdf_path))
        self.data = self.model.createData()
        self.wrist_joint_id = self._joint_id("right_wrist_roll_joint")
        self.waist_q_index = self._joint_q_index("waist_yaw_joint")
        self.right_arm_q_indices = np.asarray(
            [self._joint_q_index(name) for name in self.RIGHT_ARM_JOINT_NAMES],
            dtype=np.int64,
        )
        self.d435_frame_id = self.model.getFrameId("d435_link")
        if self.d435_frame_id >= len(self.model.frames):
            raise RuntimeError("G1-23 URDF 中找不到 d435_link。")

        palm = self.PALM_OFFSET_IN_WRIST
        axis_length = self.AXIS_LENGTH_METERS
        self.points_in_wrist = np.array(
            [
                palm,
                palm + np.array([axis_length, 0.0, 0.0]),
                palm + np.array([0.0, axis_length, 0.0]),
                palm + np.array([0.0, 0.0, axis_length]),
            ],
            dtype=np.float64,
        )

    def _joint_id(self, joint_name):
        joint_id = self.model.getJointId(joint_name)
        if joint_id == 0:
            raise RuntimeError(f"G1-23 URDF 中找不到关节：{joint_name}")
        return joint_id

    def _joint_q_index(self, joint_name):
        joint_id = self._joint_id(joint_name)
        return int(self.model.joints[joint_id].idx_q)

    def compute_frame_geometry(self, frame_record):
        """计算掌心和相机在固定 pelvis/world 坐标系中的位姿。"""
        frame_id = frame_record.get("idx", "unknown")
        states = frame_record.get("states")
        if not isinstance(states, dict):
            raise RuntimeError(f"帧 {frame_id} 缺少 states。")

        right_arm_q = np.asarray(
            states.get("right_arm", {}).get("qpos", []),
            dtype=np.float64,
        )
        body_q = np.asarray(
            states.get("body", {}).get("qpos", []),
            dtype=np.float64,
        )
        if right_arm_q.shape != (5,):
            raise RuntimeError(
                f"帧 {frame_id} 的 states.right_arm.qpos 应为 5 维，实际为 {right_arm_q.shape}。"
            )
        if body_q.size < 1:
            raise RuntimeError(f"帧 {frame_id} 的 states.body.qpos 缺少 waist_yaw。")

        q = np.zeros(self.model.nq, dtype=np.float64)
        q[self.right_arm_q_indices] = right_arm_q
        q[self.waist_q_index] = float(body_q[0])
        pin.forwardKinematics(self.model, self.data, q)
        pin.updateFramePlacements(self.model, self.data)

        t_pelvis_wrist = self.data.oMi[self.wrist_joint_id]
        t_pelvis_d435 = self.data.oMf[self.d435_frame_id]
        points_in_pelvis = (
            t_pelvis_wrist.rotation @ self.points_in_wrist.T
        ).T + t_pelvis_wrist.translation
        return {
            "points_in_world": np.asarray(points_in_pelvis, dtype=np.float64).copy(),
            "camera_rotation_in_world": np.asarray(
                t_pelvis_d435.rotation, dtype=np.float64
            ).copy(),
            "camera_translation_in_world": np.asarray(
                t_pelvis_d435.translation, dtype=np.float64
            ).copy(),
            "right_arm_q": right_arm_q.copy(),
            "waist_yaw": float(body_q[0]),
        }

    def project_world_points(
        self,
        points_in_world,
        camera_geometry,
        require_all_in_front=True,
    ):
        """使用同一个当前相机外参，将 world 点批量投影到当前图像。"""
        points_in_world = np.asarray(points_in_world, dtype=np.float64)
        if points_in_world.ndim != 2 or points_in_world.shape[1] != 3:
            raise ValueError("points_in_world 应为 N×3 数组。")

        camera_rotation_in_world = camera_geometry["camera_rotation_in_world"]
        camera_translation_in_world = camera_geometry["camera_translation_in_world"]
        points_in_d435 = (
            camera_rotation_in_world.T
            @ (points_in_world - camera_translation_in_world).T
        ).T
        points_in_optical = (
            self.R_OPTICAL_FROM_D435_LINK @ points_in_d435.T
        ).T

        valid = points_in_optical[:, 2] > 0.0
        if require_all_in_front and not np.all(valid):
            raise RuntimeError("右手掌心轨迹点或坐标轴端点位于当前相机后方。")

        pixels = np.full((len(points_in_optical), 2), np.nan, dtype=np.float64)
        normalized_xy = points_in_optical[valid, :2] / points_in_optical[valid, 2:3]
        pixels[valid, 0] = (
            self.CAMERA_MATRIX[0, 0] * normalized_xy[:, 0]
            + self.CAMERA_MATRIX[0, 2]
        )
        pixels[valid, 1] = (
            self.CAMERA_MATRIX[1, 1] * normalized_xy[:, 1]
            + self.CAMERA_MATRIX[1, 2]
        )
        return {
            "pixels": pixels,
            "points_in_optical": points_in_optical,
            "valid": valid,
        }

    def project_geometry(self, geometry):
        """将一帧的掌心原点和 XYZ 轴投影到该帧自己的相机。"""
        projection = self.project_world_points(
            geometry["points_in_world"],
            geometry,
            require_all_in_front=True,
        )
        projection.update(
            {
                "points_in_world": geometry["points_in_world"],
                "right_arm_q": geometry["right_arm_q"],
                "waist_yaw": geometry["waist_yaw"],
            }
        )
        return projection

    def project_frame(self, frame_record):
        """返回当前掌心原点与局部 XYZ 轴端点的投影。"""
        return self.project_geometry(self.compute_frame_geometry(frame_record))


def _draw_arrow(painter, start, end, color):
    """在原始分辨率的 QPixmap 上绘制带箭头的坐标轴。"""
    start_point = QPointF(float(start[0]), float(start[1]))
    end_point = QPointF(float(end[0]), float(end[1]))
    painter.setPen(QPen(color, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(start_point, end_point)

    angle = math.atan2(end_point.y() - start_point.y(), end_point.x() - start_point.x())
    arrow_size = 12.0
    arrow_left = QPointF(
        end_point.x() - arrow_size * math.cos(angle - math.pi / 6),
        end_point.y() - arrow_size * math.sin(angle - math.pi / 6),
    )
    arrow_right = QPointF(
        end_point.x() - arrow_size * math.cos(angle + math.pi / 6),
        end_point.y() - arrow_size * math.sin(angle + math.pi / 6),
    )
    painter.setBrush(QBrush(color))
    painter.drawPolygon(QPolygonF([end_point, arrow_left, arrow_right]))


def trajectory_sample_positions(
    current_index,
    total_frames,
    fps,
    window_seconds=3.0,
    samples_per_second=3,
):
    """返回过去/未来轨迹采样的 (相对秒数, 帧列表位置)。"""
    if total_frames <= 0:
        return []
    if fps <= 0:
        raise ValueError(f"FPS 必须大于 0，实际为 {fps}。")
    if samples_per_second <= 0:
        raise ValueError("samples_per_second 必须大于 0。")

    sample_count_each_side = int(round(window_seconds * samples_per_second))
    samples = []
    used_positions = set()
    for sample_number in range(-sample_count_each_side, sample_count_each_side + 1):
        if sample_number == 0:
            continue
        relative_seconds = sample_number / samples_per_second
        frame_position = int(round(current_index + relative_seconds * fps))
        if frame_position < 0 or frame_position >= total_frames:
            continue
        if frame_position == current_index or frame_position in used_positions:
            continue
        used_positions.add(frame_position)
        samples.append((relative_seconds, frame_position))
    return samples


def _draw_trajectory(painter, origin, trajectory_samples):
    """绘制过去（橙色）和未来（紫色）掌心轨迹。"""
    if not trajectory_samples:
        return

    past_color = QColor(255, 145, 30, 210)
    future_color = QColor(210, 55, 255, 210)
    origin_point = QPointF(float(origin[0]), float(origin[1]))

    for is_past, color in ((True, past_color), (False, future_color)):
        samples = [
            sample
            for sample in trajectory_samples
            if (sample["relative_seconds"] < 0.0) == is_past
        ]
        samples.sort(key=lambda sample: sample["relative_seconds"])
        if not samples:
            continue

        points = [
            QPointF(float(sample["pixel"][0]), float(sample["pixel"][1]))
            for sample in samples
        ]
        if is_past:
            line_points = points + [origin_point]
        else:
            line_points = [origin_point] + points

        painter.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(QPolygonF(line_points))

        for sample, point in zip(samples, points, strict=True):
            relative_seconds = float(sample["relative_seconds"])
            distance_ratio = min(abs(relative_seconds) / 3.0, 1.0)
            radius = 5.0 if np.isclose(relative_seconds, round(relative_seconds)) else 3.5
            point_color = QColor(color)
            point_color.setAlpha(int(round(230 - 80 * distance_ratio)))
            painter.setPen(QPen(QColor(20, 20, 20, 190), 1.2))
            painter.setBrush(QBrush(point_color))
            painter.drawEllipse(point, radius, radius)

def draw_right_palm_eepose(pixmap, projection, trajectory_samples=None):
    """复制原图，并叠加右手掌心 EE 原点、XYZ 三轴和相机坐标。"""
    if pixmap.width() != RightPalmEeProjector.CAMERA_WIDTH or pixmap.height() != RightPalmEeProjector.CAMERA_HEIGHT:
        raise RuntimeError(
            "EE 投影仅标定于 640x480 图像，"
            f"当前图像为 {pixmap.width()}x{pixmap.height()}。"
        )

    annotated = pixmap.copy()
    painter = QPainter(annotated)
    painter.setRenderHint(QPainter.Antialiasing, True)
    pixels = projection["pixels"]
    origin = pixels[0]
    _draw_trajectory(painter, origin, trajectory_samples or [])
    axis_specs = (
        ("X", QColor(255, 40, 40)),
        ("Y", QColor(30, 210, 30)),
        ("Z", QColor(40, 80, 255)),
    )

    for axis_index, (axis_name, color) in enumerate(axis_specs, start=1):
        endpoint = pixels[axis_index]
        _draw_arrow(painter, origin, endpoint, color)
        painter.setPen(QPen(color, 2))
        painter.drawText(
            QPointF(float(endpoint[0]) + 4.0, float(endpoint[1]) - 4.0),
            axis_name,
        )

    origin_point = QPointF(float(origin[0]), float(origin[1]))
    painter.setPen(QPen(QColor(255, 255, 255), 3))
    painter.setBrush(QBrush(QColor(0, 255, 255)))
    painter.drawEllipse(origin_point, 8.0, 8.0)
    painter.setPen(QPen(QColor(255, 255, 0), 2))
    painter.drawText(
        QPointF(float(origin[0]) + 12.0, float(origin[1]) - 10.0),
        "Right palm EE",
    )
    optical_xyz = projection["points_in_optical"][0]
    painter.drawText(
        QPointF(12.0, 24.0),
        f"camera xyz: [{optical_xyz[0]:.3f}, {optical_xyz[1]:.3f}, {optical_xyz[2]:.3f}] m",
    )
    painter.setPen(QPen(QColor(255, 145, 30), 2))
    painter.drawText(QPointF(12.0, 47.0), "past 3s: orange")
    painter.setPen(QPen(QColor(210, 55, 255), 2))
    painter.drawText(QPointF(165.0, 47.0), "future 3s: purple | 3 points/s")
    painter.end()
    return annotated


def _renumber_media_path(relative_path, old_idx, new_idx):
    """在不改变目录、前后缀和扩展名的情况下替换媒体文件中的帧编号。"""
    normalized_path = relative_path.replace("\\", "/")
    directory, filename = os.path.split(normalized_path)
    frame_pattern = re.compile(rf"(?<!\d)0*{old_idx}(?!\d)")
    new_filename, count = frame_pattern.subn(f"{new_idx:06d}", filename, count=1)

    if count != 1:
        raise RuntimeError(
            f"无法在媒体文件名中识别帧编号 {old_idx}：{relative_path}"
        )

    if directory:
        return f"{directory}/{new_filename}"
    return new_filename


def _resolve_episode_media_path(episode_dir, relative_path):
    """解析并校验帧媒体路径，禁止路径逃逸到 episode 目录之外。"""
    episode_realpath = os.path.realpath(episode_dir)
    media_realpath = os.path.realpath(os.path.join(episode_dir, relative_path))

    try:
        inside_episode = os.path.commonpath([episode_realpath, media_realpath]) == episode_realpath
    except ValueError:
        inside_episode = False

    if not inside_episode:
        raise RuntimeError(f"媒体路径超出 Episode 目录：{relative_path}")

    return media_realpath


def export_episode_frames(source_episode_dir, destination_episode_dir, frame_ids):
    """
    将指定帧导出为一个独立 Episode。

    每条 data.json 帧记录会被完整深拷贝，所以 states、actions、关节角以及
    其他帧级字段都会保留；colors、depths、audios 中引用的文件会同步复制并
    从 0 开始重编号。写入使用临时目录，全部成功后才生成目标 Episode。
    """
    source_episode_dir = os.path.abspath(source_episode_dir)
    destination_episode_dir = os.path.abspath(destination_episode_dir)
    source_json_path = os.path.join(source_episode_dir, "data.json")

    if not os.path.isdir(source_episode_dir):
        raise RuntimeError(f"源 Episode 目录不存在：{source_episode_dir}")
    if not os.path.isfile(source_json_path):
        raise RuntimeError(f"data.json 不存在：{source_json_path}")
    if os.path.exists(destination_episode_dir):
        raise RuntimeError(f"目标 Episode 已存在：{destination_episode_dir}")

    selected_frame_ids = list(dict.fromkeys(int(frame_id) for frame_id in frame_ids))
    if not selected_frame_ids:
        raise RuntimeError("没有选择任何要导出的帧。")

    with open(source_json_path, "r", encoding="utf-8") as f:
        json_obj = json.load(f)

    if "data" not in json_obj or not isinstance(json_obj["data"], list):
        raise RuntimeError("data.json 格式不正确：缺少 data 数组。")

    data_by_idx = {}
    ordered_frame_ids = []
    for item in json_obj["data"]:
        if not isinstance(item, dict) or "idx" not in item:
            continue
        old_idx = int(item["idx"])
        if old_idx in data_by_idx:
            raise RuntimeError(f"data.json 中存在重复帧 idx：{old_idx}")
        data_by_idx[old_idx] = item
        ordered_frame_ids.append(old_idx)

    missing_frame_ids = [frame_id for frame_id in selected_frame_ids if frame_id not in data_by_idx]
    if missing_frame_ids:
        preview = ", ".join(str(frame_id) for frame_id in missing_frame_ids[:10])
        raise RuntimeError(f"data.json 缺少选中帧：{preview}")

    destination_parent = os.path.dirname(destination_episode_dir)
    os.makedirs(destination_parent, exist_ok=True)
    temp_episode_dir = tempfile.mkdtemp(
        prefix=f".{os.path.basename(destination_episode_dir)}.exporting-",
        dir=destination_parent,
    )

    try:
        new_data_list = []
        copied_destinations = {}

        for new_idx, old_idx in enumerate(selected_frame_ids):
            new_item = copy.deepcopy(data_by_idx[old_idx])
            new_item["idx"] = new_idx

            for media_field in MEDIA_FIELDS:
                media_refs = new_item.get(media_field)
                if media_refs is None:
                    continue
                if not isinstance(media_refs, dict):
                    raise RuntimeError(
                        f"帧 {old_idx} 的 {media_field} 字段不是字典，无法安全导出。"
                    )

                new_media_refs = {}
                for media_key, relative_path in media_refs.items():
                    if relative_path in (None, ""):
                        new_media_refs[media_key] = relative_path
                        continue
                    if not isinstance(relative_path, str):
                        raise RuntimeError(
                            f"帧 {old_idx} 的媒体路径不是字符串：{media_field}.{media_key}"
                        )

                    source_media_path = _resolve_episode_media_path(
                        source_episode_dir, relative_path
                    )
                    if not os.path.isfile(source_media_path):
                        raise RuntimeError(f"关联媒体文件不存在：{relative_path}")

                    new_relative_path = _renumber_media_path(relative_path, old_idx, new_idx)
                    destination_media_path = _resolve_episode_media_path(
                        temp_episode_dir, new_relative_path
                    )

                    previous_source = copied_destinations.get(destination_media_path)
                    if previous_source is not None and previous_source != source_media_path:
                        raise RuntimeError(f"导出媒体文件名冲突：{new_relative_path}")

                    if previous_source is None:
                        os.makedirs(os.path.dirname(destination_media_path), exist_ok=True)
                        shutil.copy2(source_media_path, destination_media_path)
                        copied_destinations[destination_media_path] = source_media_path

                    new_media_refs[media_key] = new_relative_path

                new_item[media_field] = new_media_refs

            new_data_list.append(new_item)

        new_json_obj = copy.deepcopy(json_obj)
        new_json_obj["data"] = new_data_list
        old_position_by_frame_id = {
            frame_id: position for position, frame_id in enumerate(ordered_frame_ids)
        }
        kept_old_positions = [
            old_position_by_frame_id[frame_id] for frame_id in selected_frame_ids
        ]
        old_segments = get_episode_subtask_segments(
            json_obj, frame_count=len(ordered_frame_ids)
        )
        set_episode_subtask_segments(
            new_json_obj,
            remap_subtask_segments(old_segments, kept_old_positions),
        )

        temp_json_path = os.path.join(temp_episode_dir, "data.json")
        with open(temp_json_path, "w", encoding="utf-8") as f:
            json.dump(new_json_obj, f, ensure_ascii=False, indent=4)

        os.rename(temp_episode_dir, destination_episode_dir)
        return len(new_data_list)
    except Exception:
        shutil.rmtree(temp_episode_dir, ignore_errors=True)
        raise


class ImageLabel(QLabel):
    """支持自动缩放显示图片的 QLabel。"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: black;
                color: white;
                border: 1px solid #444;
            }
        """)
        self.setMinimumSize(320, 240)
        self._original_pixmap = None
        self._title = title
        self.set_placeholder(f"{title}\n等待播放")

    def set_placeholder(self, text):
        self._original_pixmap = None
        self.setPixmap(QPixmap())
        self.setText(text)

    def set_pixmap(self, pixmap: QPixmap):
        self._original_pixmap = pixmap
        self.setText("")
        self._update_scaled_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self):
        if self._original_pixmap is not None and not self._original_pixmap.isNull():
            scaled = self._original_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled)
        elif self.text() == "":
            self.setText(f"{self._title}\n无图像")


class RangeSlider(QFrame):
    """
    进度条 + 区间选择条：
    - 左键单击：定位到该帧
    - 左键拖动：实时预览该帧
    - Shift + 左键拖动：选择区间
    """
    rangeChanged = pyqtSignal(int, int)
    frameChanged = pyqtSignal(int)
    sliderPressed = pyqtSignal()
    sliderReleased = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(118)
        self.setStyleSheet("background-color: #f2f2f2; border: 1px solid #bbb;")

        self.total_frames = 0
        self.current_frame = 0

        self.sel_start = 0
        self.sel_end = 0
        self.subtask_segments = []

        self.drag_mode = None   # None / "scrub" / "select"
        self.drag_anchor = 0

    def set_total_frames(self, total_frames):
        self.total_frames = max(0, total_frames)
        if self.total_frames <= 1:
            self.current_frame = 0
            self.sel_start = 0
            self.sel_end = 0
        else:
            max_index = self.total_frames - 1
            self.current_frame = min(self.current_frame, max_index)
            self.sel_start = min(self.sel_start, max_index)
            self.sel_end = min(self.sel_end, max_index)
        self.update()

    def set_current_frame(self, frame_index):
        self.current_frame = max(0, min(frame_index, max(0, self.total_frames - 1)))
        self.update()

    def set_subtask_segments(self, segments):
        self.subtask_segments = [copy.deepcopy(segment) for segment in segments]
        self.update()

    def reset_selection(self):
        if self.total_frames > 0:
            self.sel_start = 0
            self.sel_end = 0
        else:
            self.sel_start = 0
            self.sel_end = 0
        self.rangeChanged.emit(self.sel_start, self.sel_end)
        self.update()

    def set_selected_range(self, start, end):
        """以帧列表位置设置选择区间，与 Shift 拖拽产生相同状态。"""
        if self.total_frames <= 0:
            self.sel_start = 0
            self.sel_end = 0
        else:
            max_index = self.total_frames - 1
            self.sel_start = max(0, min(int(start), max_index))
            self.sel_end = max(0, min(int(end), max_index))
        self.rangeChanged.emit(*self.get_selected_range())
        self.update()

    def get_selected_range(self):
        return min(self.sel_start, self.sel_end), max(self.sel_start, self.sel_end)

    def frame_from_x(self, x):
        if self.total_frames <= 1:
            return 0
        left = 15
        right = self.width() - 15
        width = max(1, right - left)
        x = max(left, min(x, right))
        ratio = (x - left) / width
        frame = int(round(ratio * (self.total_frames - 1)))
        return max(0, min(frame, self.total_frames - 1))

    def x_from_frame(self, frame):
        if self.total_frames <= 1:
            return 15
        left = 15
        right = self.width() - 15
        width = max(1, right - left)
        ratio = frame / (self.total_frames - 1)
        return int(left + ratio * width)

    def x_from_boundary(self, boundary):
        """将半开区间边界 0～total_frames 映射到时间轴像素。"""
        left = 15
        right = self.width() - 15
        width = max(1, right - left)
        if self.total_frames <= 0:
            return left
        ratio = max(0, min(int(boundary), self.total_frames)) / self.total_frames
        return int(round(left + ratio * width))

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or self.total_frames <= 0:
            return

        frame = self.frame_from_x(event.x())
        self.sliderPressed.emit()

        if event.modifiers() & Qt.ShiftModifier:
            self.drag_mode = "select"
            self.drag_anchor = frame
            self.sel_start = frame
            self.sel_end = frame
            self.rangeChanged.emit(*self.get_selected_range())
        else:
            self.drag_mode = "scrub"
            self.current_frame = frame
            self.frameChanged.emit(frame)

        self.update()

    def mouseMoveEvent(self, event):
        if self.drag_mode is None or self.total_frames <= 0:
            return

        frame = self.frame_from_x(event.x())

        if self.drag_mode == "select":
            self.sel_end = frame
            self.rangeChanged.emit(*self.get_selected_range())
        elif self.drag_mode == "scrub":
            self.current_frame = frame
            self.frameChanged.emit(frame)

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self.drag_mode is None:
            return

        frame = self.frame_from_x(event.x())

        if self.drag_mode == "select":
            self.sel_end = frame
            self.rangeChanged.emit(*self.get_selected_range())
        elif self.drag_mode == "scrub":
            self.current_frame = frame
            self.frameChanged.emit(frame)
            self.sliderReleased.emit(frame)

        self.drag_mode = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        left = 15
        right = self.width() - 15
        bar_y = 32
        bar_h = 12
        bar_w = max(1, right - left)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#cccccc"))
        painter.drawRoundedRect(left, bar_y, bar_w, bar_h, 6, 6)

        if self.total_frames > 0:
            start, end = self.get_selected_range()
            x1 = self.x_from_frame(start)
            x2 = self.x_from_frame(end)
            sel_x = min(x1, x2)
            sel_w = max(6, abs(x2 - x1))
            painter.setBrush(QColor("#6fa8dc"))
            painter.drawRoundedRect(sel_x, bar_y, sel_w, bar_h, 6, 6)

        subtask_y = 55
        subtask_h = 18
        painter.setPen(QPen(QColor("#999999"), 1))
        painter.setBrush(QColor("#eeeeee"))
        painter.drawRect(left, subtask_y, bar_w, subtask_h)
        for segment in self.subtask_segments:
            start = max(0, min(int(segment.get("start_frame", 0)), self.total_frames))
            end = max(start, min(int(segment.get("end_frame", start)), self.total_frames))
            if end <= start:
                continue
            x1 = self.x_from_boundary(start)
            x2 = self.x_from_boundary(end)
            color = QColor(str(segment.get("color", "#607D8B")))
            if not color.isValid():
                color = QColor("#607D8B")
            painter.setPen(QPen(color.darker(135), 1))
            painter.setBrush(color)
            painter.drawRect(x1, subtask_y, max(2, x2 - x1), subtask_h)
            hotkey = str(segment.get("hotkey", "")).strip()
            if hotkey and x2 - x1 >= 14:
                foreground = Qt.white if color.lightness() < 150 else Qt.black
                painter.setPen(foreground)
                painter.drawText(QRect(x1, subtask_y, max(2, x2 - x1), subtask_h), Qt.AlignCenter, hotkey)

        if self.total_frames > 0:
            cur_x = self.x_from_frame(self.current_frame)
            painter.setPen(QPen(QColor("red"), 2))
            painter.drawLine(cur_x, 14, cur_x, 78)

        if self.total_frames > 0:
            start, end = self.get_selected_range()
            for frame in [start, end]:
                x = self.x_from_frame(frame)
                painter.setPen(QPen(QColor("#1c4587"), 2))
                painter.setBrush(QBrush(QColor("#ffffff")))
                painter.drawEllipse(x - 5, bar_y - 4, 10, 20)

        painter.setPen(QColor("#222222"))
        top_text = "拖动定位 | A/D逐帧 | Z/C快移10帧 | Q/E设起止帧 | Shift拖动/输入选区"
        painter.drawText(QRect(10, 4, self.width() - 20, 20), Qt.AlignCenter, top_text)

        if self.total_frames > 0:
            start, end = self.get_selected_range()
            bottom_text = (
                f"选择区间: {start} - {end}    "
                f"当前帧: {self.current_frame} / {self.total_frames - 1}"
            )
        else:
            bottom_text = "无可用帧"
        painter.drawText(QRect(10, 84, self.width() - 20, 22), Qt.AlignCenter, bottom_text)


class DatasetPlayer(QWidget):
    """
    数据集回放界面：
    - 可选择 root_dir
    - 左右两侧箭头切换 episode
    - 左侧显示 color_0 原图，右侧显示右手掌心 EE Pose 投影
    - 下方进度条 + 区间选择 + 区间播放 + 裁剪
    - 删除当前episode
    """

    CAMERA_ID = 0
    FILE_PATTERN = re.compile(r"^(\d+)_color_(\d+)\.jpg$", re.IGNORECASE)

    def __init__(self, root_dir, interval_ms=100):
        super().__init__()
        self.root_dir = root_dir
        self.interval_ms = interval_ms

        self.episodes = []
        self.current_episode_index = 0
        self.current_episode_name = ""
        self.frame_keys = []
        self.frames_map = defaultdict(dict)
        self.frame_records_by_idx = {}
        self.episode_json = {}
        self.episode_data_error = ""
        self.episode_fps = 30.0
        self.ee_geometry_cache = {}
        self.ee_projection_cache = {}
        self.current_frame_index = 0
        self.subtask_definitions = {}
        self.subtask_config_path = ""
        self.subtask_segments = []
        self.subtask_anchor_position = None

        self.ee_projector = None
        self.ee_projector_error = ""
        try:
            self.ee_projector = RightPalmEeProjector()
        except Exception as exc:
            self.ee_projector_error = str(exc)

        self.is_playing = True
        self.play_selection_only = False
        self.was_playing_before_drag = False

        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.play_next_frame)
        self.timer.start(self.interval_ms)

        self.reload_dataset_root(self.root_dir, show_message=False)

    def init_ui(self):
        self.setWindowTitle("Unitree数据集编辑器 V1.3 - Subtask标注与右手掌心EE投影")
        self.resize(1550, 1020)

        self.select_root_btn = QPushButton("选择数据集路径")
        self.select_root_btn.clicked.connect(self.select_root_dir)
        self.select_root_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                padding: 10px 18px;
                border-radius: 8px;
                background-color: #2e86de;
                color: white;
            }
            QPushButton:hover:!disabled {
                background-color: #1f6fc1;
            }
        """)

        self.root_dir_label = QLabel("")
        self.root_dir_label.setWordWrap(True)
        self.root_dir_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.root_dir_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #222;
                padding: 8px 12px;
                border: 1px solid #cccccc;
                background: #fafafa;
                border-radius: 6px;
            }
        """)

        root_layout = QHBoxLayout()
        root_layout.addWidget(self.select_root_btn)
        root_layout.addWidget(self.root_dir_label, 1)

        self.select_subtask_yaml_btn = QPushButton("选择 Subtask YAML")
        self.select_subtask_yaml_btn.clicked.connect(self.select_subtask_yaml)
        self.subtask_config_label = QLabel("尚未加载 Subtask YAML")
        self.subtask_config_label.setWordWrap(True)
        self.subtask_config_label.setStyleSheet(
            "font-size: 13px; color: #333; padding: 6px; border: 1px solid #ccc;"
        )
        self.annotation_mode_btn = QPushButton("标注模式：关闭")
        self.annotation_mode_btn.setCheckable(True)
        self.annotation_mode_btn.setEnabled(False)
        self.annotation_mode_btn.toggled.connect(self.on_annotation_mode_toggled)
        self.undo_subtask_btn = QPushButton("撤销上一段")
        self.undo_subtask_btn.clicked.connect(self.undo_last_subtask_segment)
        self.undo_subtask_btn.setEnabled(False)
        self.clear_subtask_btn = QPushButton("清除当前Episode标注")
        self.clear_subtask_btn.clicked.connect(self.clear_current_subtask_segments)
        self.clear_subtask_btn.setEnabled(False)
        self.subtask_legend_label = QLabel("加载 YAML 后，Q 设置标注起点，数字键给前一段贴标签，E 设置终止帧。")
        self.subtask_legend_label.setWordWrap(True)
        self.subtask_legend_label.setStyleSheet("font-size: 13px; padding: 5px;")

        subtask_config_layout = QHBoxLayout()
        subtask_config_layout.addWidget(self.select_subtask_yaml_btn)
        subtask_config_layout.addWidget(self.subtask_config_label, 1)
        subtask_config_layout.addWidget(self.annotation_mode_btn)
        subtask_config_layout.addWidget(self.undo_subtask_btn)
        subtask_config_layout.addWidget(self.clear_subtask_btn)

        self.prev_btn = QPushButton("◀")
        self.next_btn = QPushButton("▶")

        for btn in (self.prev_btn, self.next_btn):
            btn.setFixedWidth(90)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 36px;
                    font-weight: bold;
                    background-color: #2d2d2d;
                    color: white;
                    border-radius: 10px;
                }
                QPushButton:disabled {
                    background-color: #777;
                    color: #bbb;
                }
                QPushButton:hover:!disabled {
                    background-color: #444;
                }
            """)

        self.prev_btn.clicked.connect(self.prev_episode)
        self.next_btn.clicked.connect(self.next_episode)

        self.episode_label = QLabel("当前Episode：")
        self.episode_label.setAlignment(Qt.AlignCenter)
        self.episode_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                padding: 8px;
            }
        """)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #333;
                padding-bottom: 8px;
            }
        """)

        self.raw_camera_label = ImageLabel("color_0 原始图像")
        self.eepose_camera_label = ImageLabel("右手掌心 EE Pose + 前后3秒轨迹")
        self.cam_labels = {
            "raw": self.raw_camera_label,
            "eepose": self.eepose_camera_label,
        }

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(self.raw_camera_label, 0, 0)
        grid.addWidget(self.eepose_camera_label, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.range_slider = RangeSlider()
        self.range_slider.rangeChanged.connect(self.on_range_changed)
        self.range_slider.frameChanged.connect(self.on_slider_frame_changed)
        self.range_slider.sliderPressed.connect(self.on_slider_pressed)
        self.range_slider.sliderReleased.connect(self.on_slider_released)

        self.start_frame_spin = QSpinBox()
        self.end_frame_spin = QSpinBox()
        for spin_box in (self.start_frame_spin, self.end_frame_spin):
            spin_box.setRange(0, 0)
            spin_box.setMinimumWidth(120)
            spin_box.setAlignment(Qt.AlignCenter)
            spin_box.setStyleSheet("font-size: 16px; padding: 5px;")
            spin_box.setEnabled(False)

        self.apply_range_btn = QPushButton("确认区间")
        self.apply_range_btn.clicked.connect(self.apply_manual_range)
        self.apply_range_btn.setEnabled(False)
        self.apply_range_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                padding: 7px 20px;
                border-radius: 6px;
                background-color: #2e86de;
                color: white;
            }
            QPushButton:hover:!disabled {
                background-color: #1f6fc1;
            }
            QPushButton:disabled {
                background-color: #999999;
            }
        """)

        self.prev_frame_btn = QPushButton("◀ 上一帧  A")
        self.next_frame_btn = QPushButton("下一帧  D ▶")
        for button in (self.prev_frame_btn, self.next_frame_btn):
            button.setAutoRepeat(True)
            button.setAutoRepeatDelay(300)
            button.setAutoRepeatInterval(70)
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton {
                    font-size: 15px;
                    font-weight: bold;
                    padding: 7px 16px;
                    border-radius: 6px;
                    background-color: #555555;
                    color: white;
                }
                QPushButton:hover:!disabled {
                    background-color: #333333;
                }
                QPushButton:disabled {
                    background-color: #999999;
                }
            """)
        self.prev_frame_btn.clicked.connect(lambda: self.step_frame(-1))
        self.next_frame_btn.clicked.connect(lambda: self.step_frame(1))

        self.prev_frame_shortcut = QShortcut(QKeySequence("A"), self)
        self.next_frame_shortcut = QShortcut(QKeySequence("D"), self)
        self.prev_frame_shortcut.setAutoRepeat(True)
        self.next_frame_shortcut.setAutoRepeat(True)
        self.prev_frame_shortcut.activated.connect(lambda: self.step_frame(-1))
        self.next_frame_shortcut.activated.connect(lambda: self.step_frame(1))

        self.fast_prev_frame_shortcut = QShortcut(QKeySequence("Z"), self)
        self.fast_next_frame_shortcut = QShortcut(QKeySequence("C"), self)
        self.fast_prev_frame_shortcut.setAutoRepeat(True)
        self.fast_next_frame_shortcut.setAutoRepeat(True)
        self.fast_prev_frame_shortcut.activated.connect(lambda: self.step_frame(-10))
        self.fast_next_frame_shortcut.activated.connect(lambda: self.step_frame(10))

        self.set_start_frame_shortcut = QShortcut(QKeySequence("Q"), self)
        self.set_end_frame_shortcut = QShortcut(QKeySequence("E"), self)
        self.set_start_frame_shortcut.setAutoRepeat(False)
        self.set_end_frame_shortcut.setAutoRepeat(False)
        self.set_start_frame_shortcut.activated.connect(self.mark_annotation_start)
        self.set_end_frame_shortcut.activated.connect(self.mark_annotation_end)

        self.subtask_shortcuts = {}
        for hotkey in map(str, range(1, 10)):
            shortcut = QShortcut(QKeySequence(hotkey), self)
            shortcut.setAutoRepeat(False)
            shortcut.setEnabled(False)
            shortcut.activated.connect(
                lambda selected_hotkey=hotkey: self.annotate_subtask_hotkey(selected_hotkey)
            )
            self.subtask_shortcuts[hotkey] = shortcut

        manual_range_layout = QHBoxLayout()
        manual_range_layout.addStretch()
        manual_range_layout.addWidget(self.prev_frame_btn)
        manual_range_layout.addWidget(self.next_frame_btn)
        manual_range_layout.addSpacing(28)
        manual_range_layout.addWidget(QLabel("开始帧："))
        manual_range_layout.addWidget(self.start_frame_spin)
        manual_range_layout.addSpacing(18)
        manual_range_layout.addWidget(QLabel("截止帧："))
        manual_range_layout.addWidget(self.end_frame_spin)
        manual_range_layout.addSpacing(18)
        manual_range_layout.addWidget(self.apply_range_btn)
        manual_range_layout.addStretch()

        self.range_info_label = QLabel("未选择区间")
        self.range_info_label.setAlignment(Qt.AlignCenter)
        self.range_info_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #333;
                padding-top: 4px;
                padding-bottom: 4px;
            }
        """)

        self.play_pause_btn = QPushButton("暂停")
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)

        self.play_all_btn = QPushButton("整段循环播放")
        self.play_all_btn.clicked.connect(self.set_play_all_mode)

        self.play_selection_btn = QPushButton("仅播放选中区间")
        self.play_selection_btn.clicked.connect(self.set_play_selection_mode)

        self.reset_range_btn = QPushButton("重置区间")
        self.reset_range_btn.clicked.connect(self.reset_trim_range)

        self.trim_btn = QPushButton("裁剪所选区间")
        self.trim_btn.clicked.connect(self.trim_selected_frames)

        self.export_episode_btn = QPushButton("导出所选区间为新Episode")
        self.export_episode_btn.clicked.connect(self.export_selected_frames_as_episode)

        self.delete_episode_btn = QPushButton("删除当前Episode")
        self.delete_episode_btn.clicked.connect(self.delete_current_episode)

        for btn in [
            self.play_pause_btn,
            self.play_all_btn,
            self.play_selection_btn,
            self.reset_range_btn,
            self.trim_btn,
            self.export_episode_btn,
            self.delete_episode_btn
        ]:
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 15px;
                    padding: 10px 18px;
                    border-radius: 8px;
                    background-color: #555555;
                    color: white;
                }
                QPushButton:hover:!disabled {
                    background-color: #444444;
                }
                QPushButton:disabled {
                    background-color: #999999;
                }
            """)

        self.trim_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                padding: 10px 18px;
                border-radius: 8px;
                background-color: #c0392b;
                color: white;
            }
            QPushButton:hover:!disabled {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #999999;
            }
        """)

        self.export_episode_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                padding: 10px 18px;
                border-radius: 8px;
                background-color: #168f5b;
                color: white;
            }
            QPushButton:hover:!disabled {
                background-color: #117a4d;
            }
            QPushButton:disabled {
                background-color: #999999;
            }
        """)
        self.export_episode_btn.setEnabled(False)

        self.delete_episode_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                padding: 10px 18px;
                border-radius: 8px;
                background-color: #8e44ad;
                color: white;
            }
            QPushButton:hover:!disabled {
                background-color: #7d3c98;
            }
            QPushButton:disabled {
                background-color: #999999;
            }
        """)

        control_layout = QHBoxLayout()
        control_layout.addStretch()
        control_layout.addWidget(self.play_pause_btn)
        control_layout.addWidget(self.play_all_btn)
        control_layout.addWidget(self.play_selection_btn)
        control_layout.addWidget(self.reset_range_btn)
        control_layout.addWidget(self.trim_btn)
        control_layout.addWidget(self.export_episode_btn)
        control_layout.addWidget(self.delete_episode_btn)
        control_layout.addStretch()

        center_layout = QVBoxLayout()
        center_layout.addLayout(root_layout)
        center_layout.addLayout(subtask_config_layout)
        center_layout.addWidget(self.subtask_legend_label)
        center_layout.addWidget(self.episode_label)
        center_layout.addWidget(self.info_label)
        center_layout.addLayout(grid)
        center_layout.addSpacing(12)
        center_layout.addWidget(self.range_slider)
        center_layout.addLayout(manual_range_layout)
        center_layout.addWidget(self.range_info_label)
        center_layout.addLayout(control_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.prev_btn)
        main_layout.addLayout(center_layout, 1)
        main_layout.addWidget(self.next_btn)

        self.setLayout(main_layout)

    def update_root_dir_label(self):
        self.root_dir_label.setText(f"当前数据集路径：{self.root_dir}")

    def clear_player_state(self, message="当前无可用数据"):
        self.episodes = []
        self.current_episode_index = 0
        self.current_episode_name = ""
        self.frame_keys = []
        self.frames_map = defaultdict(dict)
        self.frame_records_by_idx = {}
        self.episode_json = {}
        self.episode_data_error = ""
        self.episode_fps = 30.0
        self.ee_geometry_cache = {}
        self.ee_projection_cache = {}
        self.current_frame_index = 0
        self.play_selection_only = False
        self.subtask_segments = []
        self.subtask_anchor_position = None

        self.episode_label.setText("当前数据集：无")
        self.info_label.setText(message)

        for label in self.cam_labels.values():
            label.set_placeholder(f"{label._title}\n无图像")

        self.range_slider.set_total_frames(0)
        self.range_slider.set_subtask_segments([])
        self.configure_manual_range_inputs(0)
        self.range_info_label.setText(message)
        self.trim_btn.setEnabled(False)
        self.export_episode_btn.setEnabled(False)
        self.delete_episode_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.refresh_subtask_timeline()

    def find_episodes(self):
        episode_dirs = []
        if not os.path.isdir(self.root_dir):
            return episode_dirs

        for name in os.listdir(self.root_dir):
            full_path = os.path.join(self.root_dir, name)
            if os.path.isdir(full_path) and re.match(r"^episode_(\d+)$", name):
                episode_dirs.append(name)

        episode_dirs.sort(key=lambda x: int(re.match(r"^episode_(\d+)$", x).group(1)))
        return episode_dirs

    def reload_dataset_root(self, new_root_dir, show_message=True):
        if not new_root_dir or not os.path.isdir(new_root_dir):
            return

        self.is_playing = False
        self.update_play_button_text()

        self.root_dir = new_root_dir
        self.update_root_dir_label()

        self.episodes = self.find_episodes()

        if not self.episodes:
            self.clear_player_state("当前路径下未找到 episode_0001 / episode_0002 ...")
            if show_message:
                QMessageBox.warning(
                    self,
                    "提示",
                    f"所选目录下未找到 episode_XXXX 数据集目录：\n{self.root_dir}"
                )
            return

        self.current_episode_index = 0
        self.load_episode(self.current_episode_index)
        self.is_playing = True
        self.update_play_button_text()
        self.update_range_info()

        if show_message:
            QMessageBox.information(
                self,
                "完成",
                f"已切换数据集路径：\n{self.root_dir}"
            )

    def select_root_dir(self):
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "选择数据集根目录",
            self.root_dir if os.path.isdir(self.root_dir) else os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if selected_dir:
            self.reload_dataset_root(selected_dir, show_message=False)

    def select_subtask_yaml(self):
        start_dir = (
            os.path.dirname(self.subtask_config_path)
            if self.subtask_config_path
            else (self.root_dir if os.path.isdir(self.root_dir) else os.path.expanduser("~"))
        )
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Subtask YAML",
            start_dir,
            "YAML 文件 (*.yaml *.yml);;所有文件 (*)",
        )
        if not selected_path:
            return
        try:
            self.load_subtask_config(selected_path)
        except Exception as exc:
            QMessageBox.critical(self, "Subtask YAML 错误", str(exc))

    def load_subtask_config(self, config_path):
        definitions = load_subtask_yaml(config_path)
        self.subtask_definitions = definitions
        self.subtask_config_path = str(Path(config_path).expanduser().resolve())
        self.subtask_config_label.setText(f"当前配置：{self.subtask_config_path}")
        self.annotation_mode_btn.setEnabled(True)
        self.annotation_mode_btn.setChecked(True)
        self.update_subtask_legend()

    def on_annotation_mode_toggled(self, enabled):
        enabled = bool(enabled) and bool(self.subtask_definitions)
        self.annotation_mode_btn.setText(f"标注模式：{'开启' if enabled else '关闭'}")
        for hotkey, shortcut in self.subtask_shortcuts.items():
            shortcut.setEnabled(enabled and hotkey in self.subtask_definitions)
        self.update_subtask_legend()

    def update_subtask_legend(self):
        if not self.subtask_definitions:
            self.subtask_legend_label.setText(
                "加载 YAML 后，Q 设置标注起点，数字键给前一段贴标签，E 设置终止帧。"
            )
            return
        entries = []
        for hotkey in sorted(self.subtask_definitions, key=int):
            definition = self.subtask_definitions[hotkey]
            entries.append(f"{hotkey}={definition['action_text']}")
        anchor_text = (
            "未设置标注起点"
            if self.subtask_anchor_position is None
            else f"下一段起点={self.subtask_anchor_position}"
        )
        self.subtask_legend_label.setText(
            "    ".join(entries)
            + f"\n{anchor_text}；数字键标注 [起点, 当前帧]，E 后未覆盖尾段保持未标注。"
        )

    def segments_for_display(self):
        display_segments = []
        for index, segment in enumerate(self.subtask_segments):
            item = copy.deepcopy(segment)
            hotkey = str(item.get("hotkey", "")).strip()
            definition = self.subtask_definitions.get(hotkey, {})
            if not item.get("color"):
                item["color"] = definition.get(
                    "color", SUBTASK_DEFAULT_COLORS[index % len(SUBTASK_DEFAULT_COLORS)]
                )
            display_segments.append(item)
        return display_segments

    def refresh_subtask_timeline(self):
        self.range_slider.set_subtask_segments(self.segments_for_display())
        self.undo_subtask_btn.setEnabled(bool(self.subtask_segments))
        self.clear_subtask_btn.setEnabled(bool(self.subtask_segments))
        self.update_subtask_legend()

    def save_current_subtask_segments(self):
        if not self.current_episode_name or not self.episode_json:
            raise RuntimeError("当前没有可写入标注的 Episode。")
        if self.episode_data_error:
            raise RuntimeError(self.episode_data_error)
        updated_json = copy.deepcopy(self.episode_json)
        normalized = set_episode_subtask_segments(
            updated_json,
            validate_subtask_segments(self.subtask_segments, frame_count=len(self.frame_keys)),
        )
        json_path = Path(self.root_dir) / self.current_episode_name / "data.json"
        write_json_atomically(json_path, updated_json)
        self.episode_json = updated_json
        self.subtask_segments = normalized
        self.refresh_subtask_timeline()

    def mark_annotation_start(self):
        self.set_current_as_range_boundary(is_start=True)
        if not self.frame_keys:
            return
        self.subtask_anchor_position = self.range_slider.current_frame
        self.update_subtask_legend()

    def mark_annotation_end(self):
        self.set_current_as_range_boundary(is_start=False)
        self.update_subtask_legend()

    def annotate_subtask_hotkey(self, hotkey):
        if not self.annotation_mode_btn.isChecked():
            return
        definition = self.subtask_definitions.get(str(hotkey))
        if definition is None:
            QMessageBox.warning(self, "未定义热键", f"当前 YAML 没有定义按键 {hotkey}。")
            return
        if not self.frame_keys:
            QMessageBox.warning(self, "无法标注", "当前 Episode 没有可标注帧。")
            return
        if self.episode_data_error:
            QMessageBox.warning(self, "无法标注", self.episode_data_error)
            return
        if self.subtask_anchor_position is None:
            QMessageBox.warning(self, "尚未设置起点", "请先在起始帧按 Q。")
            return

        current_position = self.range_slider.current_frame
        if current_position < self.subtask_anchor_position:
            QMessageBox.warning(
                self,
                "标注顺序错误",
                f"当前帧 {current_position} 早于下一段起点 {self.subtask_anchor_position}。",
            )
            return
        segment = {
            "start_frame": self.subtask_anchor_position,
            "end_frame": current_position + 1,
            "hotkey": str(hotkey),
            "action_text": definition["action_text"],
            "language_memory": definition["language_memory"],
            "color": definition["color"],
        }
        previous_segments = copy.deepcopy(self.subtask_segments)
        candidate = [*previous_segments, segment]
        try:
            self.subtask_segments = validate_subtask_segments(
                candidate, frame_count=len(self.frame_keys)
            )
            self.save_current_subtask_segments()
        except Exception as exc:
            QMessageBox.critical(self, "Subtask 标注失败", str(exc))
            self.subtask_segments = previous_segments
            self.refresh_subtask_timeline()
            return

        selection_start, _ = self.range_slider.get_selected_range()
        self.range_slider.set_selected_range(selection_start, current_position)
        self.subtask_anchor_position = current_position + 1
        self.update_subtask_legend()

    def undo_last_subtask_segment(self):
        if not self.subtask_segments:
            return
        removed = self.subtask_segments.pop()
        try:
            self.save_current_subtask_segments()
        except Exception as exc:
            self.subtask_segments.append(removed)
            QMessageBox.critical(self, "撤销失败", str(exc))
            return
        self.subtask_anchor_position = int(removed["start_frame"])
        self.update_subtask_legend()

    def clear_current_subtask_segments(self):
        if not self.subtask_segments:
            return
        reply = QMessageBox.question(
            self,
            "确认清除 Subtask",
            f"将清除 {self.current_episode_name} 的全部 {len(self.subtask_segments)} 段标注，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        previous = self.subtask_segments
        self.subtask_segments = []
        try:
            self.save_current_subtask_segments()
        except Exception as exc:
            self.subtask_segments = previous
            QMessageBox.critical(self, "清除失败", str(exc))
            return
        self.subtask_anchor_position = None
        self.update_subtask_legend()

    def update_nav_buttons(self):
        if not self.episodes:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        self.prev_btn.setEnabled(self.current_episode_index > 0)
        self.next_btn.setEnabled(self.current_episode_index < len(self.episodes) - 1)

    def update_play_button_text(self):
        self.play_pause_btn.setText("暂停" if self.is_playing else "开始")

    def update_range_info(self):
        if not self.frame_keys:
            self.range_info_label.setText("当前无可用帧")
            return

        start, end = self.range_slider.get_selected_range()
        mode_text = "仅播放选中区间" if self.play_selection_only else "整段循环播放"
        state_text = "播放中" if self.is_playing else "已暂停"
        self.range_info_label.setText(
            f"当前模式：{mode_text}    状态：{state_text}    选择区间：帧 {start} ~ 帧 {end}"
        )

    def on_range_changed(self, start, end):
        self.start_frame_spin.setValue(start)
        self.end_frame_spin.setValue(end)
        has_valid_range = len(self.frame_keys) > 0 and end >= start
        self.trim_btn.setEnabled(has_valid_range)
        self.export_episode_btn.setEnabled(has_valid_range)
        self.update_range_info()

    def configure_manual_range_inputs(self, total_frames):
        """根据当前 episode 帧数配置手动区间输入框。"""
        has_frames = total_frames > 0
        max_index = max(0, total_frames - 1)
        for spin_box in (self.start_frame_spin, self.end_frame_spin):
            spin_box.setRange(0, max_index)
            spin_box.setEnabled(has_frames)
        self.apply_range_btn.setEnabled(has_frames)
        if not has_frames:
            self.start_frame_spin.setValue(0)
            self.end_frame_spin.setValue(0)
        self.update_frame_step_buttons()

    def update_frame_step_buttons(self):
        """根据当前光标位置更新逐帧按钮的边界状态。"""
        has_frames = bool(self.frame_keys)
        current_frame = self.range_slider.current_frame
        self.prev_frame_btn.setEnabled(has_frames and current_frame > 0)
        self.next_frame_btn.setEnabled(
            has_frames and current_frame < len(self.frame_keys) - 1
        )

    def step_frame(self, direction):
        """暂停播放并按指定帧数移动；用于逐帧和快速移动快捷键。"""
        if not self.frame_keys or direction == 0:
            return
        current_frame = self.range_slider.current_frame
        target_frame = max(
            0,
            min(current_frame + int(direction), len(self.frame_keys) - 1),
        )
        self.is_playing = False
        self.current_frame_index = target_frame
        self.show_frame(target_frame)
        self.update_play_button_text()
        self.update_range_info()

    def set_current_as_range_boundary(self, is_start):
        """用当前光标设置选择区间的开始帧或截止帧。"""
        if not self.frame_keys:
            return
        current_frame = self.range_slider.current_frame
        start, end = self.range_slider.get_selected_range()
        if is_start:
            start = current_frame
            if start > end:
                end = start
        else:
            end = current_frame
            if end < start:
                start = end
        self.range_slider.set_selected_range(start, end)

    def apply_manual_range(self):
        """将输入框中的起止帧应用为裁剪/播放选择区间。"""
        if not self.frame_keys:
            return
        start = self.start_frame_spin.value()
        end = self.end_frame_spin.value()
        if start > end:
            QMessageBox.warning(self, "区间无效", "开始帧不能大于截止帧。")
            return
        self.range_slider.set_selected_range(start, end)

    def on_slider_pressed(self):
        self.was_playing_before_drag = self.is_playing
        self.is_playing = False
        self.update_play_button_text()
        self.update_range_info()

    def on_slider_released(self, frame_index):
        self.current_frame_index = frame_index
        if self.was_playing_before_drag:
            self.is_playing = True
        self.update_play_button_text()
        self.update_range_info()

    def on_slider_frame_changed(self, frame_index):
        if not self.frame_keys:
            return
        self.current_frame_index = max(0, min(frame_index, len(self.frame_keys) - 1))
        self.show_frame(self.current_frame_index)

    def toggle_play_pause(self):
        if not self.frame_keys:
            return
        self.is_playing = not self.is_playing
        self.update_play_button_text()
        self.update_range_info()

    def set_play_all_mode(self):
        self.play_selection_only = False
        self.update_range_info()

    def set_play_selection_mode(self):
        if not self.frame_keys:
            return

        start, end = self.range_slider.get_selected_range()
        if start == end:
            QMessageBox.information(
                self,
                "提示",
                "当前选中区间只有 1 帧，也可以播放；如果你想播放一段范围，请按住 Shift 在进度条上拖动选择区间。"
            )

        self.play_selection_only = True
        self.current_frame_index = start
        self.show_frame(self.current_frame_index)
        self.update_range_info()

    def reset_trim_range(self):
        self.range_slider.reset_selection()
        self.update_range_info()

    def load_episode(self, episode_index):
        if not self.episodes:
            self.clear_player_state("当前无可用数据集")
            return

        self.current_episode_index = episode_index
        self.current_episode_name = self.episodes[episode_index]
        episode_dir = os.path.join(self.root_dir, self.current_episode_name)
        colors_dir = os.path.join(episode_dir, "colors")
        json_path = os.path.join(episode_dir, "data.json")
        self.frame_records_by_idx = {}
        self.episode_json = {}
        self.episode_data_error = ""
        self.episode_fps = 30.0
        self.ee_geometry_cache = {}
        self.ee_projection_cache = {}
        self.subtask_segments = []
        self.subtask_anchor_position = None

        try:
            if not os.path.isfile(json_path):
                raise RuntimeError(f"data.json 不存在：{json_path}")
            with open(json_path, "r", encoding="utf-8") as f:
                json_obj = json.load(f)
            self.episode_json = json_obj
            frame_records = json_obj.get("data")
            if not isinstance(frame_records, list):
                raise RuntimeError("data.json 格式不正确：缺少 data 数组。")
            episode_fps = json_obj.get("info", {}).get("image", {}).get("fps", 30.0)
            self.episode_fps = float(episode_fps)
            if not math.isfinite(self.episode_fps) or self.episode_fps <= 0.0:
                raise RuntimeError(f"data.json 中的 FPS 无效：{episode_fps}")
            for frame_record in frame_records:
                if not isinstance(frame_record, dict) or "idx" not in frame_record:
                    continue
                frame_id = int(frame_record["idx"])
                if frame_id in self.frame_records_by_idx:
                    raise RuntimeError(f"data.json 中存在重复帧 idx：{frame_id}")
                self.frame_records_by_idx[frame_id] = frame_record
            self.subtask_segments = get_episode_subtask_segments(
                json_obj, frame_count=len(frame_records)
            )
        except Exception as exc:
            self.frame_records_by_idx = {}
            self.episode_json = {}
            self.subtask_segments = []
            self.episode_data_error = str(exc)

        if not os.path.isdir(colors_dir):
            self.frames_map = defaultdict(dict)
            self.frame_keys = []
            self.current_frame_index = 0
            self.episode_label.setText(f"当前Episode：{self.current_episode_name}")
            self.info_label.setText(f"未找到目录：{colors_dir}")
            for label in self.cam_labels.values():
                label.set_placeholder(f"{label._title}\n未找到 colors 目录")
            self.range_slider.set_total_frames(0)
            self.range_slider.set_subtask_segments([])
            self.configure_manual_range_inputs(0)
            self.range_info_label.setText("未找到 colors 目录")
            self.trim_btn.setEnabled(False)
            self.export_episode_btn.setEnabled(False)
            self.delete_episode_btn.setEnabled(True)
            self.update_nav_buttons()
            return

        frames_map = defaultdict(dict)

        for filename in os.listdir(colors_dir):
            match = self.FILE_PATTERN.match(filename)
            if not match:
                continue

            frame_id = int(match.group(1))
            cam_id = int(match.group(2))

            if cam_id != self.CAMERA_ID:
                continue

            full_path = os.path.join(colors_dir, filename)
            frames_map[frame_id][cam_id] = full_path

        frame_keys = sorted(frames_map.keys())

        json_frame_keys = list(self.frame_records_by_idx)
        if json_frame_keys and json_frame_keys != frame_keys:
            self.episode_data_error = (
                "Subtask 标注要求 data.json 的帧顺序与 color_0 图像帧完全一致；"
                f"当前 data.json={len(json_frame_keys)} 帧，color_0={len(frame_keys)} 帧，"
                "或二者帧号顺序不同。请先修复数据一致性。"
            )
            self.subtask_segments = []

        self.frames_map = frames_map
        self.frame_keys = frame_keys
        self.current_frame_index = 0
        self.play_selection_only = False

        self.episode_label.setText(f"当前Episode：{self.current_episode_name}")

        if not self.frame_keys:
            self.info_label.setText("当前Episode未找到可播放帧")
            for label in self.cam_labels.values():
                label.set_placeholder(f"{label._title}\n无图像")
            self.range_slider.set_total_frames(0)
            self.range_slider.set_subtask_segments([])
            self.configure_manual_range_inputs(0)
            self.range_info_label.setText("当前无可用帧")
            self.trim_btn.setEnabled(False)
            self.export_episode_btn.setEnabled(False)
        else:
            if not self.episode_data_error:
                self.subtask_segments = validate_subtask_segments(
                    self.subtask_segments, frame_count=len(self.frame_keys)
                )
            self.range_slider.set_total_frames(len(self.frame_keys))
            self.configure_manual_range_inputs(len(self.frame_keys))
            self.range_slider.reset_selection()
            self.show_frame(self.current_frame_index)
            self.trim_btn.setEnabled(True)
            self.export_episode_btn.setEnabled(True)

        self.delete_episode_btn.setEnabled(True)
        self.update_nav_buttons()
        self.update_play_button_text()
        self.update_range_info()
        self.refresh_subtask_timeline()

    def get_frame_geometry(self, frame_id):
        """计算并缓存指定帧在固定 pelvis/world 坐标系中的几何信息。"""
        if frame_id in self.ee_geometry_cache:
            return self.ee_geometry_cache[frame_id]
        if self.ee_projector is None:
            raise RuntimeError(self.ee_projector_error or "EE 投影器初始化失败。")
        if self.episode_data_error:
            raise RuntimeError(self.episode_data_error)

        frame_record = self.frame_records_by_idx.get(frame_id)
        if frame_record is None:
            raise RuntimeError(f"data.json 中缺少帧 idx={frame_id}。")

        geometry = self.ee_projector.compute_frame_geometry(frame_record)
        self.ee_geometry_cache[frame_id] = geometry
        return geometry

    def get_frame_projection(self, frame_id):
        """计算并缓存当前帧自己的相机投影。"""
        if frame_id in self.ee_projection_cache:
            return self.ee_projection_cache[frame_id]

        geometry = self.get_frame_geometry(frame_id)
        projection = self.ee_projector.project_geometry(geometry)
        self.ee_projection_cache[frame_id] = projection
        return projection

    def get_trajectory_samples(self, current_frame_index):
        """取得当前帧前后 3 秒、每秒 3 点的掌心像素轨迹。"""
        sample_positions = trajectory_sample_positions(
            current_index=current_frame_index,
            total_frames=len(self.frame_keys),
            fps=self.episode_fps,
            window_seconds=3.0,
            samples_per_second=3,
        )
        current_frame_id = self.frame_keys[current_frame_index]
        current_camera_geometry = self.get_frame_geometry(current_frame_id)
        sample_metadata = []
        points_in_world = []
        for relative_seconds, frame_position in sample_positions:
            sample_frame_id = self.frame_keys[frame_position]
            try:
                sample_geometry = self.get_frame_geometry(sample_frame_id)
            except Exception:
                # 个别历史/未来帧数据损坏时，仍保留当前帧的 EE 显示。
                continue
            sample_metadata.append((relative_seconds, sample_frame_id))
            points_in_world.append(sample_geometry["points_in_world"][0])

        if not points_in_world:
            return []

        trajectory_projection = self.ee_projector.project_world_points(
            np.asarray(points_in_world, dtype=np.float64),
            current_camera_geometry,
            require_all_in_front=False,
        )
        trajectory_samples = []
        for metadata, pixel, is_valid in zip(
            sample_metadata,
            trajectory_projection["pixels"],
            trajectory_projection["valid"],
            strict=True,
        ):
            if not is_valid or not np.all(np.isfinite(pixel)):
                continue
            relative_seconds, sample_frame_id = metadata
            trajectory_samples.append(
                {
                    "relative_seconds": relative_seconds,
                    "frame_id": sample_frame_id,
                    "pixel": pixel,
                }
            )
        return trajectory_samples

    def show_frame(self, frame_index):
        if not self.frame_keys:
            return

        frame_index = max(0, min(frame_index, len(self.frame_keys) - 1))
        frame_id = self.frame_keys[frame_index]
        cam_file_map = self.frames_map[frame_id]

        mode_text = "选中区间循环" if self.play_selection_only else "整段循环"
        state_text = "播放中" if self.is_playing else "已暂停"

        base_info_text = (
            f"episode：{self.current_episode_name}    "
            f"当前帧：{frame_index}/{len(self.frame_keys) - 1}    "
            f"帧编号：{frame_id:06d}    "
            f"模式：{mode_text}    状态：{state_text}"
        )
        projection_info = ""
        image_path = cam_file_map.get(self.CAMERA_ID)

        if not image_path or not os.path.isfile(image_path):
            self.raw_camera_label.set_placeholder("color_0 原始图像\n缺少该帧")
            self.eepose_camera_label.set_placeholder("右手掌心 EE Pose\n缺少原始图像")
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.raw_camera_label.set_placeholder("color_0 原始图像\n图片读取失败")
                self.eepose_camera_label.set_placeholder("右手掌心 EE Pose\n图片读取失败")
            else:
                self.raw_camera_label.set_pixmap(pixmap)
                try:
                    projection = self.get_frame_projection(frame_id)
                    trajectory_samples = self.get_trajectory_samples(frame_index)
                    annotated_pixmap = draw_right_palm_eepose(
                        pixmap,
                        projection,
                        trajectory_samples=trajectory_samples,
                    )
                    self.eepose_camera_label.set_pixmap(annotated_pixmap)
                    origin_pixel = projection["pixels"][0]
                    past_count = sum(
                        sample["relative_seconds"] < 0.0
                        for sample in trajectory_samples
                    )
                    future_count = len(trajectory_samples) - past_count
                    projection_info = (
                        f"    掌心像素：({origin_pixel[0]:.1f}, {origin_pixel[1]:.1f})"
                        f"    轨迹点：过去{past_count}/未来{future_count}"
                        f"    FPS：{self.episode_fps:g}"
                    )
                except Exception as exc:
                    self.eepose_camera_label.set_placeholder(
                        f"右手掌心 EE Pose\n投影失败\n{str(exc)}"
                    )
                    projection_info = f"    EE投影失败：{str(exc)}"

        self.info_label.setText(base_info_text + projection_info)

        self.range_slider.set_current_frame(frame_index)
        self.update_frame_step_buttons()

    def play_next_frame(self):
        if not self.frame_keys or not self.is_playing:
            return

        if self.play_selection_only:
            start, end = self.range_slider.get_selected_range()
            start = max(0, min(start, len(self.frame_keys) - 1))
            end = max(0, min(end, len(self.frame_keys) - 1))

            if self.current_frame_index < start or self.current_frame_index > end:
                self.current_frame_index = start

            self.show_frame(self.current_frame_index)
            self.current_frame_index += 1

            if self.current_frame_index > end:
                self.current_frame_index = start
        else:
            self.show_frame(self.current_frame_index)
            self.current_frame_index += 1

            if self.current_frame_index >= len(self.frame_keys):
                self.current_frame_index = 0

    def prev_episode(self):
        if self.current_episode_index > 0:
            self.load_episode(self.current_episode_index - 1)

    def next_episode(self):
        if self.current_episode_index < len(self.episodes) - 1:
            self.load_episode(self.current_episode_index + 1)

    def trim_selected_frames(self):
        if not self.frame_keys:
            QMessageBox.warning(self, "提示", "当前 Episode 没有可裁剪的帧。")
            return

        start_idx, end_idx = self.range_slider.get_selected_range()

        if start_idx < 0 or end_idx >= len(self.frame_keys):
            QMessageBox.warning(self, "提示", "选择区间无效。")
            return

        delete_frame_ids = self.frame_keys[start_idx:end_idx + 1]
        delete_count = len(delete_frame_ids)
        remain_count = len(self.frame_keys) - delete_count

        if remain_count <= 0:
            QMessageBox.warning(
                self,
                "提示",
                "不能把当前 Episode 的所有帧全部裁掉，至少需要保留 1 帧。"
            )
            return

        reply = QMessageBox.question(
            self,
            "确认裁剪",
            (
                f"当前Episode：{self.current_episode_name}\n"
                f"将删除帧区间：{start_idx} ~ {end_idx}（共 {delete_count} 帧）\n"
                f"删除后剩余 {remain_count} 帧，并重新编号。\n\n"
                f"该操作会直接修改磁盘文件，是否继续？"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.is_playing = False
        self.update_play_button_text()

        try:
            self.delete_and_renumber_frames(delete_frame_ids)
            self.load_episode(self.current_episode_index)
            QMessageBox.information(
                self,
                "完成",
                f"裁剪完成。\n已删除 {delete_count} 帧，并完成重新编号。"
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"裁剪失败：\n{str(e)}")

    def next_episode_name(self):
        episode_numbers = []
        number_widths = []

        for episode_name in self.find_episodes():
            match = re.fullmatch(r"episode_(\d+)", episode_name)
            if match:
                number_text = match.group(1)
                episode_numbers.append(int(number_text))
                number_widths.append(len(number_text))

        next_number = max(episode_numbers, default=-1) + 1
        width = max([4, len(str(next_number)), *number_widths])
        return f"episode_{next_number:0{width}d}"

    def export_selected_frames_as_episode(self):
        if not self.frame_keys:
            QMessageBox.warning(self, "提示", "当前 Episode 没有可导出的帧。")
            return

        start_idx, end_idx = self.range_slider.get_selected_range()
        if start_idx < 0 or end_idx >= len(self.frame_keys) or end_idx < start_idx:
            QMessageBox.warning(self, "提示", "选择区间无效。")
            return

        selected_frame_ids = self.frame_keys[start_idx:end_idx + 1]
        new_episode_name = self.next_episode_name()
        source_episode_dir = os.path.join(self.root_dir, self.current_episode_name)
        destination_episode_dir = os.path.join(self.root_dir, new_episode_name)

        reply = QMessageBox.question(
            self,
            "确认导出",
            (
                f"源 Episode：{self.current_episode_name}\n"
                f"选择区间：{start_idx} ~ {end_idx}（共 {len(selected_frame_ids)} 帧）\n"
                f"新 Episode：{new_episode_name}\n\n"
                "将完整复制选中帧的图像、深度、音频以及 data.json 中的 "
                "state、action、关节角等所有帧信息。\n"
                "原 Episode 不会被修改，是否继续？"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        # load_episode 会默认回到第 0 帧，因此导出前先保存完整的查看状态。
        viewed_frame_index = self.range_slider.current_frame
        selected_range = (start_idx, end_idx)
        selection_play_mode = self.play_selection_only

        self.is_playing = False
        self.update_play_button_text()

        try:
            exported_count = export_episode_frames(
                source_episode_dir,
                destination_episode_dir,
                selected_frame_ids,
            )

            self.episodes = self.find_episodes()
            # 保持在源 Episode，方便用户继续选择下一段并连续导出多个 Episode。
            self.current_episode_index = self.episodes.index(self.current_episode_name)
            self.load_episode(self.current_episode_index)

            # 源 Episode 没有被修改，恢复导出前的光标和选择区间。
            restored_frame_index = max(
                0,
                min(viewed_frame_index, len(self.frame_keys) - 1),
            )
            restored_start = max(0, min(selected_range[0], len(self.frame_keys) - 1))
            restored_end = max(0, min(selected_range[1], len(self.frame_keys) - 1))
            self.range_slider.set_selected_range(restored_start, restored_end)
            self.play_selection_only = selection_play_mode
            self.current_frame_index = restored_frame_index
            self.show_frame(restored_frame_index)
            # 导出完成后保持暂停，避免完成提示框期间定时播放再次移动光标。
            self.is_playing = False
            self.update_play_button_text()
            self.update_range_info()

            QMessageBox.information(
                self,
                "导出完成",
                (
                    f"已生成 {new_episode_name}，共 {exported_count} 帧。\n"
                    "图像和 data.json 中的全部帧信息已同步重编号；"
                    "原 Episode 保持不变。\n"
                    f"已暂停并返回导出前查看的第 {restored_frame_index} 帧。"
                ),
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出新 Episode 失败：\n{str(e)}")

    def delete_current_episode(self):
        if not self.episodes or not self.current_episode_name:
            QMessageBox.warning(self, "提示", "当前没有可删除的Episode。")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            "该操作会删除当前Episode！",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )

        if reply != QMessageBox.Yes:
            return

        self.is_playing = False
        self.update_play_button_text()

        episode_path = os.path.join(self.root_dir, self.current_episode_name)
        current_index = self.current_episode_index

        try:
            if not os.path.isdir(episode_path):
                raise RuntimeError(f"数据集目录不存在：{episode_path}")

            shutil.rmtree(episode_path)

            self.episodes = self.find_episodes()

            if not self.episodes:
                self.clear_player_state("当前路径下已无Episode")
                QMessageBox.information(self, "完成", "当前Episode已删除。")
                return

            next_index = min(current_index, len(self.episodes) - 1)
            self.load_episode(next_index)
            self.is_playing = True
            self.update_play_button_text()
            self.update_range_info()

            QMessageBox.information(self, "完成", "当前Episode已删除。")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除当前Episode失败：\n{str(e)}")

    def delete_and_renumber_frames(self, delete_frame_ids):
        colors_dir = os.path.join(self.root_dir, self.current_episode_name, "colors")
        json_path = os.path.join(self.root_dir, self.current_episode_name, "data.json")

        if not os.path.isdir(colors_dir):
            raise RuntimeError(f"colors 目录不存在：{colors_dir}")

        if not os.path.isfile(json_path):
            raise RuntimeError(f"data.json 不存在：{json_path}")

        delete_frame_set = set(delete_frame_ids)
        original_frame_ids = list(self.frame_keys)
        kept_old_positions = [
            position
            for position, frame_id in enumerate(original_frame_ids)
            if frame_id not in delete_frame_set
        ]
        remapped_subtask_segments = remap_subtask_segments(
            self.subtask_segments, kept_old_positions
        )

        all_files = []
        for filename in os.listdir(colors_dir):
            match = self.FILE_PATTERN.match(filename)
            if not match:
                continue

            frame_id = int(match.group(1))
            cam_id = int(match.group(2))
            old_path = os.path.join(colors_dir, filename)
            all_files.append((frame_id, cam_id, old_path, filename))

        if not all_files:
            raise RuntimeError("colors 目录中没有找到合法 jpg 帧文件。")

        for frame_id, cam_id, old_path, filename in all_files:
            if frame_id in delete_frame_set and os.path.exists(old_path):
                os.remove(old_path)

        remaining = []
        for filename in os.listdir(colors_dir):
            match = self.FILE_PATTERN.match(filename)
            if not match:
                continue

            frame_id = int(match.group(1))
            cam_id = int(match.group(2))
            old_path = os.path.join(colors_dir, filename)
            remaining.append((frame_id, cam_id, old_path, filename))

        if not remaining:
            raise RuntimeError("裁剪后无剩余图片文件。")

        grouped = defaultdict(list)
        for frame_id, cam_id, old_path, filename in remaining:
            grouped[frame_id].append((cam_id, old_path, filename))

        old_frame_ids = sorted(grouped.keys())

        new_id_map = {
            old_frame_id: new_frame_id
            for new_frame_id, old_frame_id in enumerate(old_frame_ids)
        }

        temp_records = []

        for old_frame_id in old_frame_ids:
            for cam_id, old_path, old_filename in grouped[old_frame_id]:
                temp_name = f"__tmp__{old_frame_id:06d}_color_{cam_id}.jpg"
                temp_path = os.path.join(colors_dir, temp_name)
                os.rename(old_path, temp_path)
                temp_records.append((old_frame_id, cam_id, temp_path))

        for old_frame_id, cam_id, temp_path in temp_records:
            new_frame_id = new_id_map[old_frame_id]
            new_name = f"{new_frame_id:06d}_color_{cam_id}.jpg"
            new_path = os.path.join(colors_dir, new_name)
            os.rename(temp_path, new_path)

        with open(json_path, "r", encoding="utf-8") as f:
            json_obj = json.load(f)

        if "data" not in json_obj or not isinstance(json_obj["data"], list):
            raise RuntimeError("data.json 格式不正确：缺少 data 数组。")

        old_data_list = json_obj["data"]
        new_data_list = []

        for item in old_data_list:
            if not isinstance(item, dict):
                continue

            old_idx = item.get("idx", None)
            if old_idx is None:
                continue

            if old_idx in delete_frame_set:
                continue

            if old_idx in new_id_map:
                new_idx = new_id_map[old_idx]
                new_item = json.loads(json.dumps(item, ensure_ascii=False))
                new_item["idx"] = new_idx

                if isinstance(new_item.get("colors"), dict):
                    new_colors = {}
                    for color_key, color_path in new_item["colors"].items():
                        new_colors[color_key] = f"colors/{new_idx:06d}_{color_key}.jpg"
                    new_item["colors"] = new_colors

                if isinstance(new_item.get("depths"), dict):
                    new_depths = {}
                    for depth_key, depth_path in new_item["depths"].items():
                        new_depths[depth_key] = f"depths/{new_idx:06d}_{depth_key}.jpg"
                    new_item["depths"] = new_depths

                if isinstance(new_item.get("audios"), dict):
                    new_audios = {}
                    for audio_key, audio_path in new_item["audios"].items():
                        new_audios[audio_key] = f"audios/audio_{new_idx:06d}_{audio_key}.npy"
                    new_item["audios"] = new_audios

                new_data_list.append(new_item)

        if not new_data_list:
            raise RuntimeError("裁剪后 data.json 中无剩余帧数据。")

        json_obj["data"] = new_data_list
        set_episode_subtask_segments(json_obj, remapped_subtask_segments)
        write_json_atomically(json_path, json_obj)


def main():
    app = QApplication(sys.argv)

    root_dir = ""

    player = DatasetPlayer(root_dir=root_dir, interval_ms=100)
    player.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
