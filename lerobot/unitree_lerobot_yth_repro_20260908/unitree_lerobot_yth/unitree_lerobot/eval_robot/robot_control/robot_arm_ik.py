import casadi
import meshcat.geometry as mg
import numpy as np
import pinocchio as pin
import time
from pinocchio import casadi as cpin
from pinocchio.visualize import MeshcatVisualizer
import os
import sys
from unitree_lerobot.eval_robot.utils.weighted_moving_filter import WeightedMovingFilter

import logging_mp

logger_mp = logging_mp.getLogger(__name__)
logger_mp.setLevel(logging_mp.INFO)
parent2_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent2_dir)


class G1_29_ArmIK:
    def __init__(self, Unit_Test=False, Visualization=False):
        np.set_printoptions(precision=5, suppress=True, linewidth=200)

        self.Unit_Test = Unit_Test
        self.Visualization = Visualization

        if not self.Unit_Test:
            self.robot = pin.RobotWrapper.BuildFromURDF(
                "unitree_lerobot/eval_robot/assets/g1/g1_body29_hand14.urdf", "unitree_lerobot/eval_robot/assets/g1/"
            )
        else:
            self.robot = pin.RobotWrapper.BuildFromURDF(
                "unitree_lerobot/eval_robot/assets/g1/g1_body29_hand14.urdf", "unitree_lerobot/eval_robot/assets/g1/"
            )  # for test

        self.mixed_jointsToLockIDs = [
            "left_hip_pitch_joint",
            "left_hip_roll_joint",
            "left_hip_yaw_joint",
            "left_knee_joint",
            "left_ankle_pitch_joint",
            "left_ankle_roll_joint",
            "right_hip_pitch_joint",
            "right_hip_roll_joint",
            "right_hip_yaw_joint",
            "right_knee_joint",
            "right_ankle_pitch_joint",
            "right_ankle_roll_joint",
            "waist_yaw_joint",
            "waist_roll_joint",
            "waist_pitch_joint",
            "left_hand_thumb_0_joint",
            "left_hand_thumb_1_joint",
            "left_hand_thumb_2_joint",
            "left_hand_middle_0_joint",
            "left_hand_middle_1_joint",
            "left_hand_index_0_joint",
            "left_hand_index_1_joint",
            "right_hand_thumb_0_joint",
            "right_hand_thumb_1_joint",
            "right_hand_thumb_2_joint",
            "right_hand_index_0_joint",
            "right_hand_index_1_joint",
            "right_hand_middle_0_joint",
            "right_hand_middle_1_joint",
        ]

        self.reduced_robot = self.robot.buildReducedRobot(
            list_of_joints_to_lock=self.mixed_jointsToLockIDs,
            reference_configuration=np.array([0.0] * self.robot.model.nq),
        )

        self.reduced_robot.model.addFrame(
            pin.Frame(
                "L_ee",
                self.reduced_robot.model.getJointId("left_wrist_yaw_joint"),
                pin.SE3(np.eye(3), np.array([0.05, 0, 0]).T),
                pin.FrameType.OP_FRAME,
            )
        )

        self.reduced_robot.model.addFrame(
            pin.Frame(
                "R_ee",
                self.reduced_robot.model.getJointId("right_wrist_yaw_joint"),
                pin.SE3(np.eye(3), np.array([0.05, 0, 0]).T),
                pin.FrameType.OP_FRAME,
            )
        )

        # for i in range(self.reduced_robot.model.nframes):
        #     frame = self.reduced_robot.model.frames[i]
        #     frame_id = self.reduced_robot.model.getFrameId(frame.name)
        #     logger_mp.debug(f"Frame ID: {frame_id}, Name: {frame.name}")
        # for idx, name in enumerate(self.reduced_robot.model.names):
        #     logger_mp.debug(f"{idx}: {name}")

        # Creating Casadi models and data for symbolic computing
        self.cmodel = cpin.Model(self.reduced_robot.model)
        self.cdata = self.cmodel.createData()

        # Creating symbolic variables
        self.cq = casadi.SX.sym("q", self.reduced_robot.model.nq, 1)
        self.cTf_l = casadi.SX.sym("tf_l", 4, 4)
        self.cTf_r = casadi.SX.sym("tf_r", 4, 4)
        cpin.framesForwardKinematics(self.cmodel, self.cdata, self.cq)

        # Get the hand joint ID and define the error function
        self.L_hand_id = self.reduced_robot.model.getFrameId("L_ee")
        self.R_hand_id = self.reduced_robot.model.getFrameId("R_ee")

        self.translational_error = casadi.Function(
            "translational_error",
            [self.cq, self.cTf_l, self.cTf_r],
            [
                casadi.vertcat(
                    self.cdata.oMf[self.L_hand_id].translation - self.cTf_l[:3, 3],
                    self.cdata.oMf[self.R_hand_id].translation - self.cTf_r[:3, 3],
                )
            ],
        )
        self.rotational_error = casadi.Function(
            "rotational_error",
            [self.cq, self.cTf_l, self.cTf_r],
            [
                casadi.vertcat(
                    cpin.log3(self.cdata.oMf[self.L_hand_id].rotation @ self.cTf_l[:3, :3].T),
                    cpin.log3(self.cdata.oMf[self.R_hand_id].rotation @ self.cTf_r[:3, :3].T),
                )
            ],
        )

        # Defining the optimization problem
        self.opti = casadi.Opti()
        self.var_q = self.opti.variable(self.reduced_robot.model.nq)
        self.var_q_last = self.opti.parameter(self.reduced_robot.model.nq)  # for smooth
        self.param_tf_l = self.opti.parameter(4, 4)
        self.param_tf_r = self.opti.parameter(4, 4)
        self.translational_cost = casadi.sumsqr(self.translational_error(self.var_q, self.param_tf_l, self.param_tf_r))
        self.rotation_cost = casadi.sumsqr(self.rotational_error(self.var_q, self.param_tf_l, self.param_tf_r))
        self.regularization_cost = casadi.sumsqr(self.var_q)
        self.smooth_cost = casadi.sumsqr(self.var_q - self.var_q_last)

        # Setting optimization constraints and goals
        self.opti.subject_to(
            self.opti.bounded(
                self.reduced_robot.model.lowerPositionLimit, self.var_q, self.reduced_robot.model.upperPositionLimit
            )
        )
        self.opti.minimize(
            50 * self.translational_cost + self.rotation_cost + 0.02 * self.regularization_cost + 0.1 * self.smooth_cost
        )

        opts = {
            "ipopt": {"print_level": 0, "max_iter": 50, "tol": 1e-6},
            "print_time": False,  # print or not
            "calc_lam_p": False,  # https://github.com/casadi/casadi/wiki/FAQ:-Why-am-I-getting-%22NaN-detected%22in-my-optimization%3F
        }
        self.opti.solver("ipopt", opts)

        self.init_data = np.zeros(self.reduced_robot.model.nq)
        self.smooth_filter = WeightedMovingFilter(np.array([0.4, 0.3, 0.2, 0.1]), 14)
        self.vis = None

        if self.Visualization:
            # Initialize the Meshcat visualizer for visualization
            self.vis = MeshcatVisualizer(
                self.reduced_robot.model, self.reduced_robot.collision_model, self.reduced_robot.visual_model
            )
            self.vis.initViewer(open=True)
            self.vis.loadViewerModel("pinocchio")
            self.vis.displayFrames(True, frame_ids=[107, 108], axis_length=0.15, axis_width=5)
            self.vis.display(pin.neutral(self.reduced_robot.model))

            # Enable the display of end effector target frames with short axis lengths and greater width.
            frame_viz_names = ["L_ee_target", "R_ee_target"]
            FRAME_AXIS_POSITIONS = (
                np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 1]]).astype(np.float32).T
            )
            FRAME_AXIS_COLORS = (
                np.array([[1, 0, 0], [1, 0.6, 0], [0, 1, 0], [0.6, 1, 0], [0, 0, 1], [0, 0.6, 1]]).astype(np.float32).T
            )
            axis_length = 0.1
            axis_width = 20
            for frame_viz_name in frame_viz_names:
                self.vis.viewer[frame_viz_name].set_object(
                    mg.LineSegments(
                        mg.PointsGeometry(
                            position=axis_length * FRAME_AXIS_POSITIONS,
                            color=FRAME_AXIS_COLORS,
                        ),
                        mg.LineBasicMaterial(
                            linewidth=axis_width,
                            vertexColors=True,
                        ),
                    )
                )

    # If the robot arm is not the same size as your arm :)
    def scale_arms(self, human_left_pose, human_right_pose, human_arm_length=0.60, robot_arm_length=0.75):
        scale_factor = robot_arm_length / human_arm_length
        robot_left_pose = human_left_pose.copy()
        robot_right_pose = human_right_pose.copy()
        robot_left_pose[:3, 3] *= scale_factor
        robot_right_pose[:3, 3] *= scale_factor
        return robot_left_pose, robot_right_pose

    def solve_ik(self, left_wrist, right_wrist, current_lr_arm_motor_q=None, current_lr_arm_motor_dq=None):
        if current_lr_arm_motor_q is not None:
            self.init_data = current_lr_arm_motor_q
        self.opti.set_initial(self.var_q, self.init_data)

        # left_wrist, right_wrist = self.scale_arms(left_wrist, right_wrist)
        if self.Visualization:
            self.vis.viewer["L_ee_target"].set_transform(left_wrist)  # for visualization
            self.vis.viewer["R_ee_target"].set_transform(right_wrist)  # for visualization

        self.opti.set_value(self.param_tf_l, left_wrist)
        self.opti.set_value(self.param_tf_r, right_wrist)
        self.opti.set_value(self.var_q_last, self.init_data)  # for smooth

        try:
            self.opti.solve()
            # sol = self.opti.solve_limited()

            sol_q = self.opti.value(self.var_q)
            self.smooth_filter.add_data(sol_q)
            sol_q = self.smooth_filter.filtered_data

            if current_lr_arm_motor_dq is not None:
                v = current_lr_arm_motor_dq * 0.0
            else:
                v = (sol_q - self.init_data) * 0.0

            self.init_data = sol_q

            sol_tauff = pin.rnea(
                self.reduced_robot.model, self.reduced_robot.data, sol_q, v, np.zeros(self.reduced_robot.model.nv)
            )

            if self.Visualization:
                self.vis.display(sol_q)  # for visualization

            return sol_q, sol_tauff

        except Exception as e:
            logger_mp.error(f"ERROR in convergence, plotting debug info.{e}")

            sol_q = self.opti.debug.value(self.var_q)
            self.smooth_filter.add_data(sol_q)
            sol_q = self.smooth_filter.filtered_data

            if current_lr_arm_motor_dq is not None:
                v = current_lr_arm_motor_dq * 0.0
            else:
                v = (sol_q - self.init_data) * 0.0

            self.init_data = sol_q

            sol_tauff = pin.rnea(
                self.reduced_robot.model, self.reduced_robot.data, sol_q, v, np.zeros(self.reduced_robot.model.nv)
            )

            logger_mp.error(
                f"sol_q:{sol_q} \nmotorstate: \n{current_lr_arm_motor_q} \nleft_pose: \n{left_wrist} \nright_pose: \n{right_wrist}"
            )
            if self.Visualization:
                self.vis.display(sol_q)  # for visualization

            # return sol_q, sol_tauff
            return current_lr_arm_motor_q, np.zeros(self.reduced_robot.model.nv)

    def solve_tau(self, current_lr_arm_motor_q=None, current_lr_arm_motor_dq=None):
        try:
            sol_tauff = pin.rnea(
                self.reduced_robot.model,
                self.reduced_robot.data,
                current_lr_arm_motor_q,
                np.zeros(self.reduced_robot.model.nv),
                np.zeros(self.reduced_robot.model.nv),
            )
            return sol_tauff

        except Exception as e:
            logger_mp.error(f"ERROR in convergence, plotting debug info.{e}")
            return np.zeros(self.reduced_robot.model.nv)


