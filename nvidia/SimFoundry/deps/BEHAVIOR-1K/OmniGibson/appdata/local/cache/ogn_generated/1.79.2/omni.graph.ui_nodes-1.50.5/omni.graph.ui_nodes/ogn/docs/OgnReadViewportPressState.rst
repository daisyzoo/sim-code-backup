.. _omni_graph_ui_nodes_ReadViewportPressState_1:

.. _omni_graph_ui_nodes_ReadViewportPressState:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Read Viewport Press State (BETA)
    :keywords: lang-en omnigraph node ui threadsafe ui_nodes read-viewport-press-state


Read Viewport Press State (BETA)
================================

.. <description>

Read the state of the last viewport press event from the specified viewport. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Gesture (*inputs:gesture*)", "``token``", "The input gesture to trigger viewport press events", "Left Mouse Press"
    "", "Metadata", "*displayGroup* = parameters", ""
    "", "Metadata", "*allowedTokens* = Left Mouse Press,Right Mouse Press,Middle Mouse Press", ""
    "Use Normalized Coords (*inputs:useNormalizedCoords*)", "``bool``", "When true, the components of 2D position outputs are scaled to between 0 and 1, where 0 is top/left and 1 is bottom/right. When false, components are in viewport render resolution pixels.", "False"
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for press events", "Viewport"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Is Pressed (*outputs:isPressed*)", "``bool``", "True if the specified viewport is currently pressed", "None"
    "Is Release Position Valid (*outputs:isReleasePositionValid*)", "``bool``", "True if the press was released inside of the viewport, and false otherwise", "None"
    "Is Valid (*outputs:isValid*)", "``bool``", "True if a valid event state was detected and the outputs of this node are valid, and false otherwise", "None"
    "Press Position (*outputs:pressPosition*)", "``double[2]``", "The position at which the specified viewport was last pressed", "None"
    "Release Position (*outputs:releasePosition*)", "``double[2]``", "The position at which the last press on the specified viewport was released, or (0,0) if the press was released outside of the viewport or the viewport is currently pressed", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.ReadViewportPressState"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Read Viewport Press State (BETA)"
    "Categories", "ui"
    "Generated Class Name", "OgnReadViewportPressStateDatabase"
    "Python Module", "omni.graph.ui_nodes"

