r"""Support for simplified access to data on nodes of type omni.warp.WarpKernel

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Runs a single Warp kernel.
"""

import sys
import traceback

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class OgnKernelDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.warp.WarpKernel

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.codeFile
            inputs.codeProvider
            inputs.codeStr
            inputs.device
            inputs.dim1
            inputs.dim2
            inputs.dim3
            inputs.dim4
            inputs.dimCount
            inputs.dimSource
            inputs.execIn
        Outputs:
            outputs.execOut
        State:
            state.userAttrDescs
            state.userAttrsEvent

    Predefined Tokens:
        tokens.embedded
        tokens.file
    """

    # Imprint the generator and target ABI versions in the file for JIT generation
    GENERATOR_VERSION = (1, 79, 2)
    TARGET_VERSION = (2, 184, 5)

    # This is an internal object that provides per-class storage of a per-node data dictionary
    PER_NODE_DATA = {}

    # This is an internal object that describes unchanging attributes in a generic way
    # The values in this list are in no particular order, as a per-attribute tuple
    #     Name, Type, ExtendedTypeIndex, UiName, Description, Metadata,
    #     Is_Required, DefaultValue, Is_Deprecated, DeprecationMsg
    # You should not need to access any of this data directly, use the defined database interfaces
    INTERFACE = og.Database._get_interface([
        ('inputs:codeFile', 'token', 0, 'Code File', 'Path to a Python file defining the kernel function to launch.', {ogn.MetadataKeys.UI_TYPE: 'filePath', 'fileExts': 'Python scripts (*.py)'}, False, None, False, ''),
        ('inputs:codeProvider', 'token', 0, 'Code Provider', 'Where to read the code source from.', {ogn.MetadataKeys.ALLOWED_TOKENS: 'embedded,file', ogn.MetadataKeys.ALLOWED_TOKENS_RAW: '["embedded", "file"]', ogn.MetadataKeys.DEFAULT: '"embedded"'}, True, "embedded", False, ''),
        ('inputs:codeStr', 'string', 0, 'Code String', 'String defining the kernel function to launch.', {ogn.MetadataKeys.DEFAULT: '"import warp as wp\\n\\n@wp.kernel\\ndef compute(inputs: Inputs, outputs: Outputs):\\n    tid = wp.tid()\\n"'}, True, "import warp as wp\n\n@wp.kernel\ndef compute(inputs: Inputs, outputs: Outputs):\n    tid = wp.tid()\n", False, ''),
        ('inputs:device', 'token', 0, 'Device', 'Device to launch on.', {ogn.MetadataKeys.DEFAULT: '"cuda"'}, True, "cuda", False, ''),
        ('inputs:dim1', 'int', 0, 'Dim 1', 'Size of the first kernel dimension.', {'minimum': '0', ogn.MetadataKeys.DEFAULT: '1'}, True, 1, False, ''),
        ('inputs:dim2', 'int', 0, 'Dim 2', 'Size of the second kernel dimension.', {'minimum': '0', ogn.MetadataKeys.DEFAULT: '1'}, True, 1, False, ''),
        ('inputs:dim3', 'int', 0, 'Dim 3', 'Size of the third kernel dimension.', {'minimum': '0', ogn.MetadataKeys.DEFAULT: '1'}, True, 1, False, ''),
        ('inputs:dim4', 'int', 0, 'Dim 4', 'Size of the fourth kernel dimension.', {'minimum': '0', ogn.MetadataKeys.DEFAULT: '1'}, True, 1, False, ''),
        ('inputs:dimCount', 'int', 0, 'Dim Count', 'Number of kernel dimensions.', {'minimum': '1', 'maximum': '4', ogn.MetadataKeys.DEFAULT: '1'}, True, 1, False, ''),
        ('inputs:dimSource', 'token', 0, 'Dim Source', 'Where to read the dimensions from.', {ogn.MetadataKeys.DEFAULT: '"explicit"'}, True, "explicit", False, ''),
        ('inputs:execIn', 'execution', 0, None, 'Input execution.', {}, True, None, False, ''),
        ('outputs:execOut', 'execution', 0, None, 'Output execution.', {}, True, None, False, ''),
        ('state:userAttrDescs', 'string', 0, None, 'Internal: user attribute descriptions.', {ogn.MetadataKeys.DEFAULT: '"{}"'}, True, "{}", False, ''),
        ('state:userAttrsEvent', 'int', 0, None, 'Internal: user attributes event.', {ogn.MetadataKeys.DEFAULT: '0'}, True, 0, False, ''),
    ])

    class tokens:
        embedded = "embedded"
        file = "file"

    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.codeStr = og.AttributeRole.TEXT
        role_data.inputs.execIn = og.AttributeRole.EXECUTION
        role_data.outputs.execOut = og.AttributeRole.EXECUTION
        role_data.state.userAttrDescs = og.AttributeRole.TEXT
        return role_data

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"codeFile", "codeProvider", "codeStr", "device", "dim1", "dim2", "dim3", "dim4", "dimCount", "dimSource", "execIn", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = [self._attributes.codeFile, self._attributes.codeProvider, self._attributes.codeStr, self._attributes.device, self._attributes.dim1, self._attributes.dim2, self._attributes.dim3, self._attributes.dim4, self._attributes.dimCount, self._attributes.dimSource, self._attributes.execIn]
            self._batchedReadValues = [None, "embedded", "import warp as wp\n\n@wp.kernel\ndef compute(inputs: Inputs, outputs: Outputs):\n    tid = wp.tid()\n", "cuda", 1, 1, 1, 1, 1, "explicit", None]

        @property
        def codeFile(self):
            return self._batchedReadValues[0]

        @codeFile.setter
        def codeFile(self, value):
            self._batchedReadValues[0] = value

        @property
        def codeProvider(self):
            return self._batchedReadValues[1]

        @codeProvider.setter
        def codeProvider(self, value):
            self._batchedReadValues[1] = value

        @property
        def codeStr(self):
            return self._batchedReadValues[2]

        @codeStr.setter
        def codeStr(self, value):
            self._batchedReadValues[2] = value

        @property
        def device(self):
            return self._batchedReadValues[3]

        @device.setter
        def device(self, value):
            self._batchedReadValues[3] = value

        @property
        def dim1(self):
            return self._batchedReadValues[4]

        @dim1.setter
        def dim1(self, value):
            self._batchedReadValues[4] = value

        @property
        def dim2(self):
            return self._batchedReadValues[5]

        @dim2.setter
        def dim2(self, value):
            self._batchedReadValues[5] = value

        @property
        def dim3(self):
            return self._batchedReadValues[6]

        @dim3.setter
        def dim3(self, value):
            self._batchedReadValues[6] = value

        @property
        def dim4(self):
            return self._batchedReadValues[7]

        @dim4.setter
        def dim4(self, value):
            self._batchedReadValues[7] = value

        @property
        def dimCount(self):
            return self._batchedReadValues[8]

        @dimCount.setter
        def dimCount(self, value):
            self._batchedReadValues[8] = value

        @property
        def dimSource(self):
            return self._batchedReadValues[9]

        @dimSource.setter
        def dimSource(self, value):
            self._batchedReadValues[9] = value

        @property
        def execIn(self):
            return self._batchedReadValues[10]

        @execIn.setter
        def execIn(self, value):
            self._batchedReadValues[10] = value

        def __getattr__(self, item: str):
            if item in self.LOCAL_PROPERTY_NAMES:
                return object.__getattribute__(self, item)
            else:
                return super().__getattr__(item)

        def __setattr__(self, item: str, new_value):
            if item in self.LOCAL_PROPERTY_NAMES:
                object.__setattr__(self, item, new_value)
            else:
                super().__setattr__(item, new_value)

        def _prefetch(self):
            readAttributes = self._batchedReadAttributes
            newValues = _og._prefetch_input_attributes_data(readAttributes)
            if len(readAttributes) == len(newValues):
                self._batchedReadValues = newValues

    class ValuesForOutputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"execOut", "_batchedWriteValues"}
        """Helper class that creates natural hierarchical access to output attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedWriteValues = { }

        @property
        def execOut(self):
            value = self._batchedWriteValues.get(self._attributes.execOut)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.execOut)
                return data_view.get()

        @execOut.setter
        def execOut(self, value):
            self._batchedWriteValues[self._attributes.execOut] = value

        def __getattr__(self, item: str):
            if item in self.LOCAL_PROPERTY_NAMES:
                return object.__getattribute__(self, item)
            else:
                return super().__getattr__(item)

        def __setattr__(self, item: str, new_value):
            if item in self.LOCAL_PROPERTY_NAMES:
                object.__setattr__(self, item, new_value)
            else:
                super().__setattr__(item, new_value)

        def _commit(self):
            _og._commit_output_attributes_data(self._batchedWriteValues)
            self._batchedWriteValues = { }

    class ValuesForState(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to state attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self.userAttrDescs_size = 2

        @property
        def userAttrDescs(self):
            data_view = og.AttributeValueHelper(self._attributes.userAttrDescs)
            self.userAttrDescs_size = data_view.get_array_size()
            return data_view.get()

        @userAttrDescs.setter
        def userAttrDescs(self, value):
            data_view = og.AttributeValueHelper(self._attributes.userAttrDescs)
            data_view.set(value)
            self.userAttrDescs_size = data_view.get_array_size()

        @property
        def userAttrsEvent(self):
            data_view = og.AttributeValueHelper(self._attributes.userAttrsEvent)
            return data_view.get()

        @userAttrsEvent.setter
        def userAttrsEvent(self, value):
            data_view = og.AttributeValueHelper(self._attributes.userAttrsEvent)
            data_view.set(value)

    def __init__(self, node):
        super().__init__(node)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT)
        self.inputs = OgnKernelDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnKernelDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnKernelDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(OgnKernelDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'omni.warp.WarpKernel'

        @staticmethod
        def compute(context, node):
            def database_valid():
                return True
            try:
                per_node_data = OgnKernelDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = OgnKernelDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = OgnKernelDatabase(node)

            try:
                compute_function = getattr(OgnKernelDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return OgnKernelDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            OgnKernelDatabase._initialize_per_node_data(node)
            initialize_function = getattr(OgnKernelDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = OgnKernelDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                OgnKernelDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(OgnKernelDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            OgnKernelDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(OgnKernelDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(OgnKernelDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            OgnKernelDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(OgnKernelDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(OgnKernelDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "omni.warp")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Warp Kernel")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "warp")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Runs a single Warp kernel.")
                node_type.set_metadata(ogn.MetadataKeys.EXCLUSIONS, "tests,usd")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                OgnKernelDatabase.INTERFACE.add_to_node_type(node_type)
                node_type.set_has_state(True)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(OgnKernelDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        OgnKernelDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(OgnKernelDatabase.abi, 2)

    @staticmethod
    def deregister():
        og.deregister_node_type("omni.warp.WarpKernel")
