.. _omni_graph_ui_nodes_ReadViewportScrollState_1:

.. _omni_graph_ui_nodes_ReadViewportScrollState:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Read Viewport Scroll State (BETA)
    :keywords: lang-en omnigraph node ui threadsafe ui_nodes read-viewport-scroll-state


Read Viewport Scroll State (BETA)
=================================

.. <description>

Read the state of the last viewport scroll event from the specified viewport. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Use Normalized Coords (*inputs:useNormalizedCoords*)", "``bool``", "When true, the components of the 2D position output are scaled to between 0 and 1, where 0 is top/left and 1 is bottom/right. When false, components are in viewport render resolution pixels.", "False"
    "Viewport (*inputs:viewport*)", "``token``", "Name of the viewport window to watch for scroll events", "Viewport"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Is Valid (*outputs:isValid*)", "``bool``", "True if a valid event state was detected and the outputs of this node are valid, and false otherwise", "None"
    "Position (*outputs:position*)", "``double[2]``", "The last position at which a viewport scroll event occurred in the specified viewport", "None"
    "Scroll Value (*outputs:scrollValue*)", "``float``", "The number of mouse wheel clicks scrolled up if positive, or scrolled down if negative", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.ReadViewportScrollState"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Read Viewport Scroll State (BETA)"
    "Categories", "ui"
    "Generated Class Name", "OgnReadViewportScrollStateDatabase"
    "Python Module", "omni.graph.ui_nodes"

