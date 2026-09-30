.. _omni_warp_WarpParticlesFromMesh_1:

.. _omni_warp_WarpParticlesFromMesh:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Particles From Mesh
    :keywords: lang-en omnigraph node warp warp warp-particles-from-mesh


Particles From Mesh
===================

.. <description>

Generates particles inside a mesh.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "Mass (*inputs:mass*)", "``float``", "Particles mass.", "1.0"
    "", "Metadata", "*min* = 0.0", ""
    "Max Points (*inputs:maxPoints*)", "``int``", "Maximum number of points to generate.", "1000000"
    "", "Metadata", "*min* = 0", ""
    "Max SDF (*inputs:maxSdf*)", "``float``", "Maximum SDF value to consider.", "0.0"
    "Mesh (*inputs:mesh*)", "``bundle``", "Mesh.", "None"
    "Min SDF (*inputs:minSdf*)", "``float``", "Minimum SDF value to consider.", "-100.0"
    "Radius (*inputs:radius*)", "``float``", "Particles radius.", "1.0"
    "", "Metadata", "*min* = 0.0", ""
    "Seed (*inputs:seed*)", "``int``", "Seed for the random number generator.", "0"
    "Spacing (*inputs:spacing*)", "``float``", "Particles spacing.", "4.0"
    "", "Metadata", "*min* = 0.0", ""
    "Spacing Jitter (*inputs:spacingJitter*)", "``float``", "Amount by which to randomize the spacing between each particle.", "0.0"
    "", "Metadata", "*min* = 0.0", ""
    "Transform (*inputs:transform*)", "``matrixd[4]``", "World transformation to store alongside the output geometry.", "[[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]"
    "Velocity Amount (*inputs:velocityAmount*)", "``float``", "Amount for the velocity.", "0.0"
    "", "Metadata", "*min* = 0.0", ""
    "Velocity Dir (*inputs:velocityDir*)", "``vectorf[3]``", "Direction for the velocity, in the input mesh's object space.", "[0.0, 0.0, 1.0]"


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

    "Unique ID", "omni.warp.WarpParticlesFromMesh"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Particles From Mesh"
    "Categories", "warp"
    "Generated Class Name", "OgnParticlesFromMeshDatabase"
    "Python Module", "omni.warp.nodes"

