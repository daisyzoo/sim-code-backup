.. _omni_graph_ui_nodes_OnPicked_3:

.. _omni_graph_ui_nodes_OnPicked:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: On Picked (BETA)
    :keywords: lang-en omnigraph node graph:action,ui threadsafe compute-on-request ui_nodes on-picked


On Picked (BETA)
================

.. <description>

Event node which fires when a picking event occurs in the specified viewport. Note that picking events must be enabled on the specified viewport using a SetViewportMode node.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Gesture (*inputs:gesture*)", "``token``", "The input gesture to trigger a picking event", "Left Mouse Click"
    "", "Metadata", "*displayGroup* = parameters", ""
    "", "Metadata", "*literalOnly* = 1", ""
    "", "Metadata", "*allowedTokens* = Left Mouse Click,Right Mouse Click,Middle Mouse Click,Left Mouse Press,Right Mouse Press,Middle Mouse Press", ""
    "Only Simulate On Play (*inputs:onlyPlayback*)", "``bool``", "When true, the node is only executed while Stage is being played.", "True"
    "", "Metadata", "*literalOnly* = 1", ""
    "Tracked Prims (*inputs:trackedPrims*)", "``target``", "Optionally specify a set of tracked prims that will cause 'Picked' to fire when picked", "None"
    "", "Metadata", "*literalOnly* = 1", ""
    "", "Metadata", "*allowMultiInputs* = 1", ""
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for picking events", "Viewport"
    "", "Metadata", "*literalOnly* = 1", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Is Tracked Prim Picked (*outputs:isTrackedPrimPicked*)", "``bool``", "True if a tracked prim got picked, or if any prim got picked if no tracked prims are specified (will always be true when 'Picked' fires, and false when 'Missed' fires)", "None"
    "Missed (*outputs:missed*)", "``execution``", "When an attempted picking did not pick a tracked prim, or when nothing gets picked if no tracked prims are specified, signal to the graph that execution can continue downstream on this path.", "None"
    "Picked (*outputs:picked*)", "``execution``", "When a tracked prim is picked, or when any prim is picked if no tracked prims are specified, signal to the graph that execution can continue downstream on this path.", "None"
    "Picked Prim (*outputs:pickedPrim*)", "``target``", "The picked prim, or an empty target if nothing got picked", "None"
    "Picked Prim Path (*outputs:pickedPrimPath*)", "``token``", "The path of the picked prim, or an empty string if nothing got picked", "None"
    "Picked World Position (*outputs:pickedWorldPos*)", "``pointd[3]``", "The XYZ-coordinates of the point in world space at which the prim got picked, or (0,0,0) if nothing got picked", "None"
    "Tracked Prim Paths (*outputs:trackedPrimPaths*)", "``token[]``", "A list of the paths of the prims specified in 'Tracked Prims'", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.OnPicked"
    "Version", "3"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "On Picked (BETA)"
    "Categories", "graph:action,ui"
    "Generated Class Name", "OgnOnPickedDatabase"
    "Python Module", "omni.graph.ui_nodes"

