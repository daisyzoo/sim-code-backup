import dataclasses


@dataclasses.dataclass(frozen=True)
class RobotConfig:
    motors: list[str]
    cameras: list[str]
    camera_to_image_key: dict[str, str]
    json_state_data_name: list[str]
    json_action_data_name: list[str]


Z1_CONFIG = RobotConfig(
    motors=[
        "kLeftWaist",
        "kLeftShoulder",
        "kLeftElbow",
        "kLeftForearmRoll",
        "kLeftWristAngle",
        "kLeftWristRotate",
        "kLeftGripper",
        "kRightWaist",
        "kRightShoulder",
        "kRightElbow",
        "kRightForearmRoll",
        "kRightWristAngle",
        "kRightWristRotate",
        "kRightGripper",
    ],
    cameras=[
        "cam_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={"color_0": "cam_high", "color_1": "cam_left_wrist", "color_2": "cam_right_wrist"},
    json_state_data_name=["left_arm.qpos", "right_arm.qpos"],
    json_action_data_name=["left_arm.qpos", "right_arm.qpos"],
)


Z1_SINGLE_CONFIG = RobotConfig(
    motors=[
        "kWaist",
        "kShoulder",
        "kElbow",
        "kForearmRoll",
        "kWristAngle",
        "kWristRotate",
        "kGripper",
    ],
    cameras=[
        "cam_high",
        "cam_wrist",
    ],
    camera_to_image_key={"color_0": "cam_high", "color_1": "cam_wrist"},
    json_state_data_name=["left_arm.qpos", "right_arm.qpos"],
    json_action_data_name=["left_arm.qpos", "right_arm.qpos"],
)


G1_DEX1_CONFIG = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kLeftWristPitch",
        "kLeftWristYaw",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kRightWristPitch",
        "kRightWristYaw",
        "kLeftGripper",
        "kRightGripper",
    ],
    cameras=[
        "cam_left_high",
        "cam_right_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={
        "color_0": "cam_left_high",
        "color_1": "cam_right_high",
        "color_2": "cam_left_wrist",
        "color_3": "cam_right_wrist",
    },
    json_state_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
    json_action_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
)


G1_DEX1_CONFIG_SIM = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kLeftWristPitch",
        "kLeftWristYaw",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kRightWristPitch",
        "kRightWristYaw",
        "kLeftGripper",
        "kRightGripper",
    ],
    cameras=[
        "cam_left_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={
        "color_0": "cam_left_high",
        "color_1": "cam_left_wrist",
        "color_2": "cam_right_wrist",
    },
    json_state_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
    json_action_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
)


G1_23DOF_ARMS5_WAIST1_CONFIG = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kWaistYaw",
    ],
    cameras=[
        "cam_high",
    ],
    camera_to_image_key={
        "color_0": "cam_high",
    },
    json_state_data_name=["left_arm.qpos", "right_arm.qpos", "body.qpos[0]"],
    json_action_data_name=["left_arm.qpos", "right_arm.qpos", "body.qpos[0]"],
)


G1_23DOF_RIGHT_ARM5_WAIST1_CONFIG = RobotConfig(
    motors=[
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kWaistYaw",
    ],
    cameras=[
        "cam_high",
    ],
    camera_to_image_key={
        "color_0": "cam_high",
    },
    json_state_data_name=["right_arm.qpos", "body.qpos[0]"],
    json_action_data_name=["right_arm.qpos", "body.qpos[0]"],
)


G1_23DOF_RIGHT_ARM5_WAIST1_RIGHT_EEPOSE_CONFIG = RobotConfig(
    motors=[
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kWaistYaw",
        "kRightEeX",
        "kRightEeY",
        "kRightEeZ",
        "kRightEeQx",
        "kRightEeQy",
        "kRightEeQz",
        "kRightEeQw",
    ],
    cameras=[
        "cam_high",
    ],
    camera_to_image_key={
        "color_0": "cam_high",
    },
    json_state_data_name=["right_arm.qpos", "body.qpos[0]", "right_ee.qpos"],
    json_action_data_name=["right_arm.qpos", "body.qpos[0]", "right_ee.qpos"],
)


G1_23DOF_RIGHT_EEPOSE_WAIST1_CONFIG = RobotConfig(
    motors=[
        "kRightEeX",
        "kRightEeY",
        "kRightEeZ",
        "kRightEeQx",
        "kRightEeQy",
        "kRightEeQz",
        "kRightEeQw",
        "kWaistYaw",
    ],
    cameras=[
        "cam_high",
    ],
    camera_to_image_key={
        "color_0": "cam_high",
    },
    json_state_data_name=["right_ee.qpos", "body.qpos[0]"],
    json_action_data_name=["right_ee.qpos", "body.qpos[0]"],
)


