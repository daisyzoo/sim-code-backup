"""G1 23 DoF U1 sorting-station env. Import only after Isaac Lab AppLauncher.

Independent of kitchen_counter_placeholder / indoor_lab_g1_23.
Table constants (layout.json is source of truth):

    TABLE_LENGTH = 1.50
    TABLE_WIDTH = 0.60
    TABLE_THICKNESS = 0.025
    TABLE_TOP = 0.75  # ground → tabletop
    TABLE_HEIGHT = TABLE_TOP - TABLE_THICKNESS  # 0.725, legs
    TABLE_SURFACE_Z = TABLE_TOP - TABLE_THICKNESS / 2  # 0.7375, slab center
    FLOOR_Z = 0.0
"""

from __future__ import annotations

import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg
from isaaclab.sim import SimulationCfg
from isaaclab.utils.configclass import configclass
from isaaclab.visualizers import VisualizerCfg
from isaaclab_newton.physics import MJWarpSolverCfg, NewtonCfg
from isaaclab_tasks.utils.presets import MultiBackendRendererCfg
from isaaclab_physx.renderers import IsaacRtxRendererCfg

from simfoundry.calibration.sorting_station import (
    SORTING_D435I_POS,
    SORTING_D435I_ROT_XYZW,
    SORTING_ROBOT_POS,
    SORTING_ROBOT_ROT_XYZW,
)
from simfoundry.embodiment import D435I_INTRINSICS
from simfoundry.isaac_envs import mdp as kitchen_mdp
from simfoundry.isaac_envs.kitchen_env_cfg import (
    KitchenCounterEnvCfg,
    KitchenPhysicsCfg,
    TerminationsCfg,
    _placeholder_box,
)
from simfoundry.robots import G1_U1_23DOF_JOINT_NAMES, g1_u1_rubber_cfg
from simfoundry.scene_bridge.isaac_cfg import apply_layout_to_scene, textured_floor_cuboid_cfg
from simfoundry.scene_package import load_named_scene

U1_JOINT_CFG = SceneEntityCfg("robot", joint_names=list(G1_U1_23DOF_JOINT_NAMES), preserve_order=True)

# NewtonWarpRenderer returns near-black RGB on U1 visuals; RTX matches demo / teleop.
_RTX_CAMERA_RENDERER = MultiBackendRendererCfg(
    default=IsaacRtxRendererCfg(),
    isaacsim_rtx=IsaacRtxRendererCfg(),
)


@configclass
class SortingPhysicsCfg(KitchenPhysicsCfg):
    """Higher contact budget for dual-arm pushes against table + parcels."""

    newton_mjwarp: NewtonCfg = NewtonCfg(
        solver_cfg=MJWarpSolverCfg(
            njmax=520,
            nconmax=320,
            cone="pyramidal",
            integrator="implicitfast",
            impratio=1,
            update_data_interval=1,
        ),
        num_substeps=3,
        debug_mode=False,
        use_cuda_graph=True,
    )
    default: NewtonCfg = newton_mjwarp


