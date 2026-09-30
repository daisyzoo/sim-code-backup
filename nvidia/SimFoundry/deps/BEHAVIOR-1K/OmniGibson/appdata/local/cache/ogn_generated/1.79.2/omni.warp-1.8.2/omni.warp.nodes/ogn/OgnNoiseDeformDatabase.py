r"""Support for simplified access to data on nodes of type omni.warp.WarpNoiseDeform

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Deforms points using a noise.
"""

import numpy
import sys
import traceback

import carb
import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class OgnNoiseDeformDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.warp.WarpNoiseDeform

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.amplitude
            inputs.axisAmplitude
            inputs.base
            inputs.cellSize
            inputs.execIn
            inputs.falloff
            inputs.func
            inputs.mode
            inputs.prims
            inputs.seed
            inputs.speed
            inputs.time
            inputs.upAxis
        Outputs:
            outputs.execOut
            outputs.prims

    Predefined Tokens:
        tokens.perlin
        tokens.curl
        tokens.Global
        tokens.Partial
        tokens.PosX
        tokens.PosY
        tokens.PosZ
        tokens.NegX
        tokens.NegY
        tokens.NegZ
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
        ('inputs:amplitude', 'float', 0, 'Amplitude', 'Amplitude of the deformation.', {ogn.MetadataKeys.DEFAULT: '10.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 10.0, False, ''),
        ('inputs:axisAmplitude', 'float3', 0, 'Axis Amplitude', 'Amplitude of the deformation along the different axis.', {ogn.MetadataKeys.DEFAULT: '[1.0, 1.0, 1.0]', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, [1.0, 1.0, 1.0], False, ''),
        ('inputs:base', 'float', 0, 'Base', "Base location of the deformation along the given axis. Below this value, points won't be deformed, which for example helps rooting the base of an asset onto the ground.", {ogn.MetadataKeys.DEFAULT: '0.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('inputs:cellSize', 'float', 0, 'Cell Size', 'Cell size of the noise.', {ogn.MetadataKeys.DEFAULT: '100.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 100.0, False, ''),
        ('inputs:execIn', 'execution', 0, None, 'Input execution.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('inputs:falloff', 'float', 0, 'Falloff', 'Distance falloff of the deformation starting from the given base value. Beyond this value, points will be fully deformed.', {ogn.MetadataKeys.DEFAULT: '0.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('inputs:func', 'token', 0, 'Function', 'Noise function.', {ogn.MetadataKeys.ALLOWED_TOKENS: 'perlin,curl', ogn.MetadataKeys.ALLOWED_TOKENS_RAW: '["perlin", "curl"]', ogn.MetadataKeys.DEFAULT: '"perlin"', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, "perlin", False, ''),
        ('inputs:mode', 'token', 0, 'Mode', 'Allows to apply the noise only on a partial subset of the geometries, as described by the upAxis, base, and falloff attributes.', {ogn.MetadataKeys.ALLOWED_TOKENS: 'global,partial', ogn.MetadataKeys.ALLOWED_TOKENS_RAW: '{"Global": "global", "Partial": "partial"}', ogn.MetadataKeys.DEFAULT: '"global"', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, "global", False, ''),
        ('inputs:prims', 'bundle', 0, 'Primitives', 'Primitives.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('inputs:seed', 'int', 0, 'Seed', 'Seed used to generate the noise.', {ogn.MetadataKeys.DEFAULT: '0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0, False, ''),
        ('inputs:speed', 'float', 0, 'Speed', 'Speed of the animated noise.', {ogn.MetadataKeys.DEFAULT: '1.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 1.0, False, ''),
        ('inputs:time', 'double', 0, 'Time', 'Time.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('inputs:upAxis', 'token', 0, 'Up Axis', 'Axis along which the base and falloff attributes are defined in. This must be expressed in the local space of the points being deformed.', {ogn.MetadataKeys.ALLOWED_TOKENS: '+X,+Y,+Z,-X,-Y,-Z', ogn.MetadataKeys.ALLOWED_TOKENS_RAW: '{"PosX": "+X", "PosY": "+Y", "PosZ": "+Z", "NegX": "-X", "NegY": "-Y", "NegZ": "-Z"}', ogn.MetadataKeys.DEFAULT: '"+Y"', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, "+Y", False, ''),
        ('outputs:execOut', 'execution', 0, None, 'Output execution.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('outputs:prims', 'bundle', 0, 'Primitives', 'Primitives.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
    ])

    class tokens:
        perlin = "perlin"
        curl = "curl"
        Global = "global"
        Partial = "partial"
        PosX = "+X"
        PosY = "+Y"
        PosZ = "+Z"
        NegX = "-X"
        NegY = "-Y"
        NegZ = "-Z"

    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.execIn = og.AttributeRole.EXECUTION
        role_data.inputs.prims = og.AttributeRole.BUNDLE
        role_data.outputs.execOut = og.AttributeRole.EXECUTION
        role_data.outputs.prims = og.AttributeRole.BUNDLE
        return role_data

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"amplitude", "axisAmplitude", "base", "cellSize", "execIn", "falloff", "func", "mode", "seed", "speed", "time", "upAxis", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self.__bundles = og.BundleContainer(context, node, attributes, ['inputs:prims'], read_only=True, gpu_ptr_kinds={"inputs:prims": og.PtrToPtrKind.CPU})
            self._batchedReadAttributes = [self._attributes.amplitude, self._attributes.axisAmplitude, self._attributes.base, self._attributes.cellSize, self._attributes.execIn, self._attributes.falloff, self._attributes.func, self._attributes.mode, self._attributes.seed, self._attributes.speed, self._attributes.time, self._attributes.upAxis]
            self._batchedReadValues = [10.0, [1.0, 1.0, 1.0], 0.0, 100.0, None, 0.0, "perlin", "global", 0, 1.0, 0.0, "+Y"]

        @property
        def prims(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute inputs.prims"""
            return self.__bundles.prims

        @property
        def amplitude(self):
            return self._batchedReadValues[0]

        @amplitude.setter
        def amplitude(self, value):
            self._batchedReadValues[0] = value

        @property
        def axisAmplitude(self):
            return self._batchedReadValues[1]

        @axisAmplitude.setter
        def axisAmplitude(self, value):
            self._batchedReadValues[1] = value

        @property
        def base(self):
            return self._batchedReadValues[2]

        @base.setter
        def base(self, value):
            self._batchedReadValues[2] = value

        @property
        def cellSize(self):
            return self._batchedReadValues[3]

        @cellSize.setter
        def cellSize(self, value):
            self._batchedReadValues[3] = value

        @property
        def execIn(self):
            return self._batchedReadValues[4]

        @execIn.setter
        def execIn(self, value):
            self._batchedReadValues[4] = value

        @property
        def falloff(self):
            return self._batchedReadValues[5]

        @falloff.setter
        def falloff(self, value):
            self._batchedReadValues[5] = value

        @property
        def func(self):
            return self._batchedReadValues[6]

        @func.setter
        def func(self, value):
            self._batchedReadValues[6] = value

        @property
        def mode(self):
            return self._batchedReadValues[7]

        @mode.setter
        def mode(self, value):
            self._batchedReadValues[7] = value

        @property
        def seed(self):
            return self._batchedReadValues[8]

        @seed.setter
        def seed(self, value):
            self._batchedReadValues[8] = value

        @property
        def speed(self):
            return self._batchedReadValues[9]

        @speed.setter
        def speed(self, value):
            self._batchedReadValues[9] = value

        @property
        def time(self):
            return self._batchedReadValues[10]

        @time.setter
        def time(self, value):
            self._batchedReadValues[10] = value

        @property
        def upAxis(self):
            return self._batchedReadValues[11]

        @upAxis.setter
        def upAxis(self, value):
            self._batchedReadValues[11] = value

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
            self.__bundles = og.BundleContainer(context, node, attributes, ['outputs_prims'], read_only=False, gpu_ptr_kinds={"outputs_prims": og.PtrToPtrKind.CPU})
            self._batchedWriteValues = { }

        @property
        def prims(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute outputs.prims"""
            return self.__bundles.prims

        @prims.setter
        def prims(self, bundle: og.BundleContents):
            """Overwrite the bundle attribute outputs.prims with a new bundle"""
            if not isinstance(bundle, og.BundleContents):
                carb.log_error("Only bundle attributes can be assigned to another bundle attribute")
            self.__bundles.prims.bundle = bundle

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
        self.inputs = OgnNoiseDeformDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnNoiseDeformDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnNoiseDeformDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(OgnNoiseDeformDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'omni.warp.WarpNoiseDeform'

        @staticmethod
        def compute(context, node):
            def database_valid():
                if not db.inputs.prims.valid:
                    db.log_warning('Required bundle inputs.prims is invalid or not connected, compute skipped')
                    return False
                if not db.outputs.prims.valid:
                    db.log_error('Required bundle outputs.prims is invalid, compute skipped')
                    return False
                return True
            try:
                per_node_data = OgnNoiseDeformDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = OgnNoiseDeformDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = OgnNoiseDeformDatabase(node)

            try:
                compute_function = getattr(OgnNoiseDeformDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return OgnNoiseDeformDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            OgnNoiseDeformDatabase._initialize_per_node_data(node)
            initialize_function = getattr(OgnNoiseDeformDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = OgnNoiseDeformDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                OgnNoiseDeformDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(OgnNoiseDeformDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            OgnNoiseDeformDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(OgnNoiseDeformDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(OgnNoiseDeformDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            OgnNoiseDeformDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(OgnNoiseDeformDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(OgnNoiseDeformDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "omni.warp")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Noise Deform")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "warp")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Deforms points using a noise.")
                node_type.set_metadata(ogn.MetadataKeys.EXCLUSIONS, "tests")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                OgnNoiseDeformDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(OgnNoiseDeformDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        OgnNoiseDeformDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(OgnNoiseDeformDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("omni.warp.WarpNoiseDeform")
