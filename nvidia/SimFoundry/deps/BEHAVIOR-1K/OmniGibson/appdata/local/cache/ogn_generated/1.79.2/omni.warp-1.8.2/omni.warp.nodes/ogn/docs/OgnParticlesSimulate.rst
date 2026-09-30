.. _omni_warp_WarpParticlesSimulate_1:

.. _omni_warp_WarpParticlesSimulate:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Particles Simulate (Deprecated)
    :keywords: lang-en omnigraph node warp warp warp-particles-simulate


Particles Simulate (Deprecated)
===============================

.. <description>

Simulates particles.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Collider (*inputs:collider*)", "``bundle``", "Collider geometry mesh.", "None"
    "Collider Contact Distance (*inputs:colliderContactDistance*)", "``float``", "Distance to maintain from the collider's surface.", "1"
    "", "Metadata", "*min* = 0.0", ""
    "Collider Contact Query Range (*inputs:colliderContactQueryRange*)", "``float``", "Distance to start probing for contacts with the collider's surface. Multiple of the collider contact distance.", "100.0"
    "", "Metadata", "*min* = 1.0", ""
    "Contact Damping Stiffness (*inputs:contactDampingStiffness*)", "``float``", "Contact damping stiffness. Multiple of the global scale value.", "1.0"
    "", "Metadata", "*min* = 0.0", ""
    "Contact Elastic Stiffness (*inputs:contactElasticStiffness*)", "``float``", "Contact elastic stiffness. Multiple of the global scale value.", "100.0"
    "", "Metadata", "*min* = 0.0", ""
    "Contact Friction Coeff (*inputs:contactFrictionCoeff*)", "``float``", "Contact coefficient of friction.", "0.75"
    "", "Metadata", "*min* = 0.0", ""
    "Contact Friction Stiffness (*inputs:contactFrictionStiffness*)", "``float``", "Contact friction stiffness. Multiple of the global scale value.", "1.0"
    "", "Metadata", "*min* = 0.0", ""
    "Enabled (*inputs:enabled*)", "``bool``", "Whether to enable the simulation.", "True"
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "Global Scale (*inputs:globalScale*)", "``float``", "Global scale value for the simulation attributes.", "100.0"
    "", "Metadata", "*min* = 0.0", ""
    "Gravity (*inputs:gravity*)", "``vectorf[3]``", "Gravity force.", "[0.0, -980, 0.0]"
    "Ground Altitude (*inputs:groundAltitude*)", "``float``", "Position of the ground on the Y axis.", "0.0"
    "Ground Enabled (*inputs:groundEnabled*)", "``bool``", "Whether to add a ground collider.", "True"
    "Particles (*inputs:particles*)", "``bundle``", "Particles to simulate.", "None"
    "Particles Contact Adhesion (*inputs:particlesContactAdhesion*)", "``float``", "Contact coefficient of adhesion.", "0.25"
    "", "Metadata", "*min* = 0.0", ""
    "Particles Contact Cohesion (*inputs:particlesContactCohesion*)", "``float``", "Contact coefficient of cohesion.", "0.1"
    "", "Metadata", "*min* = 0.0", ""
    "Particles Query Range (*inputs:particlesQueryRange*)", "``float``", "Amount to expand the grid cell size to accommodate caching neighbours between steps. Multiple of the largest particle radius.", "2.0"
    "", "Metadata", "*min* = 1.0", ""
    "Substep Count (*inputs:substepCount*)", "``int``", "Number of substeps.", "32"
    "Time (*inputs:time*)", "``double``", "Time.", "0.0"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Exec Out (*outputs:execOut*)", "``execution``", "Output execution.", "None"
    "Particles (*outputs:particles*)", "``bundle``", "Output particles geometry.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.warp.WarpParticlesSimulate"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "hidden", "true"
    "uiName", "Particles Simulate (Deprecated)"
    "Categories", "warp"
    "Generated Class Name", "OgnParticlesSimulateDatabase"
    "Python Module", "omni.warp.nodes"

