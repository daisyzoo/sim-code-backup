.. _omni_warp_WarpTextureWrite_1:

.. _omni_warp_WarpTextureWrite:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Texture Write
    :keywords: lang-en omnigraph node warp warp warp-texture-write


Texture Write
=============

.. <description>

Writes a texture.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Data (*inputs:data*)", "``colorf[4][]``", "Texture data.", "[]"
    "Dim 1 (*inputs:dim1*)", "``int``", "Size of the first texture dimension.", "128"
    "", "Metadata", "*minimum* = 0", ""
    "Dim 2 (*inputs:dim2*)", "``int``", "Size of the second texture dimension.", "128"
    "", "Metadata", "*minimum* = 0", ""
    "Dim 3 (*inputs:dim3*)", "``int``", "Size of the third texture dimension.", "128"
    "", "Metadata", "*minimum* = 0", ""
    "Dim 4 (*inputs:dim4*)", "``int``", "Size of the fourth texture dimension.", "1"
    "", "Metadata", "*minimum* = 0", ""
    "Dim Count (*inputs:dimCount*)", "``int``", "Number of texture dimensions.", "2"
    "", "Metadata", "*minimum* = 1", ""
    "", "Metadata", "*maximum* = 4", ""
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "URI (*inputs:uri*)", "``string``", "URI of the texture to write to.", "dynamic://"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Exec Out (*outputs:execOut*)", "``execution``", "Output execution.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.warp.WarpTextureWrite"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Texture Write"
    "Categories", "warp"
    "Generated Class Name", "OgnTextureWriteDatabase"
    "Python Module", "omni.warp.nodes"