@configclass
class SortingStationSceneCfg(InteractiveSceneCfg):
    """Light-blue 1.50×0.60 table, kraft box, black mailer, two crate stacks."""

    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(50.0, 50.0), color=(0.32, 0.33, 0.34)),
        # Keep the safety plane below the carpet.  Both surfaces previously
        # ended at z=0 and caused RTX z-fighting (black flashing under table).
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, -0.03)),
    )
    # Grey carpet from pic/3.jpg crop (see assets/textures/sorting_station/).
    floor = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/floor",
        spawn=textured_floor_cuboid_cfg(size=(10.0, 10.0, 0.02)),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.8, -0.3, -0.01)),
    )
    robot: ArticulationCfg = g1_u1_rubber_cfg()
    d435i = CameraCfg(
        prim_path="{ENV_REGEX_NS}/Robot/Geometry/pelvis/torso_link/d435i",
        update_period=0.0,
        height=D435I_INTRINSICS.height,
        width=D435I_INTRINSICS.width,
        data_types=["rgb"],
        renderer_cfg=_RTX_CAMERA_RENDERER,
        spawn=sim_utils.PinholeCameraCfg.from_intrinsic_matrix(
            intrinsic_matrix=D435I_INTRINSICS.as_matrix_row_major(),
            width=D435I_INTRINSICS.width,
            height=D435I_INTRINSICS.height,
            clipping_range=(0.1, 8.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=SORTING_D435I_POS,
            rot=SORTING_D435I_ROT_XYZW,
            convention="ros",
        ),
        update_latest_camera_pose=True,
    )
    table: AssetBaseCfg = _placeholder_box("table", kinematic=True)
    table_edge_wear: AssetBaseCfg = _placeholder_box("table_edge_wear", kinematic=True)
    table_leg_fl: AssetBaseCfg = _placeholder_box("table_leg_fl", kinematic=True)
    table_leg_fr: AssetBaseCfg = _placeholder_box("table_leg_fr", kinematic=True)
    table_leg_bl: AssetBaseCfg = _placeholder_box("table_leg_bl", kinematic=True)
    table_leg_br: AssetBaseCfg = _placeholder_box("table_leg_br", kinematic=True)
    parcel_box: RigidObjectCfg = _placeholder_box("parcel_box", kinematic=False)
    parcel_box_label: RigidObjectCfg = _placeholder_box("parcel_box_label", kinematic=True)
    parcel_box_b: AssetBaseCfg = _placeholder_box("parcel_box_b", kinematic=True)
    parcel_box_b_label: AssetBaseCfg = _placeholder_box("parcel_box_b_label", kinematic=True)
    mailer: RigidObjectCfg = _placeholder_box("mailer", kinematic=False)
    mailer_label: RigidObjectCfg = _placeholder_box("mailer_label", kinematic=True)
    mailer_b: RigidObjectCfg = _placeholder_box("mailer_b", kinematic=True)
    mailer_b_label: RigidObjectCfg = _placeholder_box("mailer_b_label", kinematic=True)
    mailer_c: AssetBaseCfg = _placeholder_box("mailer_c", kinematic=True)
    mailer_c_label: AssetBaseCfg = _placeholder_box("mailer_c_label", kinematic=True)
    mailer_d: AssetBaseCfg = _placeholder_box("mailer_d", kinematic=True)
    mailer_d_label: AssetBaseCfg = _placeholder_box("mailer_d_label", kinematic=True)
    bin_box_l0: AssetBaseCfg = _placeholder_box("bin_box_l0", kinematic=True)
    bin_box_l1: AssetBaseCfg = _placeholder_box("bin_box_l1", kinematic=True)
    bin_box_l2: AssetBaseCfg = _placeholder_box("bin_box_l2", kinematic=True)
    bin_box: RigidObjectCfg = _placeholder_box("bin_box", kinematic=False)
    bin_mailer_l0: AssetBaseCfg = _placeholder_box("bin_mailer_l0", kinematic=True)
    bin_mailer_l1: AssetBaseCfg = _placeholder_box("bin_mailer_l1", kinematic=True)
    bin_mailer_l2: AssetBaseCfg = _placeholder_box("bin_mailer_l2", kinematic=True)
    bin_mailer: RigidObjectCfg = _placeholder_box("bin_mailer", kinematic=False)
    yellow_chair: AssetBaseCfg = _placeholder_box("yellow_chair", kinematic=True)
    equipment_wrap: AssetBaseCfg = _placeholder_box("equipment_wrap", kinematic=True)
    backdrop_panel: AssetBaseCfg = _placeholder_box("backdrop_panel", kinematic=True)
    pc_tower: AssetBaseCfg = _placeholder_box("pc_tower", kinematic=True)
    metal_rack: AssetBaseCfg = _placeholder_box("metal_rack", kinematic=True)
    # Tuned vs pick_cup_soring_0824 mean brightness ~0.44 (RTX path).
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(color=(0.86, 0.82, 0.76), intensity=55.0),
    )
    sun = AssetBaseCfg(
        prim_path="/World/sun",
        spawn=sim_utils.DistantLightCfg(
            color=(0.96, 0.93, 0.88),
            intensity=45.0,
            angle=0.9,
        ),
    )
    key_light = AssetBaseCfg(
        prim_path="/World/key_light",
        spawn=sim_utils.DiskLightCfg(
            color=(1.0, 0.96, 0.90),
            intensity=680.0,
            radius=0.48,
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.35, -0.15, 2.55)),
    )
    fill_light = AssetBaseCfg(
        prim_path="/World/fill_light",
        spawn=sim_utils.DiskLightCfg(
            color=(0.94, 0.95, 0.98),
            intensity=175.0,
            radius=0.55,
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(-0.55, 0.65, 2.1)),
    )
    # Phone-style third person behind robot right shoulder (matches pic/*.mp4).
    # Spawn pose uses OpenGL look-at so kit_viewport recording is correct even if
    # per-step pose updates are delayed under Newton.
    viewer_cam = CameraCfg(
        prim_path="{ENV_REGEX_NS}/viewer_cam",
        update_period=0.0,
        height=540,
        width=960,
        data_types=["rgb"],
        renderer_cfg=_RTX_CAMERA_RENDERER,
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=14.0,
            focus_distance=4.0,
            horizontal_aperture=20.955,
            clipping_range=(0.25, 24.0),
        ),
        # eye=(-1.6,-2.1,1.85) → look=(0.40,0.0,0.78); rot xyzw OpenGL (-Z forward).
        offset=CameraCfg.OffsetCfg(
            pos=(-1.60, -2.10, 1.85),
            rot=(0.5309, -0.2124, -0.3047, 0.7617),
            convention="opengl",
        ),
        update_latest_camera_pose=True,
    )


