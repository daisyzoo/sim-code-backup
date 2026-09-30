.. _omni_graph_ui_nodes_ReadMouseState_1:

.. _omni_graph_ui_nodes_ReadMouseState:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Read Mouse State
    :keywords: lang-en omnigraph node input:mouse threadsafe ui_nodes read-mouse-state


Read Mouse State
================

.. <description>

Reads the current state of the mouse. You can choose which mouse element this node is associated with. When mouse element is chosen to be a button, only outputs:isPressed is meaningful. When coordinates are chosen, only outputs:coords and outputs:window are meaningful.
Pixel coordinates are the position of the mouse cursor in screen pixel units with (0,0) top left. Normalized coordinates are values between 0-1 where 0 is top/left and 1 is bottom/right. By default, coordinates are relative to the application window, but if 'Use Relative Coords' is set to true, then coordinates are relative to the workspace window containing the mouse pointer.

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Mouse Element (*inputs:mouseElement*)", "``token``", "The mouse input to check the state of", "Left Button"
    "", "Metadata", "*displayGroup* = parameters", ""
    "", "Metadata", "*allowedTokens* = Left Button,Right Button,Middle Button,Forward Button,Back Button,Normalized Mouse Coordinates,Pixel Mouse Coordinates", ""
    "Use Relative Coords (*inputs:useRelativeCoords*)", "``bool``", "When true, the output 'coords' is made relative to the workspace window containing the mouse pointer instead of the entire application window", "False"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Coords (*outputs:coords*)", "``float[2]``", "The coordinates of the mouse. If the mouse element selected is a button, this will output a zero vector.", "None"
    "Is Pressed (*outputs:isPressed*)", "``bool``", "True if the button is currently pressed, false otherwise. If the mouse element selected is a coordinate, this will output false.", "None"
    "Window (*outputs:window*)", "``token``", "The name of the workspace window containing the mouse pointer if 'Use Relative Coords' is true and the mouse element selected is a coordinate", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.ReadMouseState"
    "Version", "1"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Read Mouse State"
    "Categories", "input:mouse"
    "Generated Class Name", "OgnReadMouseStateDatabase"
    "Python Module", "omni.graph.ui_nodes"

