"""G1 23 DoF kitchen-counter env. Import only after Isaac Lab AppLauncher."""

from __future__ import annotations

import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg
from isaaclab.sim import SimulationCfg
from isaaclab.utils.configclass import configclass
from isaaclab.visualizers import VisualizerCfg
from isaaclab_newton.physics import MJWarpSolverCfg, NewtonCfg
from isaaclab_ov.physics import OvPhysxCfg
from isaaclab_physx.physics import PhysxCfg
from isaaclab.physics import PhysxAutoCfg
from isaaclab_tasks.utils import PresetCfg
from isaaclab_tasks.utils.presets import MultiBackendRendererCfg

from simfoundry.embodiment import (
    D435I_INTRINSICS,
    D435I_OFFSET_POS,
    D435I_OFFSET_ROT_XYZW,
    G1_23DOF_JOINT_NAMES,
)
from simfoundry.isaac_envs import mdp as kitchen_mdp
from simfoundry.robots import G1_STUMP_CFG
from simfoundry.scene_bridge.isaac_cfg import apply_layout_to_scene
from simfoundry.scene_package import load_named_scene

JOINT_CFG = SceneEntityCfg("robot", joint_names=list(G1_23DOF_JOINT_NAMES), preserve_order=True)


@configclass
class KitchenPhysicsCfg(PresetCfg):
    isaacsim_physx: PhysxCfg = PhysxCfg()
    ovphysx: OvPhysxCfg = OvPhysxCfg()
    physx: PhysxAutoCfg = PhysxAutoCfg(isaacsim_physx=isaacsim_physx, ovphysx=ovphysx)
    newton_mjwarp: NewtonCfg = NewtonCfg(
        solver_cfg=MJWarpSolverCfg(
            njmax=400,
            nconmax=80,
            cone="pyramidal",
            integrator="implicitfast",
            impratio=1,
            update_data_interval=2,
        ),
        num_substeps=2,
        debug_mode=False,
        use_cuda_graph=True,
    )
    default: NewtonCfg = newton_mjwarp


def _placeholder_box(name: str, kinematic: bool) -> AssetBaseCfg | RigidObjectCfg:
    spawn = sim_utils.CuboidCfg(
        size=(0.05, 0.05, 0.05),
        collision_props=sim_utils.CollisionBaseCfg(collision_enabled=True),
    )
    prim = f"{{ENV_REGEX_NS}}/{name}"
    if kinematic:
        return AssetBaseCfg(prim_path=prim, spawn=spawn)
    return RigidObjectCfg(prim_path=prim, spawn=spawn)


@configclass
class KitchenSceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(50.0, 50.0)),
    )
    # A-period stump demos: fixed base. Free-floating G1 has no balance policy, so arm
    # motion / counter contact tips it over. Unlock again when locomotion is added.
    robot: ArticulationCfg = G1_STUMP_CFG
    d435i = CameraCfg(
        prim_path="{ENV_REGEX_NS}/Robot/torso_link/d435i",
        update_period=0.0,
        height=D435I_INTRINSICS.height,
        width=D435I_INTRINSICS.width,
        data_types=["rgb"],
        renderer_cfg=MultiBackendRendererCfg(),
        spawn=sim_utils.PinholeCameraCfg.from_intrinsic_matrix(
            intrinsic_matrix=D435I_INTRINSICS.as_matrix_row_major(),
            width=D435I_INTRINSICS.width,
            height=D435I_INTRINSICS.height,
            clipping_range=(0.1, 8.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=D435I_OFFSET_POS,
            rot=D435I_OFFSET_ROT_XYZW,
            convention="ros",
        ),
    )
    # Overwritten from scenes/<id>/twin/layout.json in env cfg __post_init__.
    counter: AssetBaseCfg = _placeholder_box("counter", kinematic=True)
    cup: RigidObjectCfg = _placeholder_box("cup", kinematic=False)
    bowl: RigidObjectCfg = _placeholder_box("bowl", kinematic=False)
    plate: RigidObjectCfg = _placeholder_box("plate", kinematic=False)
    bottle: RigidObjectCfg = _placeholder_box("bottle", kinematic=False)
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(color=(0.85, 0.85, 0.85), intensity=2800.0),
    )


@configclass
class ActionsCfg:
    joint_pos = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=list(G1_23DOF_JOINT_NAMES),
        preserve_order=True,
        scale=1.0,
        use_default_offset=True,
    )


@configclass
class ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        joint_pos = ObsTerm(func=mdp.joint_pos, params={"asset_cfg": JOINT_CFG})

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
class EventCfg:
    reset_scene = EventTerm(func=mdp.reset_scene_to_default, mode="reset")
    randomize_cup = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "pose_range": {"x": (0.0, 0.0), "y": (0.0, 0.0)},
            "velocity_range": {},
            "asset_cfg": SceneEntityCfg("cup"),
        },
    )


@configclass
class RewardsCfg:
    alive = RewTerm(func=mdp.is_alive, weight=1.0)
    push_cup_to_bowl = RewTerm(
        func=kitchen_mdp.negative_xy_distance,
        weight=1.0,
        params={"asset_a": "cup", "asset_b": "bowl"},
    )


@configclass
class TerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    fallen = DoneTerm(
        func=kitchen_mdp.root_height_below,
        params={"minimum_height": 0.35, "asset_cfg": SceneEntityCfg("robot")},
    )


@configclass
class KitchenCounterEnvCfg(ManagerBasedRLEnvCfg):
    scene_id: str = "kitchen_counter_placeholder"
    decimation = 4
    episode_length_s = 8.0
    sim: SimulationCfg = SimulationCfg(dt=1 / 120, render_interval=decimation, physics=KitchenPhysicsCfg())
    scene: KitchenSceneCfg = KitchenSceneCfg(num_envs=1, env_spacing=3.5, replicate_physics=True)
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    events: EventCfg = EventCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()

    def __post_init__(self) -> None:
        self.sim.default_visualizer_cfg = VisualizerCfg(eye=(2.6, -2.2, 1.4), lookat=(0.55, 0.0, 0.75))
        self.scene.lazy_sensor_update = False
        # Fix pelvis so stump arm demos stand without a locomotion policy.
        self.scene.robot.spawn.articulation_props.fix_root_link = True
        package = load_named_scene(self.scene_id)
        apply_layout_to_scene(self.scene, package)
