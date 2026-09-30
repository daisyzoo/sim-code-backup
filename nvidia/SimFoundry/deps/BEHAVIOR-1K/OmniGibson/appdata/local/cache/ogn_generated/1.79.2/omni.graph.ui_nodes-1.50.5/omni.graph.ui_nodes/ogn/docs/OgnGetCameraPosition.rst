.. _omni_graph_ui_nodes_GetCameraPosition_2:

.. _omni_graph_ui_nodes_GetCameraPosition:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Get Camera Position
    :keywords: lang-en omnigraph node sceneGraph:camera threadsafe ui_nodes get-camera-position


Get Camera Position
===================

.. <description>

Gets a viewport camera position

.. </description>


Installation
------------

To use this node enable :ref:`omni.graph.ui_nodes<ext_omni_graph_ui_nodes>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Prim (*inputs:prim*)", "``target``", "The camera prim, when 'usePath' is false", "None"
    "Camera Path (*inputs:primPath*)", "``token``", "Path of the camera, used when 'usePath' is true", ""
    "Use Path (*inputs:usePath*)", "``bool``", "When true, the 'primPath' attribute is used as the path to the prim being read, otherwise it will read the connection at the 'prim' attribute", "True"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Position (*outputs:position*)", "``pointd[3]``", "The position of the camera in world space", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.graph.ui_nodes.GetCameraPosition"
    "Version", "2"
    "Extension", "omni.graph.ui_nodes"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests"
    "uiName", "Get Camera Position"
    "Categories", "sceneGraph:camera"
    "Generated Class Name", "OgnGetCameraPositionDatabase"
    "Python Module", "omni.graph.ui_nodes"