class G1_23_ArmIK:
    def __init__(self, Unit_Test=False, Visualization=False):
        np.set_printoptions(precision=5, suppress=True, linewidth=200)

        self.Unit_Test = Unit_Test
        self.Visualization = Visualization

        if not self.Unit_Test:
            self.robot = pin.RobotWrapper.BuildFromURDF(
                "unitree_lerobot/eval_robot/assets/g1/g1_body23.urdf", "unitree_lerobot/eval_robot/assets/g1/"
            )
        else:
            self.robot = pin.RobotWrapper.BuildFromURDF(
                "unitree_lerobot/eval_robot/assets/g1/g1_body23.urdf", "unitree_lerobot/eval_robot/assets/g1/"
            )  # for test

        self.mixed_jointsToLockIDs = [
            "left_hip_pitch_joint",
            "left_hip_roll_joint",
            "left_hip_yaw_joint",
            "left_knee_joint",
            "left_ankle_pitch_joint",
            "left_ankle_roll_joint",
            "right_hip_pitch_joint",
            "right_hip_roll_joint",
            "right_hip_yaw_joint",
            "right_knee_joint",
            "right_ankle_pitch_joint",
            "right_ankle_roll_joint",
            "waist_yaw_joint",
        ]

        self.reduced_robot = self.robot.buildReducedRobot(
            list_of_joints_to_lock=self.mixed_jointsToLockIDs,
            reference_configuration=np.array([0.0] * self.robot.model.nq),
        )

        self.reduced_robot.model.addFrame(
            pin.Frame(
                "L_ee",
                self.reduced_robot.model.getJointId("left_wrist_roll_joint"),
                pin.SE3(np.eye(3), np.array([0.20, 0, 0]).T),
                pin.FrameType.OP_FRAME,
            )
        )

        self.reduced_robot.model.addFrame(
            pin.Frame(
                "R_ee",
                self.reduced_robot.model.getJointId("right_wrist_roll_joint"),
                pin.SE3(np.eye(3), np.array([0.20, 0, 0]).T),
                pin.FrameType.OP_FRAME,
            )
        )

        # for i in range(self.reduced_robot.model.nframes):
        #     frame = self.reduced_robot.model.frames[i]
        #     frame_id = self.reduced_robot.model.getFrameId(frame.name)
        #     logger_mp.debug(f"Frame ID: {frame_id}, Name: {frame.name}")

        # Creating Casadi models and data for symbolic computing
        self.cmodel = cpin.Model(self.reduced_robot.model)
        self.cdata = self.cmodel.createData()

        # Creating symbolic variables
        self.cq = casadi.SX.sym("q", self.reduced_robot.model.nq, 1)
        self.cTf_l = casadi.SX.sym("tf_l", 4, 4)
        self.cTf_r = casadi.SX.sym("tf_r", 4, 4)
        cpin.framesForwardKinematics(self.cmodel, self.cdata, self.cq)

        # Get the hand joint ID and define the error function
        self.L_hand_id = self.reduced_robot.model.getFrameId("L_ee")
        self.R_hand_id = self.reduced_robot.model.getFrameId("R_ee")

        self.translational_error = casadi.Function(
            "translational_error",
            [self.cq, self.cTf_l, self.cTf_r],
            [
                casadi.vertcat(
                    self.cdata.oMf[self.L_hand_id].translation - self.cTf_l[:3, 3],
                    self.cdata.oMf[self.R_hand_id].translation - self.cTf_r[:3, 3],
                )
            ],
        )
        self.rotational_error = casadi.Function(
            "rotational_error",
            [self.cq, self.cTf_l, self.cTf_r],
            [
                casadi.vertcat(
                    cpin.log3(self.cdata.oMf[self.L_hand_id].rotation @ self.cTf_l[:3, :3].T),
                    cpin.log3(self.cdata.oMf[self.R_hand_id].rotation @ self.cTf_r[:3, :3].T),
                )
            ],
        )

        # Defining the optimization problem
        self.opti = casadi.Opti()
        self.var_q = self.opti.variable(self.reduced_robot.model.nq)
        self.var_q_last = self.opti.parameter(self.reduced_robot.model.nq)  # for smooth
        self.param_tf_l = self.opti.parameter(4, 4)
        self.param_tf_r = self.opti.parameter(4, 4)
        self.translational_cost = casadi.sumsqr(self.translational_error(self.var_q, self.param_tf_l, self.param_tf_r))
        self.rotation_cost = casadi.sumsqr(self.rotational_error(self.var_q, self.param_tf_l, self.param_tf_r))
        self.regularization_cost = casadi.sumsqr(self.var_q)
        self.smooth_cost = casadi.sumsqr(self.var_q - self.var_q_last)

        # Setting optimization constraints and goals
        self.opti.subject_to(
            self.opti.bounded(
                self.reduced_robot.model.lowerPositionLimit, self.var_q, self.reduced_robot.model.upperPositionLimit
            )
        )
        self.opti.minimize(
            50 * self.translational_cost
            + 0.5 * self.rotation_cost
            + 0.02 * self.regularization_cost
            + 0.1 * self.smooth_cost
        )

        opts = {
            "ipopt": {"print_level": 0, "max_iter": 50, "tol": 1e-6},
            "print_time": False,  # print or not
            "calc_lam_p": False,  # https://github.com/casadi/casadi/wiki/FAQ:-Why-am-I-getting-%22NaN-detected%22in-my-optimization%3F
        }
        self.opti.solver("ipopt", opts)

        self.init_data = np.zeros(self.reduced_robot.model.nq)
        self.smooth_filter = WeightedMovingFilter(np.array([0.4, 0.3, 0.2, 0.1]), 10)
        self.vis = None

        if self.Visualization:
            # Initialize the Meshcat visualizer for visualization
            self.vis = MeshcatVisualizer(
                self.reduced_robot.model, self.reduced_robot.collision_model, self.reduced_robot.visual_model
            )
            self.vis.initViewer(open=True)
            self.vis.loadViewerModel("pinocchio")
            self.vis.displayFrames(True, frame_ids=[67, 68], axis_length=0.15, axis_width=5)
            self.vis.display(pin.neutral(self.reduced_robot.model))

            # Enable the display of end effector target frames with short axis lengths and greater width.
            frame_viz_names = ["L_ee_target", "R_ee_target"]
            FRAME_AXIS_POSITIONS = (
                np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 1]]).astype(np.float32).T
            )
            FRAME_AXIS_COLORS = (
                np.array([[1, 0, 0], [1, 0.6, 0], [0, 1, 0], [0.6, 1, 0], [0, 0, 1], [0, 0.6, 1]]).astype(np.float32).T
            )
            axis_length = 0.1
            axis_width = 20
            for frame_viz_name in frame_viz_names:
                self.vis.viewer[frame_viz_name].set_object(
                    mg.LineSegments(
                        mg.PointsGeometry(
                            position=axis_length * FRAME_AXIS_POSITIONS,
                            color=FRAME_AXIS_COLORS,
                        ),
                        mg.LineBasicMaterial(
                            linewidth=axis_width,
                            vertexColors=True,
                        ),
                    )
                )

    # If the robot arm is not the same size as your arm :)
    def scale_arms(self, human_left_pose, human_right_pose, human_arm_length=0.60, robot_arm_length=0.75):
        scale_factor = robot_arm_length / human_arm_length
        robot_left_pose = human_left_pose.copy()
        robot_right_pose = human_right_pose.copy()
        robot_left_pose[:3, 3] *= scale_factor
        robot_right_pose[:3, 3] *= scale_factor
        return robot_left_pose, robot_right_pose

    def solve_ik(self, left_wrist, right_wrist, current_lr_arm_motor_q=None, current_lr_arm_motor_dq=None):
        if current_lr_arm_motor_q is not None:
            self.init_data = current_lr_arm_motor_q
        self.opti.set_initial(self.var_q, self.init_data)

        # left_wrist, right_wrist = self.scale_arms(left_wrist, right_wrist)
        if self.Visualization:
            self.vis.viewer["L_ee_target"].set_transform(left_wrist)  # for visualization
            self.vis.viewer["R_ee_target"].set_transform(right_wrist)  # for visualization

        self.opti.set_value(self.param_tf_l, left_wrist)
        self.opti.set_value(self.param_tf_r, right_wrist)
        self.opti.set_value(self.var_q_last, self.init_data)  # for smooth

        try:
            self.opti.solve()
            # sol = self.opti.solve_limited()

            sol_q = self.opti.value(self.var_q)
            self.smooth_filter.add_data(sol_q)
            sol_q = self.smooth_filter.filtered_data

            if current_lr_arm_motor_dq is not None:
                v = current_lr_arm_motor_dq * 0.0
            else:
                v = (sol_q - self.init_data) * 0.0

            self.init_data = sol_q

            sol_tauff = pin.rnea(
                self.reduced_robot.model, self.reduced_robot.data, sol_q, v, np.zeros(self.reduced_robot.model.nv)
            )

            if self.Visualization:
                self.vis.display(sol_q)  # for visualization

            return sol_q, sol_tauff

        except Exception as e:
            logger_mp.error(f"ERROR in convergence, plotting debug info.{e}")

            sol_q = self.opti.debug.value(self.var_q)
            self.smooth_filter.add_data(sol_q)
            sol_q = self.smooth_filter.filtered_data

            if current_lr_arm_motor_dq is not None:
                v = current_lr_arm_motor_dq * 0.0
            else:
                v = (sol_q - self.init_data) * 0.0

            self.init_data = sol_q

            sol_tauff = pin.rnea(
                self.reduced_robot.model, self.reduced_robot.data, sol_q, v, np.zeros(self.reduced_robot.model.nv)
            )

            logger_mp.error(
                f"sol_q:{sol_q} \nmotorstate: \n{current_lr_arm_motor_q} \nleft_pose: \n{left_wrist} \nright_pose: \n{right_wrist}"
            )
            if self.Visualization:
                self.vis.display(sol_q)  # for visualization

            # return sol_q, sol_tauff
            return current_lr_arm_motor_q, np.zeros(self.reduced_robot.model.nv)

    def solve_tau(self, current_lr_arm_motor_q=None, current_lr_arm_motor_dq=None):
        try:
            sol_tauff = pin.rnea(
                self.reduced_robot.model,
                self.reduced_robot.data,
                current_lr_arm_motor_q,
                np.zeros(self.reduced_robot.model.nv),
                np.zeros(self.reduced_robot.model.nv),
            )
            return sol_tauff

        except Exception as e:
            logger_mp.error(f"ERROR in convergence, plotting debug info.{e}")
            return np.zeros(self.reduced_robot.model.nv)


