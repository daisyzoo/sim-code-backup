.. _omni_graph_ui_nodes_SetViewportFullscreen_1:

.. _omni_graph_ui_nodes_SetViewportFullscreen:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Set Viewport Fullscreen
    :keywords: lang-en omnigraph node graph:action,viewport WriteOnly ui_nodes set-viewport-fullscreen


Set Viewport Fullscreen
=======================

.. <description>

Toggles fullscreen on/off for viewport(s) and visibility on/off for all other panes.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Exec (*inputs:exec*)", "``execution``", "Signal to the graph that this node is ready to be executed.", "None"
    "Mode (*inputs:mode*)", "``token``", "The mode to toggle fullscreen on/off for viewport(s) and visibility on/off for all other panes:  ""Default"" - Windowed viewport(s) with all other panes shown. ""Fullscreen"" - Fullscreen viewport(s) with all other panes hidden. ""Hide UI"" - Windowed viewport(s) with all other panes hidden.", "Default"
    "", "Metadata", "*allowedTokens* = Default,Fullscreen,Hide UI", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Exec (*outputs:exec*)", "``execution``", "Signal to the graph that execution can continue downstream.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.SetViewportFullscreen"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Set Viewport Fullscreen"
    "Categories", "graph:action,viewport"
    "Generated Class Name", "OgnSetViewportFullscreenDatabase"
    "Python Module", "omni.graph.ui_nodes"

