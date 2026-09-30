.. _omni_warp_WarpGridCreate_1:

.. _omni_warp_WarpGridCreate:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Grid Create
    :keywords: lang-en omnigraph node warp warp warp-grid-create


Grid Create
===========

.. <description>

Creates a geometry mesh grid.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Dims (*inputs:dims*)", "``int[2]``", "Dimensions for each side of the grid.", "[1, 1]"
    "", "Metadata", "*minimum* = 1,1", ""
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "Size (*inputs:size*)", "``float[2]``", "Geometry's size.", "[100.0, 100.0]"
    "", "Metadata", "*minimum* = 0.0,0.0", ""
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

    "Unique ID", "omni.warp.WarpGridCreate"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Grid Create"
    "Categories", "warp"
    "Generated Class Name", "OgnGridCreateDatabase"
    "Python Module", "omni.warp.nodes"

