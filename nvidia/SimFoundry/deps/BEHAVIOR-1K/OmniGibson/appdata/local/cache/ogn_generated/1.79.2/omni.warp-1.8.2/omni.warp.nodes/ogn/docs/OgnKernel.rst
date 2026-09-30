.. _omni_warp_WarpKernel_2:

.. _omni_warp_WarpKernel:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Warp Kernel
    :keywords: lang-en omnigraph node warp warp warp-kernel


Warp Kernel
===========

.. <description>

Runs a single Warp kernel.

.. </description>


Installation
------------

To use this node enable :ref:`omni.warp<ext_omni_warp>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Code File (*inputs:codeFile*)", "``token``", "Path to a Python file defining the kernel function to launch.", "None"
    "", "Metadata", "*uiType* = filePath", ""
    "", "Metadata", "*fileExts* = Python scripts (\\*.py)", ""
    "Code Provider (*inputs:codeProvider*)", "``token``", "Where to read the code source from.", "embedded"
    "", "Metadata", "*allowedTokens* = embedded,file", ""
    "Code String (*inputs:codeStr*)", "``string``", "String defining the kernel function to launch.", "import warp as wp\n\n@wp.kernel\ndef compute(inputs: Inputs, outputs: Outputs):\n    tid = wp.tid()\n"
    "Device (*inputs:device*)", "``token``", "Device to launch on.", "cuda"
    "Dim 1 (*inputs:dim1*)", "``int``", "Size of the first kernel dimension.", "1"
    "", "Metadata", "*minimum* = 0", ""
    "Dim 2 (*inputs:dim2*)", "``int``", "Size of the second kernel dimension.", "1"
    "", "Metadata", "*minimum* = 0", ""
    "Dim 3 (*inputs:dim3*)", "``int``", "Size of the third kernel dimension.", "1"
    "", "Metadata", "*minimum* = 0", ""
    "Dim 4 (*inputs:dim4*)", "``int``", "Size of the fourth kernel dimension.", "1"
    "", "Metadata", "*minimum* = 0", ""
    "Dim Count (*inputs:dimCount*)", "``int``", "Number of kernel dimensions.", "1"
    "", "Metadata", "*minimum* = 1", ""
    "", "Metadata", "*maximum* = 4", ""
    "Dim Source (*inputs:dimSource*)", "``token``", "Where to read the dimensions from.", "explicit"
    "Exec In (*inputs:execIn*)", "``execution``", "Input execution.", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Exec Out (*outputs:execOut*)", "``execution``", "Output execution.", "None"


State
-----
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "User Attr Descs (*state:userAttrDescs*)", "``string``", "Internal: user attribute descriptions.", "{}"
    "User Attrs Event (*state:userAttrsEvent*)", "``int``", "Internal: user attributes event.", "0"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.warp.WarpKernel"
    "Version", "2"
    "Extension", "omni.warp"
    "Has State?", "True"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests, usd"
    "uiName", "Warp Kernel"
    "Categories", "warp"
    "Generated Class Name", "OgnKernelDatabase"
    "Python Module", "omni.warp.nodes"

