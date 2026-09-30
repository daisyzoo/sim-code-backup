.. _omni_warp_WarpOgnBundleInspectChanges_1:

.. _omni_warp_WarpOgnBundleInspectChanges:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Bundle Inspect Changes
    :keywords: lang-en omnigraph node warp warp warp-ogn-bundle-inspect-changes


Bundle Inspect Changes
======================

.. <description>

Inspects the changes made to an attribute.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Bundle (*inputs:bundle*)", "``bundle``", "Input bundle.", "None"
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Attributes Changed (*outputs:attrsChanged*)", "``string``", "List of space separated bundle attribute names that have changed.", "None"
    "Bundle (*outputs:bundle*)", "``bundle``", "Output bundle.", "None"
    "Exec Out (*outputs:execOut*)", "``execution``", "Output execution.", "None"
    "Topology Changed (*outputs:topologyChanged*)", "``bool``", "Whether the topology of the attributes has changed.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.warp.WarpOgnBundleInspectChanges"
    "Version", "1"
    "Extension", "omni.warp"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Bundle Inspect Changes"
    "Categories", "warp"
    "Generated Class Name", "OgnBundleInspectChangesDatabase"
    "Python Module", "omni.warp.nodes"

