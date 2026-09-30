.. _omni_graph_ui_nodes_OnViewportClicked_1:

.. _omni_graph_ui_nodes_OnViewportClicked:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: On Viewport Clicked (BETA)
    :keywords: lang-en omnigraph node graph:action,ui threadsafe compute-on-request ui_nodes on-viewport-clicked


On Viewport Clicked (BETA)
==========================

.. <description>

Event node which fires when a click event occurs in the specified viewport. A press event differs from a click event only in timing. Press events are held down while click events are pressed and then immediately (within a small amount of time) released. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Gesture (*inputs:gesture*)", "``token``", "The input gesture to trigger viewport click events.", "Left Mouse Click"
    "", "Metadata", "*displayGroup* = parameters", ""
    "", "Metadata", "*literalOnly* = 1", ""
    "", "Metadata", "*allowedTokens* = Left Mouse Click,Right Mouse Click,Middle Mouse Click", ""
    "Only Simulate On Play (*inputs:onlyPlayback*)", "``bool``", "When true, the node is only executed while the Stage is being played.", "True"
    "", "Metadata", "*literalOnly* = 1", ""
    "Use Normalized Coords (*inputs:useNormalizedCoords*)", "``bool``", "When true, the components of the 2D position output are scaled to between 0 and 1, where 0 is top/left and 1 is bottom/right. When false, components are in viewport render resolution pixels.", "False"
    "", "Metadata", "*literalOnly* = 1", ""
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for click events.", "Viewport"
    "", "Metadata", "*literalOnly* = 1", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Clicked (*outputs:clicked*)", "``execution``", "When the specified input gesture triggers a click event in the specified viewport, signal to the graph that execution can continue downstream.", "None"
    "Position (*outputs:position*)", "``double[2]``", "The position at which the click event occurred.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.OnViewportClicked"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "On Viewport Clicked (BETA)"
    "Categories", "graph:action,ui"
    "Generated Class Name", "OgnOnViewportClickedDatabase"
    "Python Module", "omni.graph.ui_nodes"