class G1_23_RightArmWaistIK:
    """Solve G1-23 right-arm joints from a right end-effector pose and waist yaw target.

    The reduced model keeps ``waist_yaw_joint`` and the five right-arm joints,
    and locks legs plus the left arm. The returned right-arm order matches the
    existing G1_23_RightArm5 control view:
    shoulder_pitch, shoulder_roll, shoulder_yaw, elbow, wrist_roll.
    """

    RIGHT_ARM_JOINT_NAMES = [
        "right_shoulder_pitch_joint",
        "right_shoulder_roll_joint",
        "right_shoulder_yaw_joint",
        "right_elbow_joint",
        "right_wrist_roll_joint",
    ]

    def __init__(self, Unit_Test=False, Visualization=False):
        np.set_printoptions(precision=5, suppress=True, linewidth=200)

        self.Unit_Test = Unit_Test
        self.Visualization = Visualization
        self.robot = pin.RobotWrapper.BuildFromURDF(
            "unitree_lerobot/eval_robot/assets/g1/g1_body23.urdf", "unitree_lerobot/eval_robot/assets/g1/"
        )

        joints_to_lock = [
            "left_hip_pitch_joint",
            "left_hip_roll_joint",
            "left_hip_yaw_joint",
            "left_knee_joint",
            "left_ankle_pitch_joint",
            "left_ankle_roll_joint",
            "right_hip_pitch_joint",
            "right_hip_roll_joint",
            "right_hip_yaw_joint",
            "right_knee_joint",
            "right_ankle_pitch_joint",
            "right_ankle_roll_joint",
            "left_shoulder_pitch_joint",
            "left_shoulder_roll_joint",
            "left_shoulder_yaw_joint",
            "left_elbow_joint",
            "left_wrist_roll_joint",
        ]
        self.reduced_robot = self.robot.buildReducedRobot(
            list_of_joints_to_lock=joints_to_lock,
            reference_configuration=np.array([0.0] * self.robot.model.nq),
        )
        self.reduced_robot.model.addFrame(
            pin.Frame(
                "R_ee",
                self.reduced_robot.model.getJointId("right_wrist_roll_joint"),
                pin.SE3(np.eye(3), np.array([0.20, 0, 0]).T),
                pin.FrameType.OP_FRAME,
            )
        )
        self.reduced_data = self.reduced_robot.model.createData()

        self.waist_q_index = self._joint_q_index("waist_yaw_joint")
        self.right_arm_q_indices = np.asarray(
            [self._joint_q_index(name) for name in self.RIGHT_ARM_JOINT_NAMES],
            dtype=np.int64,
        )

        self.cmodel = cpin.Model(self.reduced_robot.model)
        self.cdata = self.cmodel.createData()
        self.cq = casadi.SX.sym("q", self.reduced_robot.model.nq, 1)
        self.cTf_r = casadi.SX.sym("tf_r", 4, 4)
        cpin.framesForwardKinematics(self.cmodel, self.cdata, self.cq)

        self.R_hand_id = self.reduced_robot.model.getFrameId("R_ee")
        self.translational_error = casadi.Function(
            "right_translational_error",
            [self.cq, self.cTf_r],
            [self.cdata.oMf[self.R_hand_id].translation - self.cTf_r[:3, 3]],
        )
        self.rotational_error = casadi.Function(
            "right_rotational_error",
            [self.cq, self.cTf_r],
            [cpin.log3(self.cdata.oMf[self.R_hand_id].rotation @ self.cTf_r[:3, :3].T)],
        )

        self.opti = casadi.Opti()
        self.var_q = self.opti.variable(self.reduced_robot.model.nq)
        self.var_q_last = self.opti.parameter(self.reduced_robot.model.nq)
        self.param_tf_r = self.opti.parameter(4, 4)
        self.param_waist_yaw = self.opti.parameter()

        translational_cost = casadi.sumsqr(self.translational_error(self.var_q, self.param_tf_r))
        rotation_cost = casadi.sumsqr(self.rotational_error(self.var_q, self.param_tf_r))
        regularization_cost = casadi.sumsqr(self.var_q)
        smooth_cost = casadi.sumsqr(self.var_q - self.var_q_last)
        self.opti.subject_to(
            self.opti.bounded(
                self.reduced_robot.model.lowerPositionLimit, self.var_q, self.reduced_robot.model.upperPositionLimit
            )
        )
        self.opti.subject_to(self.var_q[self.waist_q_index] == self.param_waist_yaw)
        self.opti.minimize(
            50 * translational_cost
            + 0.5 * rotation_cost
            + 0.02 * regularization_cost
            + 0.1 * smooth_cost
        )
        opts = {
            "ipopt": {"print_level": 0, "max_iter": 50, "tol": 1e-6},
            "print_time": False,
            "calc_lam_p": False,
        }
        self.opti.solver("ipopt", opts)

        self.init_data = np.zeros(self.reduced_robot.model.nq)
        self.smooth_filter = WeightedMovingFilter(np.array([0.4, 0.3, 0.2, 0.1]), self.reduced_robot.model.nq)
        self.last_success = True

    def _joint_q_index(self, joint_name: str) -> int:
        joint_id = self.reduced_robot.model.getJointId(joint_name)
        if joint_id <= 0:
            raise ValueError(f"Joint not found in reduced model: {joint_name}")
        return int(self.reduced_robot.model.joints[joint_id].idx_q)

    @staticmethod
    def pose7_to_matrix(right_ee_pose: np.ndarray | list[float]) -> np.ndarray:
        pose = np.asarray(right_ee_pose, dtype=np.float64).reshape(-1)
        if pose.shape[0] != 7:
            raise ValueError(f"Expected right_ee_pose length 7, got {pose.shape[0]}")
        quat = pin.Quaternion(pose[6], pose[3], pose[4], pose[5])
        quat.normalize()
        transform = np.eye(4)
        transform[:3, :3] = quat.toRotationMatrix()
        transform[:3, 3] = pose[:3]
        return transform

    def solve_ik(
        self,
        right_ee_pose: np.ndarray | list[float],
        waist_yaw: float,
        current_right_arm_q: np.ndarray | list[float] | None = None,
    ) -> tuple[np.ndarray, float]:
        if current_right_arm_q is not None:
            current_right_arm_q = np.asarray(current_right_arm_q, dtype=np.float64).reshape(-1)
            if current_right_arm_q.shape[0] != len(self.RIGHT_ARM_JOINT_NAMES):
                raise ValueError(f"Expected current_right_arm_q length 5, got {current_right_arm_q.shape[0]}")
            self.init_data[self.right_arm_q_indices] = current_right_arm_q
        self.init_data[self.waist_q_index] = float(waist_yaw)

        self.opti.set_initial(self.var_q, self.init_data)
        self.opti.set_value(self.var_q_last, self.init_data)
        self.opti.set_value(self.param_tf_r, self.pose7_to_matrix(right_ee_pose))
        self.opti.set_value(self.param_waist_yaw, float(waist_yaw))

        try:
            self.opti.solve()
            sol_q = self.opti.value(self.var_q)
        except Exception as exc:
            logger_mp.error(f"ERROR in right arm waist IK convergence: {exc}")
            self.last_success = False
            if current_right_arm_q is not None:
                self.init_data[self.right_arm_q_indices] = current_right_arm_q
            self.init_data[self.waist_q_index] = float(waist_yaw)
            return self.init_data[self.right_arm_q_indices].astype(np.float32), float(self.init_data[self.waist_q_index])

        self.last_success = True
        self.smooth_filter.add_data(sol_q)
        sol_q = self.smooth_filter.filtered_data
        sol_q[self.waist_q_index] = float(waist_yaw)
        self.init_data = sol_q
        return sol_q[self.right_arm_q_indices].astype(np.float32), float(sol_q[self.waist_q_index])

    def reset(
        self,
        current_right_arm_q: np.ndarray | list[float] | None = None,
        waist_yaw: float = 0.0,
    ) -> None:
        self.init_data = np.zeros(self.reduced_robot.model.nq)
        self.init_data[self.waist_q_index] = float(waist_yaw)
        if current_right_arm_q is not None:
            current_right_arm_q = np.asarray(current_right_arm_q, dtype=np.float64).reshape(-1)
            if current_right_arm_q.shape[0] != len(self.RIGHT_ARM_JOINT_NAMES):
                raise ValueError(f"Expected current_right_arm_q length 5, got {current_right_arm_q.shape[0]}")
            self.init_data[self.right_arm_q_indices] = current_right_arm_q
        self.smooth_filter = WeightedMovingFilter(np.array([0.4, 0.3, 0.2, 0.1]), self.reduced_robot.model.nq)
        self.last_success = True

    def forward_right_ee_pose(self, right_arm_q: np.ndarray | list[float], waist_yaw: float) -> np.ndarray:
        right_arm_q = np.asarray(right_arm_q, dtype=np.float64).reshape(-1)
        if right_arm_q.shape[0] != len(self.RIGHT_ARM_JOINT_NAMES):
            raise ValueError(f"Expected right_arm_q length 5, got {right_arm_q.shape[0]}")
        q = np.zeros(self.reduced_robot.model.nq)
        q[self.waist_q_index] = float(waist_yaw)
        q[self.right_arm_q_indices] = right_arm_q
        pin.forwardKinematics(self.reduced_robot.model, self.reduced_data, q)
        pin.updateFramePlacements(self.reduced_robot.model, self.reduced_data)
        transform = self.reduced_data.oMf[self.R_hand_id]
        quat_xyzw = pin.Quaternion(transform.rotation).coeffs()
        return np.concatenate([transform.translation, quat_xyzw]).astype(np.float32)


