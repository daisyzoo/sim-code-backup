.. _omni_graph_ui_nodes_OnViewportScrolled_1:

.. _omni_graph_ui_nodes_OnViewportScrolled:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: On Viewport Scrolled (BETA)
    :keywords: lang-en omnigraph node graph:action,ui threadsafe compute-on-request ui_nodes on-viewport-scrolled


On Viewport Scrolled (BETA)
===========================

.. <description>

Event node which fires when a scroll event occurs in the specified viewport. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.

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
    "Use Normalized Coords (*inputs:useNormalizedCoords*)", "``bool``", "When true, the components of the 2D position output are scaled to between 0 and 1, where 0 is top/left and 1 is bottom/right. When false, components are in viewport render resolution pixels.", "False"
    "", "Metadata", "*literalOnly* = 1", ""
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for scroll events.", "Viewport"
    "", "Metadata", "*literalOnly* = 1", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Position (*outputs:position*)", "``double[2]``", "The position at which the viewport scroll event occurred.", "None"
    "Scroll Value (*outputs:scrollValue*)", "``float``", "The number of mouse wheel clicks scrolled up if positive, or scrolled down if negative.", "None"
    "Scrolled (*outputs:scrolled*)", "``execution``", "When a viewport scroll event occurs in the specified viewport, signal to the graph that execution can continue downstream.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.OnViewportScrolled"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "On Viewport Scrolled (BETA)"
    "Categories", "graph:action,ui"
    "Generated Class Name", "OgnOnViewportScrolledDatabase"
    "Python Module", "omni.graph.ui_nodes"

