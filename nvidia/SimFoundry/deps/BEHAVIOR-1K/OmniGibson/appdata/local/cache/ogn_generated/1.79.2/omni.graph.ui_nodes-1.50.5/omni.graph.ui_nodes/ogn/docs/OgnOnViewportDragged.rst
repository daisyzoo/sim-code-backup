.. _omni_graph_ui_nodes_OnViewportDragged_1:

.. _omni_graph_ui_nodes_OnViewportDragged:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: On Viewport Dragged (BETA)
    :keywords: lang-en omnigraph node graph:action,ui threadsafe compute-on-request ui_nodes on-viewport-dragged


On Viewport Dragged (BETA)
==========================

.. <description>

Event node which fires when a drag event occurs in the specified viewport. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Gesture (*inputs:gesture*)", "``token``", "The input gesture to trigger viewport drag events.", "Left Mouse Drag"
    "", "Metadata", "*displayGroup* = parameters", ""
    "", "Metadata", "*literalOnly* = 1", ""
    "", "Metadata", "*allowedTokens* = Left Mouse Drag,Right Mouse Drag,Middle Mouse Drag", ""
    "Only Simulate On Play (*inputs:onlyPlayback*)", "``bool``", "When true, the node is only executed while Stage is being played", "True"
    "", "Metadata", "*literalOnly* = 1", ""
    "Use Normalized Coords (*inputs:useNormalizedCoords*)", "``bool``", "When true, the components of 2D position outputs are scaled to between 0 and 1, where 0 is top/left and 1 is bottom/right. When false, components are in viewport render resolution pixels.", "False"
    "", "Metadata", "*literalOnly* = 1", ""
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for drag events.", "Viewport"
    "", "Metadata", "*literalOnly* = 1", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Began (*outputs:began*)", "``execution``", "When the drag begins, signal to the graph that execution can continue downstream on this path. 'Initial Position' will also be populated when this signal is set.", "None"
    "Ended (*outputs:ended*)", "``execution``", "When the drag ends, signal to the graph that execution can continue downstream on this path. 'Final Position' will also be populated when this signal is set.", "None"
    "Final Position (*outputs:finalPosition*)", "``double[2]``", "The mouse position at which the drag ended (valid when 'Ended' is enabled).", "None"
    "Initial Position (*outputs:initialPosition*)", "``double[2]``", "The mouse position at which the drag began (valid when either 'Began' or 'Ended' is enabled).", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.OnViewportDragged"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "On Viewport Dragged (BETA)"
    "Categories", "graph:action,ui"
    "Generated Class Name", "OgnOnViewportDraggedDatabase"
    "Python Module", "omni.graph.ui_nodes"