G1_DEX3_CONFIG = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kLeftWristPitch",
        "kLeftWristYaw",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kRightWristPitch",
        "kRightWristYaw",
        "kLeftHandThumb0",
        "kLeftHandThumb1",
        "kLeftHandThumb2",
        "kLeftHandMiddle0",
        "kLeftHandMiddle1",
        "kLeftHandIndex0",
        "kLeftHandIndex1",
        "kRightHandThumb0",
        "kRightHandThumb1",
        "kRightHandThumb2",
        "kRightHandIndex0",
        "kRightHandIndex1",
        "kRightHandMiddle0",
        "kRightHandMiddle1",
    ],
    cameras=[
        "cam_left_high",
        "cam_right_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={
        "color_0": "cam_left_high",
        "color_1": "cam_right_high",
        "color_2": "cam_left_wrist",
        "color_3": "cam_right_wrist",
    },
    json_state_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
    json_action_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
)


G1_BRAINCO_CONFIG = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kLeftWristPitch",
        "kLeftWristYaw",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kRightWristPitch",
        "kRightWristYaw",
        "kLeftHandThumb",
        "kLeftHandThumbAux",
        "kLeftHandIndex",
        "kLeftHandMiddle",
        "kLeftHandRing",
        "kLeftHandPinky",
        "kRightHandThumb",
        "kRightHandThumbAux",
        "kRightHandIndex",
        "kRightHandMiddle",
        "kRightHandRing",
        "kRightHandPinky",
    ],
    cameras=[
        "cam_left_high",
        "cam_right_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={
        "color_0": "cam_left_high",
        "color_1": "cam_right_high",
        "color_2": "cam_left_wrist",
        "color_3": "cam_right_wrist",
    },
    json_state_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
    json_action_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
)


G1_INSPIRE_CONFIG = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kLeftWristPitch",
        "kLeftWristYaw",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kRightWristPitch",
        "kRightWristYaw",
        "kLeftHandPinky",
        "kLeftHandRing",
        "kLeftHandMiddle",
        "kLeftHandIndex",
        "kLeftHandThumbBend",
        "kLeftHandThumbRotation",
        "kRightHandPinky",
        "kRightHandRing",
        "kRightHandMiddle",
        "kRightHandIndex",
        "kRightHandThumbBend",
        "kRightHandThumbRotation",
    ],
    cameras=[
        "cam_left_high",
        "cam_right_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={
        "color_0": "cam_left_high",
        "color_1": "cam_right_high",
        "color_2": "cam_left_wrist",
        "color_3": "cam_right_wrist",
    },
    json_state_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
    json_action_data_name=["left_arm.qpos", "right_arm.qpos", "left_ee.qpos", "right_ee.qpos"],
)


MOVEIBLE_LIFT_G1_DEX1_USEWAIST_CONFIG = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kLeftWristPitch",
        "kLeftWristYaw",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kRightWristPitch",
        "kRightWristYaw",
        "kWaistYaw",
        "kWaistPitch",
        "kHighLift",
        "kMoveX",
        "kMoveYaw",
        "kLeftGripper",
        "kRightGripper",
    ],
    cameras=[
        "cam_left_high",
        "cam_right_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={
        "color_0": "cam_left_high",
        "color_1": "cam_right_high",
        "color_2": "cam_left_wrist",
        "color_3": "cam_right_wrist",
    },
    json_state_data_name=[
        "left_arm.qpos",
        "right_arm.qpos",
        "waist.qpos",
        "torso.height",
        "chassis.qvel",
        "left_ee.qpos",
        "right_ee.qpos",
    ],
    json_action_data_name=[
        "left_arm.qpos",
        "right_arm.qpos",
        "waist.qpos",
        "torso.qvel",
        "chassis.qvel",
        "left_ee.qpos",
        "right_ee.qpos",
    ],
)


MOVEIBLE_LIFT_G1_DEX1_NOUSEWAIST_CONFIG = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kLeftWristPitch",
        "kLeftWristYaw",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kRightWristPitch",
        "kRightWristYaw",
        "kHighLift",
        "kMoveX",
        "kMoveYaw",
        "kLeftGripper",
        "kRightGripper",
    ],
    cameras=[
        "cam_left_high",
        "cam_right_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={
        "color_0": "cam_left_high",
        "color_1": "cam_right_high",
        "color_2": "cam_left_wrist",
        "color_3": "cam_right_wrist",
    },
    json_state_data_name=[
        "left_arm.qpos",
        "right_arm.qpos",
        "torso.height",
        "chassis.qvel",
        "left_ee.qpos",
        "right_ee.qpos",
    ],
    json_action_data_name=[
        "left_arm.qpos",
        "right_arm.qpos",
        "torso.qvel",
        "chassis.qvel",
        "left_ee.qpos",
        "right_ee.qpos",
    ],
)