class H1_2_ArmIK:
    def __init__(self, Unit_Test=False, Visualization=False):
        np.set_printoptions(precision=5, suppress=True, linewidth=200)

        self.Unit_Test = Unit_Test
        self.Visualization = Visualization

        if not self.Unit_Test:
            self.robot = pin.RobotWrapper.BuildFromURDF(
                "unitree_lerobot/eval_robot/assets/h1_2/h1_2.urdf", "unitree_lerobot/eval_robot/assets/h1_2/"
            )
        else:
            self.robot = pin.RobotWrapper.BuildFromURDF(
                "unitree_lerobot/eval_robot/assets/h1_2/h1_2.urdf", "unitree_lerobot/eval_robot/assets/h1_2/"
            )  # for test

        self.mixed_jointsToLockIDs = [
            "left_hip_yaw_joint",
            "left_hip_pitch_joint",
            "left_hip_roll_joint",
            "left_knee_joint",
            "left_ankle_pitch_joint",
            "left_ankle_roll_joint",
            "right_hip_yaw_joint",
            "right_hip_pitch_joint",
            "right_hip_roll_joint",
            "right_knee_joint",
            "right_ankle_pitch_joint",
            "right_ankle_roll_joint",
            "torso_joint",
            "L_index_proximal_joint",
            "L_index_intermediate_joint",
            "L_middle_proximal_joint",
            "L_middle_intermediate_joint",
            "L_pinky_proximal_joint",
            "L_pinky_intermediate_joint",
            "L_ring_proximal_joint",
            "L_ring_intermediate_joint",
            "L_thumb_proximal_yaw_joint",
            "L_thumb_proximal_pitch_joint",
            "L_thumb_intermediate_joint",
            "L_thumb_distal_joint",
            "R_index_proximal_joint",
            "R_index_intermediate_joint",
            "R_middle_proximal_joint",
            "R_middle_intermediate_joint",
            "R_pinky_proximal_joint",
            "R_pinky_intermediate_joint",
            "R_ring_proximal_joint",
            "R_ring_intermediate_joint",
            "R_thumb_proximal_yaw_joint",
            "R_thumb_proximal_pitch_joint",
            "R_thumb_intermediate_joint",
            "R_thumb_distal_joint",
        ]

        self.reduced_robot = self.robot.buildReducedRobot(
            list_of_joints_to_lock=self.mixed_jointsToLockIDs,
            reference_configuration=np.array([0.0] * self.robot.model.nq),
        )

        self.reduced_robot.model.addFrame(
            pin.Frame(
                "L_ee",
                self.reduced_robot.model.getJointId("left_wrist_yaw_joint"),
                pin.SE3(np.eye(3), np.array([0.05, 0, 0]).T),
                pin.FrameType.OP_FRAME,
            )
        )

        self.reduced_robot.model.addFrame(
            pin.Frame(
                "R_ee",
                self.reduced_robot.model.getJointId("right_wrist_yaw_joint"),
                pin.SE3(np.eye(3), np.array([0.05, 0, 0]).T),
                pin.FrameType.OP_FRAME,
            )
        )

        # for i in range(self.reduced_robot.model.nframes):
        #     frame = self.reduced_robot.model.frames[i]
        #     frame_id = self.reduced_robot.model.getFrameId(frame.name)
        #     logger_mp.debug(f"Frame ID: {frame_id}, Name: {frame.name}")

        # Creating Casadi models and data for symbolic computing
        self.cmodel = cpin.Model(self.reduced_robot.model)
        self.cdata = self.cmodel.createData()

        # Creating symbolic variables
        self.cq = casadi.SX.sym("q", self.reduced_robot.model.nq, 1)
        self.cTf_l = casadi.SX.sym("tf_l", 4, 4)
        self.cTf_r = casadi.SX.sym("tf_r", 4, 4)
        cpin.framesForwardKinematics(self.cmodel, self.cdata, self.cq)

        # Get the hand joint ID and define the error function
        self.L_hand_id = self.reduced_robot.model.getFrameId("L_ee")
        self.R_hand_id = self.reduced_robot.model.getFrameId("R_ee")

        self.translational_error = casadi.Function(
            "translational_error",
            [self.cq, self.cTf_l, self.cTf_r],
            [
                casadi.vertcat(
                    self.cdata.oMf[self.L_hand_id].translation - self.cTf_l[:3, 3],
                    self.cdata.oMf[self.R_hand_id].translation - self.cTf_r[:3, 3],
                )
            ],
        )
        self.rotational_error = casadi.Function(
            "rotational_error",
            [self.cq, self.cTf_l, self.cTf_r],
            [
                casadi.vertcat(
                    cpin.log3(self.cdata.oMf[self.L_hand_id].rotation @ self.cTf_l[:3, :3].T),
                    cpin.log3(self.cdata.oMf[self.R_hand_id].rotation @ self.cTf_r[:3, :3].T),
                )
            ],
        )

        # Defining the optimization problem
        self.opti = casadi.Opti()
        self.var_q = self.opti.variable(self.reduced_robot.model.nq)
        self.var_q_last = self.opti.parameter(self.reduced_robot.model.nq)  # for smooth
        self.param_tf_l = self.opti.parameter(4, 4)
        self.param_tf_r = self.opti.parameter(4, 4)
        self.translational_cost = casadi.sumsqr(self.translational_error(self.var_q, self.param_tf_l, self.param_tf_r))
        self.rotation_cost = casadi.sumsqr(self.rotational_error(self.var_q, self.param_tf_l, self.param_tf_r))
        self.regularization_cost = casadi.sumsqr(self.var_q)
        self.smooth_cost = casadi.sumsqr(self.var_q - self.var_q_last)

        # Setting optimization constraints and goals
        self.opti.subject_to(
            self.opti.bounded(
                self.reduced_robot.model.lowerPositionLimit, self.var_q, self.reduced_robot.model.upperPositionLimit
            )
        )
        self.opti.minimize(
            50 * self.translational_cost + self.rotation_cost + 0.02 * self.regularization_cost + 0.1 * self.smooth_cost
        )

        opts = {
            "ipopt": {"print_level": 0, "max_iter": 50, "tol": 1e-6},
            "print_time": False,  # print or not
            "calc_lam_p": False,  # https://github.com/casadi/casadi/wiki/FAQ:-Why-am-I-getting-%22NaN-detected%22in-my-optimization%3F
        }
        self.opti.solver("ipopt", opts)

        self.init_data = np.zeros(self.reduced_robot.model.nq)
        self.smooth_filter = WeightedMovingFilter(np.array([0.4, 0.3, 0.2, 0.1]), 14)
        self.vis = None

        if self.Visualization:
            # Initialize the Meshcat visualizer for visualization
            self.vis = MeshcatVisualizer(
                self.reduced_robot.model, self.reduced_robot.collision_model, self.reduced_robot.visual_model
            )
            self.vis.initViewer(open=True)
            self.vis.loadViewerModel("pinocchio")
            self.vis.displayFrames(True, frame_ids=[113, 114], axis_length=0.15, axis_width=5)
            self.vis.display(pin.neutral(self.reduced_robot.model))

            # Enable the display of end effector target frames with short axis lengths and greater width.
            frame_viz_names = ["L_ee_target", "R_ee_target"]
            FRAME_AXIS_POSITIONS = (
                np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 1]]).astype(np.float32).T
            )
            FRAME_AXIS_COLORS = (
                np.array([[1, 0, 0], [1, 0.6, 0], [0, 1, 0], [0.6, 1, 0], [0, 0, 1], [0, 0.6, 1]]).astype(np.float32).T
            )
            axis_length = 0.1
            axis_width = 10
            for frame_viz_name in frame_viz_names:
                self.vis.viewer[frame_viz_name].set_object(
                    mg.LineSegments(
                        mg.PointsGeometry(
                            position=axis_length * FRAME_AXIS_POSITIONS,
                            color=FRAME_AXIS_COLORS,
                        ),
                        mg.LineBasicMaterial(
                            linewidth=axis_width,
                            vertexColors=True,
                        ),
                    )
                )

    # If the robot arm is not the same size as your arm :)
    def scale_arms(self, human_left_pose, human_right_pose, human_arm_length=0.60, robot_arm_length=0.75):
        scale_factor = robot_arm_length / human_arm_length
        robot_left_pose = human_left_pose.copy()
        robot_right_pose = human_right_pose.copy()
        robot_left_pose[:3, 3] *= scale_factor
        robot_right_pose[:3, 3] *= scale_factor
        return robot_left_pose, robot_right_pose

    def solve_ik(self, left_wrist, right_wrist, current_lr_arm_motor_q=None, current_lr_arm_motor_dq=None):
        if current_lr_arm_motor_q is not None:
            self.init_data = current_lr_arm_motor_q
        self.opti.set_initial(self.var_q, self.init_data)

        left_wrist, right_wrist = self.scale_arms(left_wrist, right_wrist)
        if self.Visualization:
            self.vis.viewer["L_ee_target"].set_transform(left_wrist)  # for visualization
            self.vis.viewer["R_ee_target"].set_transform(right_wrist)  # for visualization

        self.opti.set_value(self.param_tf_l, left_wrist)
        self.opti.set_value(self.param_tf_r, right_wrist)
        self.opti.set_value(self.var_q_last, self.init_data)  # for smooth

        try:
            self.opti.solve()
            # sol = self.opti.solve_limited()

            sol_q = self.opti.value(self.var_q)
            self.smooth_filter.add_data(sol_q)
            sol_q = self.smooth_filter.filtered_data

            if current_lr_arm_motor_dq is not None:
                v = current_lr_arm_motor_dq * 0.0
            else:
                v = (sol_q - self.init_data) * 0.0

            self.init_data = sol_q

            sol_tauff = pin.rnea(
                self.reduced_robot.model, self.reduced_robot.data, sol_q, v, np.zeros(self.reduced_robot.model.nv)
            )

            if self.Visualization:
                self.vis.display(sol_q)  # for visualization

            return sol_q, sol_tauff

        except Exception as e:
            logger_mp.error(f"ERROR in convergence, plotting debug info.{e}")

            sol_q = self.opti.debug.value(self.var_q)
            self.smooth_filter.add_data(sol_q)
            sol_q = self.smooth_filter.filtered_data

            if current_lr_arm_motor_dq is not None:
                v = current_lr_arm_motor_dq * 0.0
            else:
                v = (sol_q - self.init_data) * 0.0

            self.init_data = sol_q

            sol_tauff = pin.rnea(
                self.reduced_robot.model, self.reduced_robot.data, sol_q, v, np.zeros(self.reduced_robot.model.nv)
            )

            logger_mp.error(
                f"sol_q:{sol_q} \nmotorstate: \n{current_lr_arm_motor_q} \nleft_pose: \n{left_wrist} \nright_pose: \n{right_wrist}"
            )
            if self.Visualization:
                self.vis.display(sol_q)  # for visualization

            # return sol_q, sol_tauff
            return current_lr_arm_motor_q, np.zeros(self.reduced_robot.model.nv)


