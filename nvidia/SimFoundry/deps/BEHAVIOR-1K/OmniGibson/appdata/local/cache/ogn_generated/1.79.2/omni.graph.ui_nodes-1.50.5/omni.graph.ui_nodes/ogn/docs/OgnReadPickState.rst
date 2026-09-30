.. _omni_graph_ui_nodes_ReadPickState_2:

.. _omni_graph_ui_nodes_ReadPickState:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Read Pick State (BETA)
    :keywords: lang-en omnigraph node ui threadsafe ui_nodes read-pick-state


Read Pick State (BETA)
======================

.. <description>

Read the state of the last picking event from the specified viewport. Note that picking events must be enabled on the specified viewport using a SetViewportMode node.

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
    "", "Metadata", "*allowedTokens* = Left Mouse Click,Right Mouse Click,Middle Mouse Click,Left Mouse Press,Right Mouse Press,Middle Mouse Press", ""
    "Tracked Prim Paths (*inputs:trackedPrimPaths*)", "``token[]``", "Optionally specify a set of prims (by paths) to track whether or not they got picked (only affects the value of 'Is Tracked Prim Picked')", "None"
    "Tracked Prims (*inputs:trackedPrims*)", "``target``", "Optionally specify a set of prims to track whether or not they got picked (only affects the value of 'Is Tracked Prim Picked')", "None"
    "", "Metadata", "*allowMultiInputs* = 1", ""
    "Use Paths (*inputs:usePaths*)", "``bool``", "When true, 'Tracked Prim Paths' is used, otherwise 'Tracked Prims' is used", "False"
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for picking events", "Viewport"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Is Tracked Prim Picked (*outputs:isTrackedPrimPicked*)", "``bool``", "True if a tracked prim got picked in the last picking event, or if any prim got picked if no tracked prims are specified", "None"
    "Is Valid (*outputs:isValid*)", "``bool``", "True if a valid event state was detected and the outputs of this node are valid, and false otherwise", "None"
    "Picked Prim (*outputs:pickedPrim*)", "``target``", "The picked prim, or an empty target if nothing got picked", "None"
    "Picked Prim Path (*outputs:pickedPrimPath*)", "``token``", "The path of the prim picked in the last picking event, or an empty string if nothing got picked", "None"
    "Picked World Position (*outputs:pickedWorldPos*)", "``pointd[3]``", "The XYZ-coordinates of the point in world space at which the prim got picked, or (0,0,0) if nothing got picked", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.ReadPickState"
    "Version", "2"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Read Pick State (BETA)"
    "Categories", "ui"
    "Generated Class Name", "OgnReadPickStateDatabase"
    "Python Module", "omni.graph.ui_nodes"

