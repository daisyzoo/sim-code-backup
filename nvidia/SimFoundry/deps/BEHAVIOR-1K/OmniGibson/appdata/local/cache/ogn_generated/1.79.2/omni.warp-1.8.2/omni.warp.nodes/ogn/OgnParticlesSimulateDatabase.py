r"""Support for simplified access to data on nodes of type omni.warp.WarpParticlesSimulate

 __   ___ .  .  ___  __       ___  ___  __      __   __   __   ___
/ _` |__  |\ | |__  |__)  /\   |  |__  |  \    /  ` /  \ |  \ |__
\__| |___ | \| |___ |  \ /--\  |  |___ |__/    \__, \__/ |__/ |___

 __   __     .  .  __  ___     .  .  __   __     ___
|  \ /  \    |\ | /  \  |      |\/| /  \ |  \ | |__  \ /
|__/ \__/    | \| \__/  |      |  | \__/ |__/ | |     |

Simulates particles.
"""

import numpy
import sys
import traceback

import carb
import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class OgnParticlesSimulateDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.warp.WarpParticlesSimulate

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.collider
            inputs.colliderContactDistance
            inputs.colliderContactQueryRange
            inputs.contactDampingStiffness
            inputs.contactElasticStiffness
            inputs.contactFrictionCoeff
            inputs.contactFrictionStiffness
            inputs.enabled
            inputs.execIn
            inputs.globalScale
            inputs.gravity
            inputs.groundAltitude
            inputs.groundEnabled
            inputs.particles
            inputs.particlesContactAdhesion
            inputs.particlesContactCohesion
            inputs.particlesQueryRange
            inputs.substepCount
            inputs.time
        Outputs:
            outputs.execOut
            outputs.particles
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
        ('inputs:collider', 'bundle', 0, 'Collider', 'Collider geometry mesh.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, False, None, False, ''),
        ('inputs:colliderContactDistance', 'float', 0, 'Collider Contact Distance', "Distance to maintain from the collider's surface.", {'min': '0.0', ogn.MetadataKeys.DEFAULT: '1', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 1, False, ''),
        ('inputs:colliderContactQueryRange', 'float', 0, 'Collider Contact Query Range', "Distance to start probing for contacts with the collider's surface. Multiple of the collider contact distance.", {'min': '1.0', ogn.MetadataKeys.DEFAULT: '100.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 100.0, False, ''),
        ('inputs:contactDampingStiffness', 'float', 0, 'Contact Damping Stiffness', 'Contact damping stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '1.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 1.0, False, ''),
        ('inputs:contactElasticStiffness', 'float', 0, 'Contact Elastic Stiffness', 'Contact elastic stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '100.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 100.0, False, ''),
        ('inputs:contactFrictionCoeff', 'float', 0, 'Contact Friction Coeff', 'Contact coefficient of friction.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '0.75', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.75, False, ''),
        ('inputs:contactFrictionStiffness', 'float', 0, 'Contact Friction Stiffness', 'Contact friction stiffness. Multiple of the global scale value.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '1.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 1.0, False, ''),
        ('inputs:enabled', 'bool', 0, 'Enabled', 'Whether to enable the simulation.', {ogn.MetadataKeys.DEFAULT: 'true', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, True, False, ''),
        ('inputs:execIn', 'execution', 0, None, 'Input execution.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('inputs:globalScale', 'float', 0, 'Global Scale', 'Global scale value for the simulation attributes.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '100.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 100.0, False, ''),
        ('inputs:gravity', 'vector3f', 0, 'Gravity', 'Gravity force.', {ogn.MetadataKeys.DEFAULT: '[0.0, -980, 0.0]', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, [0.0, -980, 0.0], False, ''),
        ('inputs:groundAltitude', 'float', 0, 'Ground Altitude', 'Position of the ground on the Y axis.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('inputs:groundEnabled', 'bool', 0, 'Ground Enabled', 'Whether to add a ground collider.', {ogn.MetadataKeys.DEFAULT: 'true', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, True, False, ''),
        ('inputs:particles', 'bundle', 0, 'Particles', 'Particles to simulate.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('inputs:particlesContactAdhesion', 'float', 0, 'Particles Contact Adhesion', 'Contact coefficient of adhesion.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '0.25', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.25, False, ''),
        ('inputs:particlesContactCohesion', 'float', 0, 'Particles Contact Cohesion', 'Contact coefficient of cohesion.', {'min': '0.0', ogn.MetadataKeys.DEFAULT: '0.1', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.1, False, ''),
        ('inputs:particlesQueryRange', 'float', 0, 'Particles Query Range', 'Amount to expand the grid cell size to accommodate caching neighbours between steps. Multiple of the largest particle radius.', {'min': '1.0', ogn.MetadataKeys.DEFAULT: '2.0', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 2.0, False, ''),
        ('inputs:substepCount', 'int', 0, 'Substep Count', 'Number of substeps.', {ogn.MetadataKeys.DEFAULT: '32', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 32, False, ''),
        ('inputs:time', 'double', 0, 'Time', 'Time.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, 0.0, False, ''),
        ('outputs:execOut', 'execution', 0, None, 'Output execution.', {ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
        ('outputs:particles', 'bundle', 0, 'Particles', 'Output particles geometry.', {ogn.MetadataKeys.MEMORY_TYPE: 'cuda', ogn.MetadataKeys.CUDA_POINTERS: 'cpu'}, True, None, False, ''),
    ])

    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.collider = og.AttributeRole.BUNDLE
        role_data.inputs.execIn = og.AttributeRole.EXECUTION
        role_data.inputs.gravity = og.AttributeRole.VECTOR
        role_data.inputs.particles = og.AttributeRole.BUNDLE
        role_data.outputs.execOut = og.AttributeRole.EXECUTION
        role_data.outputs.particles = og.AttributeRole.BUNDLE
        return role_data

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"colliderContactDistance", "colliderContactQueryRange", "contactDampingStiffness", "contactElasticStiffness", "contactFrictionCoeff", "contactFrictionStiffness", "enabled", "execIn", "globalScale", "gravity", "groundAltitude", "groundEnabled", "particlesContactAdhesion", "particlesContactCohesion", "particlesQueryRange", "substepCount", "time", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self.__bundles = og.BundleContainer(context, node, attributes, ['inputs:collider', 'inputs:particles'], read_only=True, gpu_ptr_kinds={"inputs:collider": og.PtrToPtrKind.CPU,"inputs:particles": og.PtrToPtrKind.CPU})
            self._batchedReadAttributes = [self._attributes.colliderContactDistance, self._attributes.colliderContactQueryRange, self._attributes.contactDampingStiffness, self._attributes.contactElasticStiffness, self._attributes.contactFrictionCoeff, self._attributes.contactFrictionStiffness, self._attributes.enabled, self._attributes.execIn, self._attributes.globalScale, self._attributes.gravity, self._attributes.groundAltitude, self._attributes.groundEnabled, self._attributes.particlesContactAdhesion, self._attributes.particlesContactCohesion, self._attributes.particlesQueryRange, self._attributes.substepCount, self._attributes.time]
            self._batchedReadValues = [1, 100.0, 1.0, 100.0, 0.75, 1.0, True, None, 100.0, [0.0, -980, 0.0], 0.0, True, 0.25, 0.1, 2.0, 32, 0.0]

        @property
        def collider(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute inputs.collider"""
            return self.__bundles.collider

        @property
        def particles(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute inputs.particles"""
            return self.__bundles.particles

        @property
        def colliderContactDistance(self):
            return self._batchedReadValues[0]

        @colliderContactDistance.setter
        def colliderContactDistance(self, value):
            self._batchedReadValues[0] = value

        @property
        def colliderContactQueryRange(self):
            return self._batchedReadValues[1]

        @colliderContactQueryRange.setter
        def colliderContactQueryRange(self, value):
            self._batchedReadValues[1] = value

        @property
        def contactDampingStiffness(self):
            return self._batchedReadValues[2]

        @contactDampingStiffness.setter
        def contactDampingStiffness(self, value):
            self._batchedReadValues[2] = value

        @property
        def contactElasticStiffness(self):
            return self._batchedReadValues[3]

        @contactElasticStiffness.setter
        def contactElasticStiffness(self, value):
            self._batchedReadValues[3] = value

        @property
        def contactFrictionCoeff(self):
            return self._batchedReadValues[4]

        @contactFrictionCoeff.setter
        def contactFrictionCoeff(self, value):
            self._batchedReadValues[4] = value

        @property
        def contactFrictionStiffness(self):
            return self._batchedReadValues[5]

        @contactFrictionStiffness.setter
        def contactFrictionStiffness(self, value):
            self._batchedReadValues[5] = value

        @property
        def enabled(self):
            return self._batchedReadValues[6]

        @enabled.setter
        def enabled(self, value):
            self._batchedReadValues[6] = value

        @property
        def execIn(self):
            return self._batchedReadValues[7]

        @execIn.setter
        def execIn(self, value):
            self._batchedReadValues[7] = value

        @property
        def globalScale(self):
            return self._batchedReadValues[8]

        @globalScale.setter
        def globalScale(self, value):
            self._batchedReadValues[8] = value

        @property
        def gravity(self):
            return self._batchedReadValues[9]

        @gravity.setter
        def gravity(self, value):
            self._batchedReadValues[9] = value

        @property
        def groundAltitude(self):
            return self._batchedReadValues[10]

        @groundAltitude.setter
        def groundAltitude(self, value):
            self._batchedReadValues[10] = value

        @property
        def groundEnabled(self):
            return self._batchedReadValues[11]

        @groundEnabled.setter
        def groundEnabled(self, value):
            self._batchedReadValues[11] = value

        @property
        def particlesContactAdhesion(self):
            return self._batchedReadValues[12]

        @particlesContactAdhesion.setter
        def particlesContactAdhesion(self, value):
            self._batchedReadValues[12] = value

        @property
        def particlesContactCohesion(self):
            return self._batchedReadValues[13]

        @particlesContactCohesion.setter
        def particlesContactCohesion(self, value):
            self._batchedReadValues[13] = value

        @property
        def particlesQueryRange(self):
            return self._batchedReadValues[14]

        @particlesQueryRange.setter
        def particlesQueryRange(self, value):
            self._batchedReadValues[14] = value

        @property
        def substepCount(self):
            return self._batchedReadValues[15]

        @substepCount.setter
        def substepCount(self, value):
            self._batchedReadValues[15] = value

        @property
        def time(self):
            return self._batchedReadValues[16]

        @time.setter
        def time(self, value):
            self._batchedReadValues[16] = value

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
            self.__bundles = og.BundleContainer(context, node, attributes, ['outputs_particles'], read_only=False, gpu_ptr_kinds={"outputs_particles": og.PtrToPtrKind.CPU})
            self._batchedWriteValues = { }

        @property
        def particles(self) -> og.BundleContents:
            """Get the bundle wrapper class for the attribute outputs.particles"""
            return self.__bundles.particles

        @particles.setter
        def particles(self, bundle: og.BundleContents):
            """Overwrite the bundle attribute outputs.particles with a new bundle"""
            if not isinstance(bundle, og.BundleContents):
                carb.log_error("Only bundle attributes can be assigned to another bundle attribute")
            self.__bundles.particles.bundle = bundle

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
        self.inputs = OgnParticlesSimulateDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnParticlesSimulateDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnParticlesSimulateDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(OgnParticlesSimulateDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):  # pragma: no cover
                return get_node_type_function()
            return 'omni.warp.WarpParticlesSimulate'

        @staticmethod
        def compute(context, node):
            def database_valid():
                if not db.inputs.particles.valid:
                    db.log_warning('Required bundle inputs.particles is invalid or not connected, compute skipped')
                    return False
                if not db.outputs.particles.valid:
                    db.log_error('Required bundle outputs.particles is invalid, compute skipped')
                    return False
                return True
            try:
                per_node_data = OgnParticlesSimulateDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = OgnParticlesSimulateDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = OgnParticlesSimulateDatabase(node)

            try:
                compute_function = getattr(OgnParticlesSimulateDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:  # pragma: no cover
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return OgnParticlesSimulateDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:  # pragma: no cover
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            OgnParticlesSimulateDatabase._initialize_per_node_data(node)
            initialize_function = getattr(OgnParticlesSimulateDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):  # pragma: no cover
                initialize_function(context, node)

            per_node_data = OgnParticlesSimulateDatabase.PER_NODE_DATA[node.node_id()]

            def on_connection_or_disconnection(*args):
                per_node_data['_db'] = None

            node.register_on_connected_callback(on_connection_or_disconnection)
            node.register_on_disconnected_callback(on_connection_or_disconnection)

        @staticmethod
        def initialize_nodes(context, nodes):
            for n in nodes:
                OgnParticlesSimulateDatabase.abi.initialize(context, n)

        @staticmethod
        def release(node):
            release_function = getattr(OgnParticlesSimulateDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):  # pragma: no cover
                release_function(node)
            OgnParticlesSimulateDatabase._release_per_node_data(node)

        @staticmethod
        def init_instance(node, graph_instance_id):
            init_instance_function = getattr(OgnParticlesSimulateDatabase.NODE_TYPE_CLASS, 'init_instance', None)
            if callable(init_instance_function):  # pragma: no cover
                init_instance_function(node, graph_instance_id)

        @staticmethod
        def release_instance(node, graph_instance_id):
            release_instance_function = getattr(OgnParticlesSimulateDatabase.NODE_TYPE_CLASS, 'release_instance', None)
            if callable(release_instance_function):  # pragma: no cover
                release_instance_function(node, graph_instance_id)
            OgnParticlesSimulateDatabase._release_per_node_instance_data(node, graph_instance_id)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(OgnParticlesSimulateDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):  # pragma: no cover
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(OgnParticlesSimulateDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):  # pragma: no cover
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "omni.warp")
                node_type.set_metadata(ogn.MetadataKeys.HIDDEN, "true")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Particles Simulate (Deprecated)")
                node_type.set_metadata(ogn.MetadataKeys.CATEGORIES, "warp")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Simulates particles.")
                node_type.set_metadata(ogn.MetadataKeys.EXCLUSIONS, "tests")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                OgnParticlesSimulateDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(OgnParticlesSimulateDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):  # pragma: no cover
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        OgnParticlesSimulateDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(OgnParticlesSimulateDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("omni.warp.WarpParticlesSimulate")
