.. _omni_graph_ui_nodes_SetCameraPosition_2:

.. _omni_graph_ui_nodes_SetCameraPosition:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Set Camera Position
    :keywords: lang-en omnigraph node sceneGraph:camera WriteOnly ui_nodes set-camera-position


Set Camera Position
===================

.. <description>

Sets the camera's position

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "In (*inputs:execIn*)", "``execution``", "Signal to the graph that this node is ready to be executed.", "None"
    "Position (*inputs:position*)", "``pointd[3]``", "The new position", "[0.0, 0.0, 0.0]"
    "Prim (*inputs:prim*)", "``target``", "The camera prim, when 'usePath' is false", "None"
    "Camera Path (*inputs:primPath*)", "``token``", "Path of the camera, used when 'usePath' is true", ""
    "Rotate (*inputs:rotate*)", "``bool``", "True to keep position but change orientation and radius (camera moves to new   position while still looking at the same target). False to keep orientation and radius but change position (camera moves to look at new target).", "True"
    "Use Path (*inputs:usePath*)", "``bool``", "When true, the 'primPath' attribute is used as the path to the prim being read, otherwise it will read the connection at the 'prim' attribute", "True"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Out (*outputs:execOut*)", "``execution``", "Signal to the graph that execution can continue downstream.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.SetCameraPosition"
    "Version", "2"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Set Camera Position"
    "Categories", "sceneGraph:camera"
    "Generated Class Name", "OgnSetCameraPositionDatabase"
    "Python Module", "omni.graph.ui_nodes"