LIFT_G1_DEX1_USEWAIST_CONFIG = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kLeftWristPitch",
        "kLeftWristYaw",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kRightWristPitch",
        "kRightWristYaw",
        "kWaistYaw",
        "kWaistRoll",
        "kHighLift",
        "kLeftGripper",
        "kRightGripper",
    ],
    cameras=[
        "cam_left_high",
        "cam_right_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={
        "color_0": "cam_left_high",
        "color_1": "cam_right_high",
        "color_2": "cam_left_wrist",
        "color_3": "cam_right_wrist",
    },
    json_state_data_name=[
        "left_arm.qpos",
        "right_arm.qpos",
        "waist.qpos",
        "torso.height",
        "left_ee.qpos",
        "right_ee.qpos",
    ],
    json_action_data_name=[
        "left_arm.qpos",
        "right_arm.qpos",
        "waist.qpos",
        "torso.qvel",
        "left_ee.qpos",
        "right_ee.qpos",
    ],
)


LIFT_G1_DEX1_NOUSEWAIST_CONFIG = RobotConfig(
    motors=[
        "kLeftShoulderPitch",
        "kLeftShoulderRoll",
        "kLeftShoulderYaw",
        "kLeftElbow",
        "kLeftWristRoll",
        "kLeftWristPitch",
        "kLeftWristYaw",
        "kRightShoulderPitch",
        "kRightShoulderRoll",
        "kRightShoulderYaw",
        "kRightElbow",
        "kRightWristRoll",
        "kRightWristPitch",
        "kRightWristYaw",
        "kHighLift",
        "kLeftGripper",
        "kRightGripper",
    ],
    cameras=[
        "cam_left_high",
        "cam_right_high",
        "cam_left_wrist",
        "cam_right_wrist",
    ],
    camera_to_image_key={
        "color_0": "cam_left_high",
        "color_1": "cam_right_high",
        "color_2": "cam_left_wrist",
        "color_3": "cam_right_wrist",
    },
    json_state_data_name=["left_arm.qpos", "right_arm.qpos", "torso.height", "left_ee.qpos", "right_ee.qpos"],
    json_action_data_name=["left_arm.qpos", "right_arm.qpos", "torso.qvel", "left_ee.qpos", "right_ee.qpos"],
)

ROBOT_CONFIGS = {
    "Unitree_Z1_Single": Z1_SINGLE_CONFIG,
    "Unitree_Z1_Dual": Z1_CONFIG,
    "Unitree_G1_Dex1": G1_DEX1_CONFIG,
    "Unitree_G1_Dex1_Sim": G1_DEX1_CONFIG_SIM,
    "Unitree_G1_23Dof_Arms5_Waist1": G1_23DOF_ARMS5_WAIST1_CONFIG,
    "Unitree_G1_23Dof_RightArm5_Waist1": G1_23DOF_RIGHT_ARM5_WAIST1_CONFIG,
    "Unitree_G1_23Dof_RightArm5_Waist1_RightEePose": G1_23DOF_RIGHT_ARM5_WAIST1_RIGHT_EEPOSE_CONFIG,
    "Unitree_G1_23Dof_RightEePose_Waist1": G1_23DOF_RIGHT_EEPOSE_WAIST1_CONFIG,
    "Unitree_G1_Dex3": G1_DEX3_CONFIG,
    "Unitree_G1_Brainco": G1_BRAINCO_CONFIG,
    "Unitree_G1_Inspire": G1_INSPIRE_CONFIG,
    "Unitree_G1_MoveibleLift_Dex1_UseWaist": MOVEIBLE_LIFT_G1_DEX1_USEWAIST_CONFIG,
    "Unitree_G1_MoveibleLift_Dex1_NoUseWaist": MOVEIBLE_LIFT_G1_DEX1_NOUSEWAIST_CONFIG,
    "Unitree_G1_Lift_Dex1_UseWaist": LIFT_G1_DEX1_USEWAIST_CONFIG,
    "Unitree_G1_Lift_Dex1_NoUseWaist": LIFT_G1_DEX1_NOUSEWAIST_CONFIG,
}
