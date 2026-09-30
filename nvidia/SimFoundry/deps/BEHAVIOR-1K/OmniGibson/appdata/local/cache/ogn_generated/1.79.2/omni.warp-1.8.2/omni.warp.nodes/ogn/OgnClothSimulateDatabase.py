r"""Support for simplified access to data on nodes of type omni.warp.WarpClothSimulate

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Simulates cloth.
"""

import numpy
import sys
import traceback

import carb
import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class OgnClothSimulateDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.warp.WarpClothSimulate

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.cloth
            inputs.clothDensity
            inputs.clothEdgeBendingStiffness
            inputs.clothEdgeDampingStiffness
            inputs.clothTriAreaStiffness
            inputs.clothTriDampingStiffness
            inputs.clothTriDrag
            inputs.clothTriElasticStiffness
            inputs.clothTriLift
            inputs.collider
            inputs.colliderContactDistance
            inputs.colliderContactQueryRange
            inputs.contactDampingStiffness
            inputs.contactElasticStiffness
            inputs.contactFrictionCoeff
            inputs.contactFrictionStiffness
            inputs.enabled
            inputs.execIn
            inputs.gravity
            inputs.groundAltitude
            inputs.groundEnabled
            inputs.springDampingStiffness
            inputs.springElasticStiffness
            inputs.springIndexPairs
            inputs.springVisualize
            inputs.springVisualizeColor
            inputs.springVisualizeWidth
            inputs.substepCount
            inputs.time
        Outputs:
            outputs.cloth
            outputs.execOut
            outputs.visualization
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
        ('inputs:cloth', 'bundle', 0, 'Cloth', 'Cloth to simulate.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('inputs:clothDensity', 'float', 0, 'Cloth Density', 'Cloth density.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '0.1', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.1, False, ''),
        ('inputs:clothEdgeBendingStiffness', 'float', 0, 'Cloth Edge Bending Stiffness', 'Edge bending stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '0.01', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.01, False, ''),
        ('inputs:clothEdgeDampingStiffness', 'float', 0, 'Cloth Edge Damping Stiffness', 'Edge damping stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '1e-05', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 1e-05, False, ''),
        ('inputs:clothTriAreaStiffness', 'float', 0, 'Cloth Triangle Area Stiffness', 'Triangle area stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '100000.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 100000.0, False, ''),
        ('inputs:clothTriDampingStiffness', 'float', 0, 'Cloth Triangle Damping Stiffness', 'Triangle damping stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '1e-05', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 1e-05, False, ''),
        ('inputs:clothTriDrag', 'float', 0, 'Cloth Triangle Drag', 'Triangle drag force. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '0.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('inputs:clothTriElasticStiffness', 'float', 0, 'Cloth Triangle Elastic Stiffness', 'Triangle elastic stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '100000.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 100000.0, False, ''),
        ('inputs:clothTriLift', 'float', 0, 'Cloth Triangle Lift', 'Triangle lift force. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '0.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('inputs:collider', 'bundle', 0, 'Collider', 'Collider geometry mesh.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, False, None, False, ''),
        ('inputs:colliderContactDistance', 'float', 0, 'Collider Contact Distance', "Distance to maintain from the collider's surface.", {'min': '0.0', ogn.MetadataKeys.DEFAULT: '5.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 5.0, False, ''),
        ('inputs:colliderContactQueryRange', 'float', 0, 'Collider Contact Query Range', "Distance to start probing for contacts with the collider's surface. Multiple of the collider contact distance.", {'min': '1.0', ogn.MetadataKeys.DEFAULT: '10.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 10.0, False, ''),
        ('inputs:contactDampingStiffness', 'float', 0, 'Contact Damping Stiffness', 'Contact damping stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '10000.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 10000.0, False, ''),
        ('inputs:contactElasticStiffness', 'float', 0, 'Contact Elastic Stiffness', 'Contact elastic stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '100000.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 100000.0, False, ''),
        ('inputs:contactFrictionCoeff', 'float', 0, 'Contact Friction Coeff', 'Contact coefficient of friction.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '0.75', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.75, False, ''),
        ('inputs:contactFrictionStiffness', 'float', 0, 'Contact Friction Stiffness', 'Contact friction stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '10000.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 10000.0, False, ''),
        ('inputs:enabled', 'bool', 0, 'Enabled', 'Whether to enable the simulation.', {ogn.MetadataKeys.DEFAULT: 'true', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, True, False, ''),
        ('inputs:execIn', 'execution', 0, None, 'Input execution.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('inputs:gravity', 'vector3f', 0, 'Gravity', 'Gravity force.', {ogn.MetadataKeys.DEFAULT: '[0.0, -980, 0.0]', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, [0.0, -980, 0.0], False, ''),
        ('inputs:groundAltitude', 'float', 0, 'Ground Altitude', 'Position of the ground on the Y axis.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('inputs:groundEnabled', 'bool', 0, 'Ground Enabled', 'Whether to add a ground collider.', {ogn.MetadataKeys.DEFAULT: 'true', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, True, False, ''),
        ('inputs:springDampingStiffness', 'float', 0, 'Spring Damping Stiffness', 'Spring elastic stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '1.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 1.0, False, ''),
        ('inputs:springElasticStiffness', 'float', 0, 'Spring Elastic Stiffness', 'Spring elastic stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '1000.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 1000.0, False, ''),
        ('inputs:springIndexPairs', 'int2[]', 0, 'Spring Index Pairs', 'Vertex indices where each pair represents a spring constraint.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, [], False, ''),
        ('inputs:springVisualize', 'bool', 0, 'Spring Visualize', 'Whether to visualize the spring constraints.', {ogn.MetadataKeys.DEFAULT: 'false', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, False, False, ''),
        ('inputs:springVisualizeColor', 'color3f', 0, 'Spring Visualize Color', 'Visualization colour for the spring constraints.', {ogn.MetadataKeys.DEFAULT: '[10.0, 10.0, 0.0]', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, [10.0, 10.0, 0.0], False, ''),
        ('inputs:springVisualizeWidth', 'float', 0, 'Spring Visualize Width', 'Visualization width for the spring constraints.', {ogn.MetadataKeys.DEFAULT: '0.5', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.5, False, ''),
        ('inputs:substepCount', 'int', 0, 'Substep Count', 'Number of substeps.', {ogn.MetadataKeys.DEFAULT: '32', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 32, False, ''),
        ('inputs:time', 'double', 0, 'Time', 'Time.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('outputs:cloth', 'bundle', 0, 'Cloth', 'Output particles geometry.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('outputs:execOut', 'execution', 0, None, 'Output execution.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('outputs:visualization', 'bundle', 0, 'Visualization', 'Output visualization.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
    ])

    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.cloth = og.AttributeRole.BUNDLE
        role_data.inputs.collider = og.AttributeRole.BUNDLE
        role_data.inputs.execIn = og.AttributeRole.EXECUTION
        role_data.inputs.gravity = og.AttributeRole.VECTOR
        role_data.inputs.springVisualizeColor = og.AttributeRole.COLOR
        role_data.outputs.cloth = og.AttributeRole.BUNDLE
        role_data.outputs.execOut = og.AttributeRole.EXECUTION
        role_data.outputs.visualization = og.AttributeRole.BUNDLE
        return role_data

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"clothDensity", "clothEdgeBendingStiffness", "clothEdgeDampingStiffness", "clothTriAreaStiffness", "clothTriDampingStiffness", "clothTriDrag", "clothTriElasticStiffness", "clothTriLift", "colliderContactDistance", "colliderContactQueryRange", "contactDampingStiffness", "contactElasticStiffness", "contactFrictionCoeff", "contactFrictionStiffness", "enabled", "execIn", "gravity", "groundAltitude", "groundEnabled", "springDampingStiffness", "springElasticStiffness", "springVisualize", "springVisualizeColor", "springVisualizeWidth", "substepCount", "time", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self.__bundles = og.BundleContainer(context, node, attributes, ['inputs:cloth', 'inputs:collider'], read_only=True, gpu_ptr_kinds={"inputs:cloth": og.PtrToPtrKind.CPU,"inputs:collider": og.PtrToPtrKind.CPU})
            self._batchedReadAttributes = [self._attributes.clothDensity, self._attributes.clothEdgeBendingStiffness, self._attributes.clothEdgeDampingStiffness, self._attributes.clothTriAreaStiffness, self._attributes.clothTriDampingStiffness, self._attributes.clothTriDrag, self._attributes.clothTriElasticStiffness, self._attributes.clothTriLift, self._attributes.colliderContactDistance, self._attributes.colliderContactQueryRange, self._attributes.contactDampingStiffness, self._attributes.contactElasticStiffness, self._attributes.contactFrictionCoeff, self._attributes.contactFrictionStiffness, self._attributes.enabled, self._attributes.execIn, self._attributes.gravity, self._attributes.groundAltitude, self._attributes.groundEnabled, self._attributes.springDampingStiffness, self._attributes.springElasticStiffness, self._attributes.springVisualize, self._attributes.springVisualizeColor, self._attributes.springVisualizeWidth, self._attributes.substepCount, self._attributes.time]
            self._batchedReadValues = [0.1, 0.01, 1e-05, 100000.0, 1e-05, 0.0, 100000.0, 0.0, 5.0, 10.0, 10000.0, 100000.0, 0.75, 10000.0, True, None, [0.0, -980, 0.0], 0.0, True, 1.0, 1000.0, False, [10.0, 10.0, 0.0], 0.5, 32, 0.0]

        @property
        def cloth(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute inputs.cloth"""
            return self.__bundles.cloth

        @property
        def collider(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute inputs.collider"""
            return self.__bundles.collider

        @property
        def springIndexPairs(self):
            data_view = og.AttributeValueHelper(self._attributes.springIndexPairs)
            return data_view.get()

        @springIndexPairs.setter
        def springIndexPairs(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.springIndexPairs)
            data_view = og.AttributeValueHelper(self._attributes.springIndexPairs)
            data_view.set(value)
            self.springIndexPairs_size = data_view.get_array_size()

        @property
        def clothDensity(self):
            return self._batchedReadValues[0]

        @clothDensity.setter
        def clothDensity(self, value):
            self._batchedReadValues[0] = value

        @property
        def clothEdgeBendingStiffness(self):
            return self._batchedReadValues[1]

        @clothEdgeBendingStiffness.setter
        def clothEdgeBendingStiffness(self, value):
            self._batchedReadValues[1] = value

        @property
        def clothEdgeDampingStiffness(self):
            return self._batchedReadValues[2]

        @clothEdgeDampingStiffness.setter
        def clothEdgeDampingStiffness(self, value):
            self._batchedReadValues[2] = value

        @property
        def clothTriAreaStiffness(self):
            return self._batchedReadValues[3]

        @clothTriAreaStiffness.setter
        def clothTriAreaStiffness(self, value):
            self._batchedReadValues[3] = value

        @property
        def clothTriDampingStiffness(self):
            return self._batchedReadValues[4]

        @clothTriDampingStiffness.setter
        def clothTriDampingStiffness(self, value):
            self._batchedReadValues[4] = value

        @property
        def clothTriDrag(self):
            return self._batchedReadValues[5]

        @clothTriDrag.setter
        def clothTriDrag(self, value):
            self._batchedReadValues[5] = value

        @property
        def clothTriElasticStiffness(self):
            return self._batchedReadValues[6]

        @clothTriElasticStiffness.setter
        def clothTriElasticStiffness(self, value):
            self._batchedReadValues[6] = value

        @property
        def clothTriLift(self):
            return self._batchedReadValues[7]

        @clothTriLift.setter
        def clothTriLift(self, value):
            self._batchedReadValues[7] = value

        @property
        def colliderContactDistance(self):
            return self._batchedReadValues[8]

        @colliderContactDistance.setter
        def colliderContactDistance(self, value):
            self._batchedReadValues[8] = value

        @property
        def colliderContactQueryRange(self):
            return self._batchedReadValues[9]

        @colliderContactQueryRange.setter
        def colliderContactQueryRange(self, value):
            self._batchedReadValues[9] = value

        @property
        def contactDampingStiffness(self):
            return self._batchedReadValues[10]

        @contactDampingStiffness.setter
        def contactDampingStiffness(self, value):
            self._batchedReadValues[10] = value

        @property
        def contactElasticStiffness(self):
            return self._batchedReadValues[11]

        @contactElasticStiffness.setter
        def contactElasticStiffness(self, value):
            self._batchedReadValues[11] = value

        @property
        def contactFrictionCoeff(self):
            return self._batchedReadValues[12]

        @contactFrictionCoeff.setter
        def contactFrictionCoeff(self, value):
            self._batchedReadValues[12] = value

        @property
        def contactFrictionStiffness(self):
            return self._batchedReadValues[13]

        @contactFrictionStiffness.setter
        def contactFrictionStiffness(self, value):
            self._batchedReadValues[13] = value

        @property
        def enabled(self):
            return self._batchedReadValues[14]

        @enabled.setter
        def enabled(self, value):
            self._batchedReadValues[14] = value

        @property
        def execIn(self):
            return self._batchedReadValues[15]

        @execIn.setter
        def execIn(self, value):
            self._batchedReadValues[15] = value

        @property
        def gravity(self):
            return self._batchedReadValues[16]

        @gravity.setter
        def gravity(self, value):
            self._batchedReadValues[16] = value

        @property
        def groundAltitude(self):
            return self._batchedReadValues[17]

        @groundAltitude.setter
        def groundAltitude(self, value):
            self._batchedReadValues[17] = value

        @property
        def groundEnabled(self):
            return self._batchedReadValues[18]

        @groundEnabled.setter
        def groundEnabled(self, value):
            self._batchedReadValues[18] = value

        @property
        def springDampingStiffness(self):
            return self._batchedReadValues[19]

        @springDampingStiffness.setter
        def springDampingStiffness(self, value):
            self._batchedReadValues[19] = value

        @property
        def springElasticStiffness(self):
            return self._batchedReadValues[20]

        @springElasticStiffness.setter
        def springElasticStiffness(self, value):
            self._batchedReadValues[20] = value

        @property
        def springVisualize(self):
            return self._batchedReadValues[21]

        @springVisualize.setter
        def springVisualize(self, value):
            self._batchedReadValues[21] = value

        @property
        def springVisualizeColor(self):
            return self._batchedReadValues[22]

        @springVisualizeColor.setter
        def springVisualizeColor(self, value):
            self._batchedReadValues[22] = value

        @property
        def springVisualizeWidth(self):
            return self._batchedReadValues[23]

        @springVisualizeWidth.setter
        def springVisualizeWidth(self, value):
            self._batchedReadValues[23] = value

        @property
        def substepCount(self):
            return self._batchedReadValues[24]

        @substepCount.setter
        def substepCount(self, value):
            self._batchedReadValues[24] = value

        @property
        def time(self):
            return self._batchedReadValues[25]

        @time.setter
        def time(self, value):
            self._batchedReadValues[25] = value

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
            self.__bundles = og.BundleContainer(context, node, attributes, ['outputs_cloth', 'outputs_visualization'], read_only=False, gpu_ptr_kinds={"outputs_cloth": og.PtrToPtrKind.CPU,"outputs_visualization": og.PtrToPtrKind.CPU})
            self._batchedWriteValues = { }

        @property
        def cloth(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute outputs.cloth"""
            return self.__bundles.cloth

        @cloth.setter
        def cloth(self, bundle: og.BundleContents):
            """Overwrite the bundle attribute outputs.cloth with a new bundle"""
            if not isinstance(bundle, og.BundleContents):
                carb.log_error("Only bundle attributes can be assigned to another bundle attribute")
            self.__bundles.cloth.bundle = bundle

        @property
        def visualization(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute outputs.visualization"""
            return self.__bundles.visualization

        @visualization.setter
        def visualization(self, bundle: og.BundleContents):
            """Overwrite the bundle attribute outputs.visualization with a new bundle"""
            if not isinstance(bundle, og.BundleContents):
                carb.log_error("Only bundle attributes can be assigned to another bundle attribute")
            self.__bundles.visualization.bundle = bundle

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
        self.inputs = OgnClothSimulateDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnClothSimulateDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnClothSimulateDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(OgnClothSimulateDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'omni.warp.WarpClothSimulate'

        @staticmethod
        def compute(context, node):
            def database_valid():
                if not db.inputs.cloth.valid:
                    db.log_warning('Required bundle inputs.cloth is invalid or not connected, compute skipped')
                    return False
                if not db.outputs.cloth.valid:
                    db.log_error('Required bundle outputs.cloth is invalid, compute skipped')
                    return False
                if not db.outputs.visualization.valid:
                    db.log_error('Required bundle outputs.visualization is invalid, compute skipped')
                    return False
                return True
            try:
                per_node_data = OgnClothSimulateDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = OgnClothSimulateDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = OgnClothSimulateDatabase(node)

            try:
                compute_function = getattr(OgnClothSimulateDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return OgnClothSimulateDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            OgnClothSimulateDatabase._initialize_per_node_data(node)
            initialize_function = getattr(OgnClothSimulateDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = OgnClothSimulateDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                OgnClothSimulateDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(OgnClothSimulateDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            OgnClothSimulateDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(OgnClothSimulateDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(OgnClothSimulateDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            OgnClothSimulateDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(OgnClothSimulateDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(OgnClothSimulateDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "omni.warp")
                node_type.set_metadata(ogn.MetadataKeys.HIDDEN, "true")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Cloth Simulate (Deprecated)")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "warp")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Simulates cloth.")
                node_type.set_metadata(ogn.MetadataKeys.EXCLUSIONS, "tests")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                OgnClothSimulateDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(OgnClothSimulateDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        OgnClothSimulateDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(OgnClothSimulateDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("omni.warp.WarpClothSimulate")
