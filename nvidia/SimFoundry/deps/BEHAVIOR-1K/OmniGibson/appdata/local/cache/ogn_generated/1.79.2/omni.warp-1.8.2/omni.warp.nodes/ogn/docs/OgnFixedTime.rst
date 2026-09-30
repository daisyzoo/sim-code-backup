.. _omni_warp_FixedTime_1:

.. _omni_warp_FixedTime:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Fixed Time
    :keywords: lang-en omnigraph node warp fixed-time


Fixed Time
==========

.. <description>

Retrieves a time with a fixed time step.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "End (*inputs:end*)", "``double``", "End time.", "1000.0"
    "Fps (*inputs:fps*)", "``double``", "Frames per second.", "60.0"
    "Start (*inputs:start*)", "``double``", "Start time.", "0.0"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Time (*outputs:time*)", "``double``", "Fixed time.", "0.0"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.warp.FixedTime"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "Generated Class Name", "OgnFixedTimeDatabase"
    "Python Module", "omni.warp.nodes"

