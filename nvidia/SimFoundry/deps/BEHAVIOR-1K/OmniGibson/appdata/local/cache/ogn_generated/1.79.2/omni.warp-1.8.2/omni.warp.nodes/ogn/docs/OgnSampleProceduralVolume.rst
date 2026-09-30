.. _omni_warp_WarpSampleProceduralVolume_1:

.. _omni_warp_WarpSampleProceduralVolume:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Sample Procedural Volume
    :keywords: lang-en omnigraph node warp,warp:samples warp warp-sample-procedural-volume


Sample Procedural Volume
========================

.. <description>

Generates a procedural volume.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Dim (*inputs:dim*)", "``int``", "Dimension for each side of the volume.", "64"
    "", "Metadata", "*minimum* = 1", ""
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "Smooth Min Radius (*inputs:smoothMinRadius*)", "``float``", "Smoothness radius used to blend SDF volumes.", "1"
    "", "Metadata", "*minimum* = 0", ""
    "Time (*inputs:time*)", "``double``", "Time.", "0.0"
    "Torus Altitude (*inputs:torusAltitude*)", "``float``", "Normalized position of the torus on the Y-axis.", "-0.5"
    "", "Metadata", "*minimum* = -1", ""
    "", "Metadata", "*maximum* = 1", ""
    "Torus Major Radius (*inputs:torusMajorRadius*)", "``float``", "Normalized distance from the centre of the torus to the centre of the tube.", "0.75"
    "", "Metadata", "*minimum* = 0", ""
    "", "Metadata", "*maximum* = 1", ""
    "Torus Minor Radius (*inputs:torusMinorRadius*)", "``float``", "Normalized radius of the tube.", "0.1"
    "", "Metadata", "*minimum* = 0", ""
    "", "Metadata", "*maximum* = 1", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Data (*outputs:data*)", "``float[]``", "Output volume data.", "None"
    "Exec Out (*outputs:execOut*)", "``execution``", "Output execution.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.warp.WarpSampleProceduralVolume"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Sample Procedural Volume"
    "Categories", "warp,warp:samples"
    "Generated Class Name", "OgnSampleProceduralVolumeDatabase"
    "Python Module", "omni.warp.nodes"

