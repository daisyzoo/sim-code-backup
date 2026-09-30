.. _omni_warp_WarpNoiseDeform_1:

.. _omni_warp_WarpNoiseDeform:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Noise Deform
    :keywords: lang-en omnigraph node warp warp warp-noise-deform


Noise Deform
============

.. <description>

Deforms points using a noise.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Amplitude (*inputs:amplitude*)", "``float``", "Amplitude of the deformation.", "10.0"
    "Axis Amplitude (*inputs:axisAmplitude*)", "``float[3]``", "Amplitude of the deformation along the different axis.", "[1.0, 1.0, 1.0]"
    "Base (*inputs:base*)", "``float``", "Base location of the deformation along the given axis. Below this value, points won't be deformed, which for example helps rooting the base of an asset onto the ground.", "0.0"
    "Cell Size (*inputs:cellSize*)", "``float``", "Cell size of the noise.", "100.0"
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"
    "Falloff (*inputs:falloff*)", "``float``", "Distance falloff of the deformation starting from the given base value. Beyond this value, points will be fully deformed.", "0.0"
    "Function (*inputs:func*)", "``token``", "Noise function.", "perlin"
    "", "Metadata", "*allowedTokens* = perlin,curl", ""
    "Mode (*inputs:mode*)", "``token``", "Allows to apply the noise only on a partial subset of the geometries, as described by the upAxis, base, and falloff attributes.", "global"
    "", "Metadata", "*allowedTokens* = global,partial", ""
    "Primitives (*inputs:prims*)", "``bundle``", "Primitives.", "None"
    "Seed (*inputs:seed*)", "``int``", "Seed used to generate the noise.", "0"
    "Speed (*inputs:speed*)", "``float``", "Speed of the animated noise.", "1.0"
    "Time (*inputs:time*)", "``double``", "Time.", "0.0"
    "Up Axis (*inputs:upAxis*)", "``token``", "Axis along which the base and falloff attributes are defined in. This must be expressed in the local space of the points being deformed.", "+Y"
    "", "Metadata", "*allowedTokens* = +X,+Y,+Z,-X,-Y,-Z", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Exec Out (*outputs:execOut*)", "``execution``", "Output execution.", "None"
    "Primitives (*outputs:prims*)", "``bundle``", "Primitives.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.warp.WarpNoiseDeform"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Noise Deform"
    "Categories", "warp"
    "Generated Class Name", "OgnNoiseDeformDatabase"
    "Python Module", "omni.warp.nodes"

