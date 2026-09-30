"""G1 23 indoor lab (connected zones). Import only after AppLauncher."""

from __future__ import annotations

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.sensors import CameraCfg
from isaaclab.utils.configclass import configclass
from isaaclab.visualizers import VisualizerCfg
from isaaclab_tasks.utils.presets import MultiBackendRendererCfg

from simfoundry.isaac_envs.kitchen_env_cfg import (
    ActionsCfg,
    EventCfg,
    KitchenCounterEnvCfg,
    KitchenSceneCfg,
    ObservationsCfg,
    RewardsCfg,
    TerminationsCfg,
    _placeholder_box,
)
from simfoundry.robots import G1_STUMP_CFG
from simfoundry.scene_bridge.isaac_cfg import apply_layout_to_scene
from simfoundry.scene_package import load_named_scene


def _wall(name: str) -> AssetBaseCfg:
    return _placeholder_box(name, kinematic=True)


def _kinematic_body(name: str) -> RigidObjectCfg:
    """Kinematic cuboid with TensorAPI pose writes (door / button / switch)."""
    return _placeholder_box(name, kinematic=False)


@configclass
class IndoorLabSceneCfg(KitchenSceneCfg):
    robot: ArticulationCfg = G1_STUMP_CFG
    hall_wall_left: AssetBaseCfg = _wall("hall_wall_left")
    hall_wall_right: AssetBaseCfg = _wall("hall_wall_right")
    vestibule_left: AssetBaseCfg = _wall("vestibule_left")
    vestibule_right: AssetBaseCfg = _wall("vestibule_right")
    room_wall_left: AssetBaseCfg = _wall("room_wall_left")
    room_wall_right: AssetBaseCfg = _wall("room_wall_right")
    room_wall_far: AssetBaseCfg = _wall("room_wall_far")
    door: RigidObjectCfg = _kinematic_body("door")
    wall_button: RigidObjectCfg = _kinematic_body("wall_button")
    floor_marker: AssetBaseCfg = _wall("floor_marker")
    person: AssetBaseCfg = _wall("person")
    lab_bench: AssetBaseCfg = _wall("lab_bench")
    table_switch: RigidObjectCfg = _kinematic_body("table_switch")
    lab_box: RigidObjectCfg = _placeholder_box("lab_box", kinematic=False)
    # Third-person camera posed each demo step to match the Kit 3D viewer.
    viewer_cam = CameraCfg(
        prim_path="{ENV_REGEX_NS}/viewer_cam",
        update_period=0.0,
        height=540,
        width=960,
        data_types=["rgb"],
        renderer_cfg=MultiBackendRendererCfg(),
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=12.0,
            focus_distance=8.0,
            horizontal_aperture=20.955,
            clipping_range=(0.15, 24.0),
        ),
        offset=CameraCfg.OffsetCfg(pos=(-1.8, -8.0, 4.6), rot=(0.0, 0.0, 0.0, 1.0), convention="world"),
        update_latest_camera_pose=True,
    )


@configclass
class IndoorLabEnvCfg(KitchenCounterEnvCfg):
    scene_id: str = "indoor_lab_g1_23"
    episode_length_s = 180.0
    scene: IndoorLabSceneCfg = IndoorLabSceneCfg(num_envs=1, env_spacing=14.0, replicate_physics=True)
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    events: EventCfg = EventCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()

    def __post_init__(self) -> None:
        # Kit Perspective + a streaming panel of the D435i head camera.
        self.sim.default_visualizer_cfg = VisualizerCfg(
            eye=(1.4, -6.2, 3.5),
            lookat=(3.6, 0.15, 0.85),
            streaming_view=True,
            streaming_sensor_prim_path="/World/envs/env_[^/]+/Robot/torso_link/d435i",
            streaming_envs=[0],
        )
        self.scene.lazy_sensor_update = False
        self.scene.robot.spawn.articulation_props.fix_root_link = True
        package = load_named_scene(self.scene_id)
        apply_layout_to_scene(self.scene, package)
        # Follow the torso / viewer xform every render; default False freezes spawn pose.
        self.scene.d435i.update_latest_camera_pose = True
        self.scene.viewer_cam.update_latest_camera_pose = True