class H1_ArmIK:
    def __init__(self, Unit_Test=False, Visualization=False):
        np.set_printoptions(precision=5, suppress=True, linewidth=200)

        self.Unit_Test = Unit_Test
        self.Visualization = Visualization

        if not self.Unit_Test:
            self.robot = pin.RobotWrapper.BuildFromURDF("../assets/h1/h1_with_hand.urdf", "../assets/h1/")
        else:
            self.robot = pin.RobotWrapper.BuildFromURDF(
                "../../assets/h1/h1_with_hand.urdf", "../../assets/h1/"
            )  # for test

        self.mixed_jointsToLockIDs = [
            "right_hip_roll_joint",
            "right_hip_pitch_joint",
            "right_knee_joint",
            "left_hip_roll_joint",
            "left_hip_pitch_joint",
            "left_knee_joint",
            "torso_joint",
            "left_hip_yaw_joint",
            "right_hip_yaw_joint",
            "left_ankle_joint",
            "right_ankle_joint",
            "L_index_proximal_joint",
            "L_index_intermediate_joint",
            "L_middle_proximal_joint",
            "L_middle_intermediate_joint",
            "L_ring_proximal_joint",
            "L_ring_intermediate_joint",
            "L_pinky_proximal_joint",
            "L_pinky_intermediate_joint",
            "L_thumb_proximal_yaw_joint",
            "L_thumb_proximal_pitch_joint",
            "L_thumb_intermediate_joint",
            "L_thumb_distal_joint",
            "R_index_proximal_joint",
            "R_index_intermediate_joint",
            "R_middle_proximal_joint",
            "R_middle_intermediate_joint",
            "R_ring_proximal_joint",
            "R_ring_intermediate_joint",
            "R_pinky_proximal_joint",
            "R_pinky_intermediate_joint",
            "R_thumb_proximal_yaw_joint",
            "R_thumb_proximal_pitch_joint",
            "R_thumb_intermediate_joint",
            "R_thumb_distal_joint",
            "left_hand_joint",
            "right_hand_joint",
        ]

        self.reduced_robot = self.robot.buildReducedRobot(
            list_of_joints_to_lock=self.mixed_jointsToLockIDs,
            reference_configuration=np.array([0.0] * self.robot.model.nq),
        )

        self.reduced_robot.model.addFrame(
            pin.Frame(
                "L_ee",
                self.reduced_robot.model.getJointId("left_elbow_joint"),
                pin.SE3(np.eye(3), np.array([0.2605 + 0.05, 0, 0]).T),
                pin.FrameType.OP_FRAME,
            )
        )

        self.reduced_robot.model.addFrame(
            pin.Frame(
                "R_ee",
                self.reduced_robot.model.getJointId("right_elbow_joint"),
                pin.SE3(np.eye(3), np.array([0.2605 + 0.05, 0, 0]).T),
                pin.FrameType.OP_FRAME,
            )
        )

        # for i in range(self.reduced_robot.model.nframes):
        #     frame = self.reduced_robot.model.frames[i]
        #     frame_id = self.reduced_robot.model.getFrameId(frame.name)
        #     logger_mp.debug(f"Frame ID: {frame_id}, Name: {frame.name}")

        # Creating Casadi models and data for symbolic computing
        self.cmodel = cpin.Model(self.reduced_robot.model)
        self.cdata = self.cmodel.createData()

        # Creating symbolic variables
        self.cq = casadi.SX.sym("q", self.reduced_robot.model.nq, 1)
        self.cTf_l = casadi.SX.sym("tf_l", 4, 4)
        self.cTf_r = casadi.SX.sym("tf_r", 4, 4)
        cpin.framesForwardKinematics(self.cmodel, self.cdata, self.cq)

        # Get the hand joint ID and define the error function
        self.L_hand_id = self.reduced_robot.model.getFrameId("L_ee")
        self.R_hand_id = self.reduced_robot.model.getFrameId("R_ee")

        self.translational_error = casadi.Function(
            "translational_error",
            [self.cq, self.cTf_l, self.cTf_r],
            [
                casadi.vertcat(
                    self.cdata.oMf[self.L_hand_id].translation - self.cTf_l[:3, 3],
                    self.cdata.oMf[self.R_hand_id].translation - self.cTf_r[:3, 3],
                )
            ],
        )
        self.rotational_error = casadi.Function(
            "rotational_error",
            [self.cq, self.cTf_l, self.cTf_r],
            [
                casadi.vertcat(
                    cpin.log3(self.cdata.oMf[self.L_hand_id].rotation @ self.cTf_l[:3, :3].T),
                    cpin.log3(self.cdata.oMf[self.R_hand_id].rotation @ self.cTf_r[:3, :3].T),
                )
            ],
        )

        # Defining the optimization problem
        self.opti = casadi.Opti()
        self.var_q = self.opti.variable(self.reduced_robot.model.nq)
        self.var_q_last = self.opti.parameter(self.reduced_robot.model.nq)  # for smooth
        self.param_tf_l = self.opti.parameter(4, 4)
        self.param_tf_r = self.opti.parameter(4, 4)
        self.translational_cost = casadi.sumsqr(self.translational_error(self.var_q, self.param_tf_l, self.param_tf_r))
        self.rotation_cost = casadi.sumsqr(self.rotational_error(self.var_q, self.param_tf_l, self.param_tf_r))
        self.regularization_cost = casadi.sumsqr(self.var_q)
        self.smooth_cost = casadi.sumsqr(self.var_q - self.var_q_last)

        # Setting optimization constraints and goals
        self.opti.subject_to(
            self.opti.bounded(
                self.reduced_robot.model.lowerPositionLimit, self.var_q, self.reduced_robot.model.upperPositionLimit
            )
        )
        self.opti.minimize(
            50 * self.translational_cost
            + 0.5 * self.rotation_cost
            + 0.02 * self.regularization_cost
            + 0.1 * self.smooth_cost
        )

        opts = {
            "ipopt": {"print_level": 0, "max_iter": 50, "tol": 1e-6},
            "print_time": False,  # print or not
            "calc_lam_p": False,  # https://github.com/casadi/casadi/wiki/FAQ:-Why-am-I-getting-%22NaN-detected%22in-my-optimization%3F
        }
        self.opti.solver("ipopt", opts)

        self.init_data = np.zeros(self.reduced_robot.model.nq)
        self.smooth_filter = WeightedMovingFilter(np.array([0.4, 0.3, 0.2, 0.1]), 8)
        self.vis = None

        if self.Visualization:
            # Initialize the Meshcat visualizer for visualization
            self.vis = MeshcatVisualizer(
                self.reduced_robot.model, self.reduced_robot.collision_model, self.reduced_robot.visual_model
            )
            self.vis.initViewer(open=True)
            self.vis.loadViewerModel("pinocchio")
            self.vis.displayFrames(True, frame_ids=[105, 106], axis_length=0.15, axis_width=5)
            self.vis.display(pin.neutral(self.reduced_robot.model))

            # Enable the display of end effector target frames with short axis lengths and greater width.
            frame_viz_names = ["L_ee_target", "R_ee_target"]
            FRAME_AXIS_POSITIONS = (
                np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 1]]).astype(np.float32).T
            )
            FRAME_AXIS_COLORS = (
                np.array(
                    [
                        [1.0, 0.3, 0.3],
                        [1.0, 0.7, 0.7],
                        [0.3, 1.0, 0.5],
                        [0.7, 1.0, 0.8],
                        [0.3, 0.8, 1.0],
                        [0.7, 0.9, 1.0],
                    ]
                )
                .astype(np.float32)
                .T
            )
            axis_length = 0.1
            axis_width = 10
            for frame_viz_name in frame_viz_names:
                self.vis.viewer[frame_viz_name].set_object(
                    mg.LineSegments(
                        mg.PointsGeometry(
                            position=axis_length * FRAME_AXIS_POSITIONS,
                            color=FRAME_AXIS_COLORS,
                        ),
                        mg.LineBasicMaterial(
                            linewidth=axis_width,
                            vertexColors=True,
                        ),
                    )
                )

    # If the robot arm is not the same size as your arm :)
    def scale_arms(self, human_left_pose, human_right_pose, human_arm_length=0.60, robot_arm_length=0.75):
        scale_factor = robot_arm_length / human_arm_length
        robot_left_pose = human_left_pose.copy()
        robot_right_pose = human_right_pose.copy()
        robot_left_pose[:3, 3] *= scale_factor
        robot_right_pose[:3, 3] *= scale_factor
        return robot_left_pose, robot_right_pose

    def solve_ik(self, left_wrist, right_wrist, current_lr_arm_motor_q=None, current_lr_arm_motor_dq=None):
        if current_lr_arm_motor_q is not None:
            self.init_data = current_lr_arm_motor_q
        self.opti.set_initial(self.var_q, self.init_data)

        left_wrist, right_wrist = self.scale_arms(left_wrist, right_wrist)
        if self.Visualization:
            self.vis.viewer["L_ee_target"].set_transform(left_wrist)  # for visualization
            self.vis.viewer["R_ee_target"].set_transform(right_wrist)  # for visualization

        self.opti.set_value(self.param_tf_l, left_wrist)
        self.opti.set_value(self.param_tf_r, right_wrist)
        self.opti.set_value(self.var_q_last, self.init_data)  # for smooth

        try:
            self.opti.solve()
            # sol = self.opti.solve_limited()

            sol_q = self.opti.value(self.var_q)
            self.smooth_filter.add_data(sol_q)
            sol_q = self.smooth_filter.filtered_data

            if current_lr_arm_motor_dq is not None:
                v = current_lr_arm_motor_dq * 0.0
            else:
                v = (sol_q - self.init_data) * 0.0

            self.init_data = sol_q

            sol_tauff = pin.rnea(
                self.reduced_robot.model, self.reduced_robot.data, sol_q, v, np.zeros(self.reduced_robot.model.nv)
            )

            if self.Visualization:
                self.vis.display(sol_q)  # for visualization

            return sol_q, sol_tauff

        except Exception as e:
            logger_mp.error(f"ERROR in convergence, plotting debug info.{e}")

            sol_q = self.opti.debug.value(self.var_q)
            self.smooth_filter.add_data(sol_q)
            sol_q = self.smooth_filter.filtered_data

            if current_lr_arm_motor_dq is not None:
                v = current_lr_arm_motor_dq * 0.0
            else:
                v = (sol_q - self.init_data) * 0.0

            self.init_data = sol_q

            sol_tauff = pin.rnea(
                self.reduced_robot.model, self.reduced_robot.data, sol_q, v, np.zeros(self.reduced_robot.model.nv)
            )

            logger_mp.error(
                f"sol_q:{sol_q} \nmotorstate: \n{current_lr_arm_motor_q} \nleft_pose: \n{left_wrist} \nright_pose: \n{right_wrist}"
            )
            if self.Visualization:
                self.vis.display(sol_q)  # for visualization

            # return sol_q, sol_tauff
            return current_lr_arm_motor_q, np.zeros(self.reduced_robot.model.nv)


