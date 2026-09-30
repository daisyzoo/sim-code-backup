.. _omni_warp_WarpClothSimulate_1:

.. _omni_warp_WarpClothSimulate:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Cloth Simulate (Deprecated)
    :keywords: lang-en omnigraph node warp warp warp-cloth-simulate


Cloth Simulate (Deprecated)
===========================

.. <description>

Simulates cloth.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Cloth (*inputs:cloth*)", "``bundle``", "Cloth to simulate.", "None"
    "Cloth Density (*inputs:clothDensity*)", "``float``", "Cloth density.", "0.1"
    "", "Metadata", "*min* = 0.0", ""
    "Cloth Edge Bending Stiffness (*inputs:clothEdgeBendingStiffness*)", "``float``", "Edge bending stiffness. Multiple of the global scale value.", "0.01"
    "", "Metadata", "*min* = 0.0", ""
    "Cloth Edge Damping Stiffness (*inputs:clothEdgeDampingStiffness*)", "``float``", "Edge damping stiffness. Multiple of the global scale value.", "1e-05"
    "", "Metadata", "*min* = 0.0", ""
    "Cloth Triangle Area Stiffness (*inputs:clothTriAreaStiffness*)", "``float``", "Triangle area stiffness. Multiple of the global scale value.", "100000.0"
    "", "Metadata", "*min* = 0.0", ""
    "Cloth Triangle Damping Stiffness (*inputs:clothTriDampingStiffness*)", "``float``", "Triangle damping stiffness. Multiple of the global scale value.", "1e-05"
    "", "Metadata", "*min* = 0.0", ""
    "Cloth Triangle Drag (*inputs:clothTriDrag*)", "``float``", "Triangle drag force. Multiple of the global scale value.", "0.0"
    "", "Metadata", "*min* = 0.0", ""
    "Cloth Triangle Elastic Stiffness (*inputs:clothTriElasticStiffness*)", "``float``", "Triangle elastic stiffness. Multiple of the global scale value.", "100000.0"
    "", "Metadata", "*min* = 0.0", ""
    "Cloth Triangle Lift (*inputs:clothTriLift*)", "``float``", "Triangle lift force. Multiple of the global scale value.", "0.0"
    "", "Metadata", "*min* = 0.0", ""
    "Collider (*inputs:collider*)", "``bundle``", "Collider geometry mesh.", "None"
    "Collider Contact Distance (*inputs:colliderContactDistance*)", "``float``", "Distance to maintain from the collider's surface.", "5.0"
    "", "Metadata", "*min* = 0.0", ""
    "Collider Contact Query Range (*inputs:colliderContactQueryRange*)", "``float``", "Distance to start probing for contacts with the collider's surface. Multiple of the collider contact distance.", "10.0"
    "", "Metadata", "*min* = 1.0", ""
    "Contact Damping Stiffness (*inputs:contactDampingStiffness*)", "``float``", "Contact damping stiffness. Multiple of the global scale value.", "10000.0"
    "", "Metadata", "*min* = 0.0", ""
    "Contact Elastic Stiffness (*inputs:contactElasticStiffness*)", "``float``", "Contact elastic stiffness. Multiple of the global scale value.", "100000.0"
    "", "Metadata", "*min* = 0.0", ""
    "Contact Friction Coeff (*inputs:contactFrictionCoeff*)", "``float``", "Contact coefficient of friction.", "0.75"
    "", "Metadata", "*min* = 0.0", ""
    "Contact Friction Stiffness (*inputs:contactFrictionStiffness*)", "``float``", "Contact friction stiffness. Multiple of the global scale value.", "10000.0"
    "", "Metadata", "*min* = 0.0", ""
    "Enabled (*inputs:enabled*)", "``bool``", "Whether to enable the simulation.", "True"
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "Gravity (*inputs:gravity*)", "``vectorf[3]``", "Gravity force.", "[0.0, -980, 0.0]"
    "Ground Altitude (*inputs:groundAltitude*)", "``float``", "Position of the ground on the Y axis.", "0.0"
    "Ground Enabled (*inputs:groundEnabled*)", "``bool``", "Whether to add a ground collider.", "True"
    "Spring Damping Stiffness (*inputs:springDampingStiffness*)", "``float``", "Spring elastic stiffness. Multiple of the global scale value.", "1.0"
    "", "Metadata", "*min* = 0.0", ""
    "Spring Elastic Stiffness (*inputs:springElasticStiffness*)", "``float``", "Spring elastic stiffness. Multiple of the global scale value.", "1000.0"
    "", "Metadata", "*min* = 0.0", ""
    "Spring Index Pairs (*inputs:springIndexPairs*)", "``int[2][]``", "Vertex indices where each pair represents a spring constraint.", "[]"
    "Spring Visualize (*inputs:springVisualize*)", "``bool``", "Whether to visualize the spring constraints.", "False"
    "Spring Visualize Color (*inputs:springVisualizeColor*)", "``colorf[3]``", "Visualization colour for the spring constraints.", "[10.0, 10.0, 0.0]"
    "Spring Visualize Width (*inputs:springVisualizeWidth*)", "``float``", "Visualization width for the spring constraints.", "0.5"
    "Substep Count (*inputs:substepCount*)", "``int``", "Number of substeps.", "32"
    "Time (*inputs:time*)", "``double``", "Time.", "0.0"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Cloth (*outputs:cloth*)", "``bundle``", "Output particles geometry.", "None"
    "Exec Out (*outputs:execOut*)", "``execution``", "Output execution.", "None"
    "Visualization (*outputs:visualization*)", "``bundle``", "Output visualization.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.warp.WarpClothSimulate"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "hidden", "true"
    "uiName", "Cloth Simulate (Deprecated)"
    "Categories", "warp"
    "Generated Class Name", "OgnClothSimulateDatabase"
    "Python Module", "omni.warp.nodes"

