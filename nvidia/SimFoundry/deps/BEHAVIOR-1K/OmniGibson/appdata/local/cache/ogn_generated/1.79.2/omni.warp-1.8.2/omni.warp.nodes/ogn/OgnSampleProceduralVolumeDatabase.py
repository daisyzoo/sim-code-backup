r"""Support for simplified access to data on nodes of type omni.warp.WarpSampleProceduralVolume

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Generates a procedural volume.
"""

import numpy
import sys
import traceback

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class OgnSampleProceduralVolumeDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.warp.WarpSampleProceduralVolume

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.dim
            inputs.execIn
            inputs.smoothMinRadius
            inputs.time
            inputs.torusAltitude
            inputs.torusMajorRadius
            inputs.torusMinorRadius
        Outputs:
            outputs.data
            outputs.execOut
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
        ('inputs:dim', 'int', 0, 'Dim', 'Dimension for each side of the volume.', {'minimum': '1', ogn.MetadataKeys.DEFAULT: '64', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 64, False, ''),
        ('inputs:execIn', 'execution', 0, None, 'Input execution.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('inputs:smoothMinRadius', 'float', 0, 'Smooth Min Radius', 'Smoothness radius used to blend SDF volumes.', {'minimum': '0', ogn.MetadataKeys.DEFAULT: '1', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 1, False, ''),
        ('inputs:time', 'double', 0, 'Time', 'Time.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('inputs:torusAltitude', 'float', 0, 'Torus Altitude', 'Normalized position of the torus on the Y-axis.', {'minimum': '-1', 'maximum': '1', ogn.MetadataKeys.DEFAULT: '-0.5', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, -0.5, False, ''),
        ('inputs:torusMajorRadius', 'float', 0, 'Torus Major Radius', 'Normalized distance from the centre of the torus to the centre of the tube.', {'minimum': '0', 'maximum': '1', ogn.MetadataKeys.DEFAULT: '0.75', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.75, False, ''),
        ('inputs:torusMinorRadius', 'float', 0, 'Torus Minor Radius', 'Normalized radius of the tube.', {'minimum': '0', 'maximum': '1', ogn.MetadataKeys.DEFAULT: '0.1', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.1, False, ''),
        ('outputs:data', 'float[]', 0, 'Data', 'Output volume data.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('outputs:execOut', 'execution', 0, None, 'Output execution.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
    ])

    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.execIn = og.AttributeRole.EXECUTION
        role_data.outputs.execOut = og.AttributeRole.EXECUTION
        return role_data

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"dim", "execIn", "smoothMinRadius", "time", "torusAltitude", "torusMajorRadius", "torusMinorRadius", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = [self._attributes.dim, self._attributes.execIn, self._attributes.smoothMinRadius, self._attributes.time, self._attributes.torusAltitude, self._attributes.torusMajorRadius, self._attributes.torusMinorRadius]
            self._batchedReadValues = [64, None, 1, 0.0, -0.5, 0.75, 0.1]

        @property
        def dim(self):
            return self._batchedReadValues[0]

        @dim.setter
        def dim(self, value):
            self._batchedReadValues[0] = value

        @property
        def execIn(self):
            return self._batchedReadValues[1]

        @execIn.setter
        def execIn(self, value):
            self._batchedReadValues[1] = value

        @property
        def smoothMinRadius(self):
            return self._batchedReadValues[2]

        @smoothMinRadius.setter
        def smoothMinRadius(self, value):
            self._batchedReadValues[2] = value

        @property
        def time(self):
            return self._batchedReadValues[3]

        @time.setter
        def time(self, value):
            self._batchedReadValues[3] = value

        @property
        def torusAltitude(self):
            return self._batchedReadValues[4]

        @torusAltitude.setter
        def torusAltitude(self, value):
            self._batchedReadValues[4] = value

        @property
        def torusMajorRadius(self):
            return self._batchedReadValues[5]

        @torusMajorRadius.setter
        def torusMajorRadius(self, value):
            self._batchedReadValues[5] = value

        @property
        def torusMinorRadius(self):
            return self._batchedReadValues[6]

        @torusMinorRadius.setter
        def torusMinorRadius(self, value):
            self._batchedReadValues[6] = value

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
            self.data_size = None
            self._batchedWriteValues = { }

        @property
        def data(self):
            data_view = og.AttributeValueHelper(self._attributes.data)
            data_view.gpu_ptr_kind = og.PtrToPtrKind.CPU
            return data_view.get(reserved_element_count=self.data_size, on_gpu=True)

        @data.setter
        def data(self, value):
            data_view = og.AttributeValueHelper(self._attributes.data)
            data_view.gpu_ptr_kind = og.PtrToPtrKind.CPU
            data_view.set(value, on_gpu=True)
            self.data_size = data_view.get_array_size()

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

    def __init__(self, node):
        super().__init__(node)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT)
        self.inputs = OgnSampleProceduralVolumeDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnSampleProceduralVolumeDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnSampleProceduralVolumeDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'omni.warp.WarpSampleProceduralVolume'

        @staticmethod
        def compute(context, node):
            def database_valid():
                return True
            try:
                per_node_data = OgnSampleProceduralVolumeDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = OgnSampleProceduralVolumeDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = OgnSampleProceduralVolumeDatabase(node)

            try:
                compute_function = getattr(OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            OgnSampleProceduralVolumeDatabase._initialize_per_node_data(node)
            initialize_function = getattr(OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = OgnSampleProceduralVolumeDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                OgnSampleProceduralVolumeDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            OgnSampleProceduralVolumeDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            OgnSampleProceduralVolumeDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "omni.warp")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Sample Procedural Volume")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "warp,warp:samples")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Generates a procedural volume.")
                node_type.set_metadata(ogn.MetadataKeys.EXCLUSIONS, "tests")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                OgnSampleProceduralVolumeDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        OgnSampleProceduralVolumeDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(OgnSampleProceduralVolumeDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("omni.warp.WarpSampleProceduralVolume")
