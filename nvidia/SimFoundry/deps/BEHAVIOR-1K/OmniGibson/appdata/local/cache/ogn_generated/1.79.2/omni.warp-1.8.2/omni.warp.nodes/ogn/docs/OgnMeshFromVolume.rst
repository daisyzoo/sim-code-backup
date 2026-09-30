.. _omni_warp_WarpMeshFromVolume_1:

.. _omni_warp_WarpMeshFromVolume:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Mesh From Volume
    :keywords: lang-en omnigraph node warp warp warp-mesh-from-volume


Mesh From Volume
================

.. <description>

Converts a volume into a mesh.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Data (*inputs:data*)", "``float[]``", "Volume data.", "[]"
    "Dim 1 (*inputs:dim1*)", "``int``", "Size of the first texture dimension.", "64"
    "", "Metadata", "*minimum* = 1", ""
    "Dim 2 (*inputs:dim2*)", "``int``", "Size of the second texture dimension.", "64"
    "", "Metadata", "*minimum* = 1", ""
    "Dim 3 (*inputs:dim3*)", "``int``", "Size of the third texture dimension.", "64"
    "", "Metadata", "*minimum* = 1", ""
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "Max Points (*inputs:maxPoints*)", "``int``", "Maximum number of points to generate.", "1000000"
    "Max Triangles (*inputs:maxTriangles*)", "``int``", "Maximum number of triangles to generate.", "1000000"
    "Size (*inputs:size*)", "``float[3]``", "Geometry's size.", "[100.0, 100.0, 100.0]"
    "", "Metadata", "*minimum* = 0.0,0.0,0.0", ""
    "Threshold (*inputs:threshold*)", "``float``", "ISO value that is considered as being the surface.", "0.0"
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

    "Unique ID", "omni.warp.WarpMeshFromVolume"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Mesh From Volume"
    "Categories", "warp"
    "Generated Class Name", "OgnMeshFromVolumeDatabase"
    "Python Module", "omni.warp.nodes"

