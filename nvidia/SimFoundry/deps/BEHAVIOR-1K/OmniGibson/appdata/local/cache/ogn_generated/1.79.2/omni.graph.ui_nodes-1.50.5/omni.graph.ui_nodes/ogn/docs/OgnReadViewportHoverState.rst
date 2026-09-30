.. _omni_graph_ui_nodes_ReadViewportHoverState_1:

.. _omni_graph_ui_nodes_ReadViewportHoverState:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Read Viewport Hover State (BETA)
    :keywords: lang-en omnigraph node ui threadsafe ui_nodes read-viewport-hover-state


Read Viewport Hover State (BETA)
================================

.. <description>

Read the state of the last viewport hover event from the specified viewport. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Use Normalized Coords (*inputs:useNormalizedCoords*)", "``bool``", "When true, the components of 2D position and velocity outputs are scaled to between 0 and 1, where 0 is top/left and 1 is bottom/right. When false, components are in viewport render resolution pixels.", "False"
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for hover events", "Viewport"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Is Hovered (*outputs:isHovered*)", "``bool``", "True if the specified viewport is currently hovered", "None"
    "Is Valid (*outputs:isValid*)", "``bool``", "True if a valid event state was detected and the outputs of this node are valid, and false otherwise", "None"
    "Position (*outputs:position*)", "``double[2]``", "The current mouse position if the specified viewport is currently hovered, otherwise (0,0)", "None"
    "Velocity (*outputs:velocity*)", "``double[2]``", "A vector representing the change in position of the mouse since the previous frame if the specified viewport is currently hovered, otherwise (0,0)", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.ReadViewportHoverState"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Read Viewport Hover State (BETA)"
    "Categories", "ui"
    "Generated Class Name", "OgnReadViewportHoverStateDatabase"
    "Python Module", "omni.graph.ui_nodes"

