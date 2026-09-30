.. _omni_warp_WarpSampleOceanDeform_1:

.. _omni_warp_WarpSampleOceanDeform:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Ocean Deform
    :keywords: lang-en omnigraph node warp warp warp-sample-ocean-deform


Ocean Deform
============

.. <description>

Mesh deformer modeling ocean waves.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Amplitude (*inputs:amplitude*)", "``float``", "Wave amplitude factor.", "1.0"
    "Camera Position (*inputs:cameraPos*)", "``vectorf[3]``", "Camera position to use to move the clipmap.", "[0.0, 0.0, 0.0]"
    "Clipmap Cell Size (*inputs:clipmapCellSize*)", "``float``", "Size of a single cell at the centre of the clipmap grid.", "1.0"
    "Direction (*inputs:direction*)", "``float``", "Wave direction.", "0"
    "Directionality (*inputs:directionality*)", "``float``", "Isotropic vs directional wave motion", "0"
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "Mesh (*inputs:mesh*)", "``bundle``", "Input mesh geometry.", "None"
    "Horizontal Scale (*inputs:scale*)", "``float``", "Horizontal wave scaling, can be used to match scene units.", "1.0"
    "Time (*inputs:time*)", "``double``", "Time.", "0"
    "Water Depth (*inputs:waterDepth*)", "``float``", "Water depth (1..1000 m).", "50.0"
    "Wind Speed (*inputs:windSpeed*)", "``float``", "Wind speed (m/s) 10m above ocean (0..30).", "10.0"


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

    "Unique ID", "omni.warp.WarpSampleOceanDeform"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Ocean Deform"
    "Categories", "warp"
    "Generated Class Name", "OgnSampleOceanDeformDatabase"
    "Python Module", "omni.warp.nodes"

