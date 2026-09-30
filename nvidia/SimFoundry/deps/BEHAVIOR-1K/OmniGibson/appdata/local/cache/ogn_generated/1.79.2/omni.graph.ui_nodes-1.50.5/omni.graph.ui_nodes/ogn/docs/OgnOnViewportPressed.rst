.. _omni_graph_ui_nodes_OnViewportPressed_1:

.. _omni_graph_ui_nodes_OnViewportPressed:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: On Viewport Pressed (BETA)
    :keywords: lang-en omnigraph node graph:action,ui threadsafe compute-on-request ui_nodes on-viewport-pressed


On Viewport Pressed (BETA)
==========================

.. <description>

Event node which fires when a press event is initiated in a viewport, and when that press is released. A press event differs from a click event only in timing. Press events are held down while click events are pressed and then immediately (within a small amount of time) released. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Gesture (*inputs:gesture*)", "``token``", "The input gesture that will trigger press events", "Left Mouse Press"
    "", "Metadata", "*displayGroup* = parameters", ""
    "", "Metadata", "*literalOnly* = 1", ""
    "", "Metadata", "*allowedTokens* = Left Mouse Press,Right Mouse Press,Middle Mouse Press", ""
    "Only Simulate On Play (*inputs:onlyPlayback*)", "``bool``", "When true, the node is only executed while Stage is being played", "True"
    "", "Metadata", "*literalOnly* = 1", ""
    "Use Normalized Coords (*inputs:useNormalizedCoords*)", "``bool``", "When true, the components of 2D position outputs are scaled to between 0 and 1, where 0 is top/left and 1 is bottom/right. When false, components are in viewport render resolution pixels.", "False"
    "", "Metadata", "*literalOnly* = 1", ""
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for press events", "Viewport"
    "", "Metadata", "*literalOnly* = 1", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Is Release Position Valid (*outputs:isReleasePositionValid*)", "``bool``", "True if the press was released inside of the viewport, and false otherwise", "None"
    "Press Position (*outputs:pressPosition*)", "``double[2]``", "The position at which the press occurred (valid when either 'Pressed' or 'Released' is enabled)", "None"
    "Pressed (*outputs:pressed*)", "``execution``", "When a press event is initiated in the viewport, signal to the graph that execution can continue downstream on this path. 'Press Position' will also be populated when this signal is set.", "None"
    "Release Position (*outputs:releasePosition*)", "``double[2]``", "The position at which the press was released, or (0,0) if the press was released outside of the viewport or the viewport is currently pressed (valid when 'Ended' is enabled and 'Is Release Position Valid' is true)", "None"
    "Released (*outputs:released*)", "``execution``", "When a press in the viewport is released, signal to the graph that execution can continue downstream on this path. 'Release Position' and 'Is Release Position Valid' will also be populated when this signal is set.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.OnViewportPressed"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "On Viewport Pressed (BETA)"
    "Categories", "graph:action,ui"
    "Generated Class Name", "OgnOnViewportPressedDatabase"
    "Python Module", "omni.graph.ui_nodes"