if __name__ == "__main__":
    arm_ik = G1_29_ArmIK(Unit_Test=True, Visualization=True)
    # arm_ik = H1_2_ArmIK(Unit_Test = True, Visualization = True)
    # arm_ik = G1_23_ArmIK(Unit_Test = True, Visualization = True)
    # arm_ik = H1_ArmIK(Unit_Test = True, Visualization = True)

    # initial position
    L_tf_target = pin.SE3(
        pin.Quaternion(1, 0, 0, 0),
        np.array([0.25, +0.25, 0.1]),
    )

    R_tf_target = pin.SE3(
        pin.Quaternion(1, 0, 0, 0),
        np.array([0.25, -0.25, 0.1]),
    )

    rotation_speed = 0.005
    noise_amplitude_translation = 0.001
    noise_amplitude_rotation = 0.01

    user_input = input("Please enter the start signal (enter 's' to start the subsequent program):\n")
    if user_input.lower() == "s":
        step = 0
        while True:
            # Apply rotation noise with bias towards y and z axes
            rotation_noise_L = pin.Quaternion(
                np.cos(np.random.normal(0, noise_amplitude_rotation) / 2),
                0,
                np.random.normal(0, noise_amplitude_rotation / 2),
                0,
            ).normalized()  # y bias

            rotation_noise_R = pin.Quaternion(
                np.cos(np.random.normal(0, noise_amplitude_rotation) / 2),
                0,
                0,
                np.random.normal(0, noise_amplitude_rotation / 2),
            ).normalized()  # z bias

            if step <= 120:
                angle = rotation_speed * step
                L_tf_target.rotation = (
                    rotation_noise_L * pin.Quaternion(np.cos(angle / 2), 0, np.sin(angle / 2), 0)
                ).toRotationMatrix()  # y axis
                R_tf_target.rotation = (
                    rotation_noise_R * pin.Quaternion(np.cos(angle / 2), 0, 0, np.sin(angle / 2))
                ).toRotationMatrix()  # z axis
                L_tf_target.translation += np.array([0.001, 0.001, 0.001]) + np.random.normal(
                    0, noise_amplitude_translation, 3
                )
                R_tf_target.translation += np.array([0.001, -0.001, 0.001]) + np.random.normal(
                    0, noise_amplitude_translation, 3
                )
            else:
                angle = rotation_speed * (240 - step)
                L_tf_target.rotation = (
                    rotation_noise_L * pin.Quaternion(np.cos(angle / 2), 0, np.sin(angle / 2), 0)
                ).toRotationMatrix()  # y axis
                R_tf_target.rotation = (
                    rotation_noise_R * pin.Quaternion(np.cos(angle / 2), 0, 0, np.sin(angle / 2))
                ).toRotationMatrix()  # z axis
                L_tf_target.translation -= np.array([0.001, 0.001, 0.001]) + np.random.normal(
                    0, noise_amplitude_translation, 3
                )
                R_tf_target.translation -= np.array([0.001, -0.001, 0.001]) + np.random.normal(
                    0, noise_amplitude_translation, 3
                )

            arm_ik.solve_ik(L_tf_target.homogeneous, R_tf_target.homogeneous)

            step += 1
            if step > 240:
                step = 0
            time.sleep(0.1)
