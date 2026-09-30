.. _omni_graph_ui_nodes_ReadViewportDragState_1:

.. _omni_graph_ui_nodes_ReadViewportDragState:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Read Viewport Drag State (BETA)
    :keywords: lang-en omnigraph node ui threadsafe ui_nodes read-viewport-drag-state


Read Viewport Drag State (BETA)
===============================

.. <description>

Read the state of the last viewport drag event from the specified viewport. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Gesture (*inputs:gesture*)", "``token``", "The input gesture to trigger viewport drag events", "Left Mouse Drag"
    "", "Metadata", "*displayGroup* = parameters", ""
    "", "Metadata", "*allowedTokens* = Left Mouse Drag,Right Mouse Drag,Middle Mouse Drag", ""
    "Use Normalized Coords (*inputs:useNormalizedCoords*)", "``bool``", "When true, the components of 2D position and velocity outputs are scaled to between 0 and 1, where 0 is top/left and 1 is bottom/right. When false, components are in viewport render resolution pixels.", "False"
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for drag events", "Viewport"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Current Position (*outputs:currentPosition*)", "``double[2]``", "The current mouse position if a drag is in progress, or the final mouse position of the most recent drag if a drag is not in progress", "None"
    "Initial Position (*outputs:initialPosition*)", "``double[2]``", "The mouse position at which the most recent drag began", "None"
    "Is Drag In Progress (*outputs:isDragInProgress*)", "``bool``", "True if a viewport drag event is currently in progress in the specified viewport", "None"
    "Is Valid (*outputs:isValid*)", "``bool``", "True if a valid event state was detected and the outputs of this node are valid, and false otherwise", "None"
    "Velocity (*outputs:velocity*)", "``double[2]``", "A vector representing the change in position of the mouse since the previous frame if a drag is in progress, otherwise (0,0)", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.ReadViewportDragState"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Read Viewport Drag State (BETA)"
    "Categories", "ui"
    "Generated Class Name", "OgnReadViewportDragStateDatabase"
    "Python Module", "omni.graph.ui_nodes"

