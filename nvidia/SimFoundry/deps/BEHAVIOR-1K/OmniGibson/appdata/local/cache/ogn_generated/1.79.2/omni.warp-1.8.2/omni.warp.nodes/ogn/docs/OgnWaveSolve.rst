.. _omni_warp_WarpWaveSolve_1:

.. _omni_warp_WarpWaveSolve:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Wave Solve
    :keywords: lang-en omnigraph node warp warp warp-wave-solve


Wave Solve
==========

.. <description>

Creates a grid geometry simulated with a wave equation solver.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Amplitude (*inputs:amplitude*)", "``float``", "Displacement amplitude.", "1.0"
    "Cell Size (*inputs:cellSize*)", "``float``", "Cell size for the grid.", "1.0"
    "", "Metadata", "*minimum* = 0.0", ""
    "Collider (*inputs:collider*)", "``bundle``", "Collider.", "None"
    "Damping (*inputs:damping*)", "``float``", "Simulation damping.", "0.25"
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "Size (*inputs:size*)", "``float[2]``", "Grid's size.", "[100.0, 100.0]"
    "", "Metadata", "*minimum* = 0.0,0.0", ""
    "Speed (*inputs:speed*)", "``float``", "Simulation speed.", "100.0"
    "Time (*inputs:time*)", "``double``", "Time.", "0.0"
    "Transform (*inputs:transform*)", "``matrixd[4]``", "World transformation to store alongside the output geometry.", "[[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Exec Out (*outputs:execOut*)", "``execution``", "Output execution.", "None"
    "Mesh (*outputs:mesh*)", "``bundle``", "Output mesh geometry.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.warp.WarpWaveSolve"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Wave Solve"
    "Categories", "warp"
    "Generated Class Name", "OgnWaveSolveDatabase"
    "Python Module", "omni.warp.nodes"

