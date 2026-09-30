.. _isaacsim_robot_wheeled_robots_DifferentialController_1:

.. _isaacsim_robot_wheeled_robots_DifferentialController:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Differential Controller
    :keywords: lang-en omnigraph node isaacWheeledRobots wheeled_robots differential-controller


Differential Controller
=======================

.. <description>

Differential Controller

.. </description>


Installation
------------

To use this node enable :ref:`isaacsim.robot.wheeled_robots<ext_isaacsim_robot_wheeled_robots>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Desired Angular Velocity (*inputs:angularVelocity*)", "``double``", "Desired rotation velocity in rad/s", "0.0"
    "Dt (*inputs:dt*)", "``double``", "Delta time in seconds", "0.0"
    "Exec In (*inputs:execIn*)", "``execution``", "The input execution", "None"
    "Desired Linear Velocity (*inputs:linearVelocity*)", "``double``", "Desired linear velocity in m/s", "0.0"
    "Max Acceleration (*inputs:maxAcceleration*)", "``double``", "Maximum linear acceleration of the robot for forward and reverse in m/s^2, 0.0 means not set", "0.0"
    "Max Angular Acceleration (*inputs:maxAngularAcceleration*)", "``double``", "Maximum angular acceleration of the robot in rad/s^2, 0.0 means not set", "0.0"
    "Max Angular Speed (*inputs:maxAngularSpeed*)", "``double``", "Max angular speed allowed for vehicle in rad/s, 0.0 means not set", "0.0"
    "Max Deceleration (*inputs:maxDeceleration*)", "``double``", "Maximum linear braking of the robot in m/s^2, 0.0 means not set.", "0.0"
    "Max Linear Speed (*inputs:maxLinearSpeed*)", "``double``", "Max linear speed allowed for vehicle in m/s, 0.0 means not set", "0.0"
    "Max Wheel Speed (*inputs:maxWheelSpeed*)", "``double``", "Max wheel speed allowed in rad/s, 0.0 means not set", "0.0"
    "Wheel Distance (*inputs:wheelDistance*)", "``double``", "Distance between the two wheels in meters", "0.0"
    "Wheel Radius (*inputs:wheelRadius*)", "``double``", "Radius of the wheels in meters", "0.0"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Velocity Command (*outputs:velocityCommand*)", "``double[]``", "Velocity commands Units:     linear (m/s)     angular (rad/s)", "[0.0, 0.0]"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "isaacsim.robot.wheeled_robots.DifferentialController"
    "Version", "1"
    "Extension", "isaacsim.robot.wheeled_robots"
    "Icon", "/home/user/Documents/zoo/sim/nvidia/SimFoundry/deps/BEHAVIOR-1K/OmniGibson/appdata/local/cache/ogn_generated/1.79.2/isaacsim.robot.wheeled_robots-4.0.24/isaacsim.robot.wheeled_robots/ogn/icons/isaacsim.robot.wheeled_robots.DifferentialController.svg"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "None"
    "uiName", "Differential Controller"
    "Categories", "isaacWheeledRobots"
    "Generated Class Name", "OgnDifferentialControllerDatabase"
    "Python Module", "isaacsim.robot.wheeled_robots"

