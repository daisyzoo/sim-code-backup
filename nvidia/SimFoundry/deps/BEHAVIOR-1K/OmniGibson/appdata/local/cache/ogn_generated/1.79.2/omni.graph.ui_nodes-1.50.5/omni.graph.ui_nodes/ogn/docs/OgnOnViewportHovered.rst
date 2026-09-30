.. _omni_graph_ui_nodes_OnViewportHovered_1:

.. _omni_graph_ui_nodes_OnViewportHovered:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: On Viewport Hovered (BETA)
    :keywords: lang-en omnigraph node graph:action,ui threadsafe compute-on-request ui_nodes on-viewport-hovered


On Viewport Hovered (BETA)
==========================

.. <description>

Event node which fires when the specified viewport is hovered over. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Only Simulate On Play (*inputs:onlyPlayback*)", "``bool``", "When true, the node is only executed while the Stage is being played.", "True"
    "", "Metadata", "*literalOnly* = 1", ""
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for hover events.", "Viewport"
    "", "Metadata", "*literalOnly* = 1", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Began (*outputs:began*)", "``execution``", "When the hover begins, signal to the graph that execution can continue downstream on this path.", "None"
    "Ended (*outputs:ended*)", "``execution``", "When the hover ends, signal to the graph that execution can continue downstream on this path.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.OnViewportHovered"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "On Viewport Hovered (BETA)"
    "Categories", "graph:action,ui"
    "Generated Class Name", "OgnOnViewportHoveredDatabase"
    "Python Module", "omni.graph.ui_nodes"