@configclass
class SortingActionsCfg:
    joint_pos = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=list(G1_U1_23DOF_JOINT_NAMES),
        preserve_order=True,
        scale=1.0,
        use_default_offset=True,
    )


@configclass
class SortingObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        joint_pos = ObsTerm(func=mdp.joint_pos, params={"asset_cfg": U1_JOINT_CFG})

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class RgbCfg(ObsGroup):
        rgb = ObsTerm(
            func=mdp.image,
            params={
                "sensor_cfg": SceneEntityCfg("d435i"),
                "data_type": "rgb",
                "normalize": False,
                "permute": True,
            },
        )

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()
    rgb: RgbCfg = RgbCfg()


@configclass
class SortingEventCfg:
    reset_scene = EventTerm(func=mdp.reset_scene_to_default, mode="reset")


@configclass
class SortingRewardsCfg:
    alive = RewTerm(func=mdp.is_alive, weight=1.0)
    push_box_to_bin = RewTerm(
        func=kitchen_mdp.negative_xy_distance,
        weight=1.0,
        params={"asset_a": "parcel_box", "asset_b": "bin_box"},
    )


@configclass
class SortingStationEnvCfg(KitchenCounterEnvCfg):
    scene_id: str = "sorting_station_g1_23"
    # Physics 120 Hz (parent sim.dt); decimation 8 → 15 Hz env.step_dt (matches real teleop).
    decimation = 8
    episode_length_s = 16.0
    sim: SimulationCfg = SimulationCfg(dt=1 / 120, render_interval=decimation, physics=SortingPhysicsCfg())
    scene: SortingStationSceneCfg = SortingStationSceneCfg(num_envs=1, env_spacing=4.0, replicate_physics=True)
    observations: SortingObservationsCfg = SortingObservationsCfg()
    actions: SortingActionsCfg = SortingActionsCfg()
    events: SortingEventCfg = SortingEventCfg()
    rewards: SortingRewardsCfg = SortingRewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()

    def __post_init__(self) -> None:
        self.sim.default_visualizer_cfg = VisualizerCfg(
            eye=(-1.60, -2.10, 1.85),
            lookat=(0.40, 0.0, 0.78),
            streaming_view=True,
            streaming_sensor_prim_path="/World/envs/env_[^/]+/Robot/Geometry/pelvis/torso_link/d435i",
            streaming_envs=[0],
        )
        self.scene.lazy_sensor_update = False
        # Match control decimation to avoid double render per step.
        self.sim.render_interval = self.decimation
        # U1 USD already has PhysicsFixedJoint root_joint; Isaac cannot add another
        # because ArticulationRootAPI sits on Geometry (not a rigid body).
        self.scene.robot.spawn.articulation_props.fix_root_link = False
        package = load_named_scene(self.scene_id)
        apply_layout_to_scene(self.scene, package)
        # Keep decorative table parcels off-camera so single-parcel collect shows one package.
        _off = (5.0, 5.0, 3.0)
        for name in (
            "parcel_box_b",
            "parcel_box_label",
            "parcel_box_b_label",
            "mailer_b",
            "mailer_label",
            "mailer_b_label",
            "mailer_c",
            "mailer_c_label",
            "mailer_d",
            "mailer_d_label",
        ):
            asset = getattr(self.scene, name, None)
            if asset is None or not hasattr(asset, "init_state"):
                continue
            asset.init_state.pos = _off
        self.scene.d435i.update_latest_camera_pose = True
        self.scene.viewer_cam.update_latest_camera_pose = True
        # Calibrated: face +X toward table, 0.34 m standoff from near edge.
        self.scene.robot.init_state.pos = SORTING_ROBOT_POS
        self.scene.robot.init_state.rot = SORTING_ROBOT_ROT_XYZW
        arms = self.scene.robot.actuators["arms"]
        arms.stiffness = 220.0
        arms.damping = 22.0
        legs = self.scene.robot.actuators["legs"]
        # Hold waist_yaw hard at rest so the robot stays square to the table.
        if isinstance(legs.stiffness, dict):
            legs.stiffness = {**legs.stiffness, "waist_yaw_joint": 400.0}
        if isinstance(legs.damping, dict):
            legs.damping = {**legs.damping, "waist_yaw_joint": 20.0}
        arms.effort_limit_sim = 180.0
