#pragma once

#include <carb/InterfaceUtils.h>
#include <omni/graph/core/NodeTypeRegistrar.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/CppWrappers.h>
#include <omni/fabric/Enums.h>
using omni::fabric::PtrToPtrKind;
#include <map>
#include <vector>
#include <tuple>
#include <omni/graph/core/OgnHelpers.h>
#include <carb/tokens/TokensUtils.h>
#include <array>
#include <omni/graph/core/Type.h>
#include <omni/graph/core/ogn/ArrayAttribute.h>
#include <omni/graph/core/ogn/SimpleAttribute.h>

namespace OgnDifferentialControllerAttributes
{
namespace inputs
{
using angularVelocity_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> angularVelocity("inputs:angularVelocity", "double", kExtendedAttributeType_Regular, 0.0);
using dt_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> dt("inputs:dt", "double", kExtendedAttributeType_Regular, 0.0);
using execIn_t = const uint32_t&;
ogn::AttributeInitializer<const uint32_t, ogn::kOgnInput> execIn("inputs:execIn", "execution", kExtendedAttributeType_Regular);
using linearVelocity_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> linearVelocity("inputs:linearVelocity", "double", kExtendedAttributeType_Regular, 0.0);
using maxAcceleration_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> maxAcceleration("inputs:maxAcceleration", "double", kExtendedAttributeType_Regular, 0.0);
using maxAngularAcceleration_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> maxAngularAcceleration("inputs:maxAngularAcceleration", "double", kExtendedAttributeType_Regular, 0.0);
using maxAngularSpeed_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> maxAngularSpeed("inputs:maxAngularSpeed", "double", kExtendedAttributeType_Regular, 0.0);
using maxDeceleration_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> maxDeceleration("inputs:maxDeceleration", "double", kExtendedAttributeType_Regular, 0.0);
using maxLinearSpeed_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> maxLinearSpeed("inputs:maxLinearSpeed", "double", kExtendedAttributeType_Regular, 0.0);
using maxWheelSpeed_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> maxWheelSpeed("inputs:maxWheelSpeed", "double", kExtendedAttributeType_Regular, 0.0);
using wheelDistance_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> wheelDistance("inputs:wheelDistance", "double", kExtendedAttributeType_Regular, 0.0);
using wheelRadius_t = const double&;
ogn::AttributeInitializer<const double, ogn::kOgnInput> wheelRadius("inputs:wheelRadius", "double", kExtendedAttributeType_Regular, 0.0);
}
namespace outputs
{
using velocityCommand_t = ogn::array<double>&;
ogn::AttributeInitializer<double*, ogn::kOgnOutput> velocityCommand("outputs:velocityCommand", "double[]", kExtendedAttributeType_Regular, std::array<double, 2>{{0.0,0.0}}.data(), 2);
}
namespace state
{
}
}
using namespace OgnDifferentialControllerAttributes;
namespace IOgnDifferentialController
{
// Differential Controller
class OgnDifferentialControllerDatabase : public omni::graph::core::ogn::OmniGraphDatabase
{
public:
    template <typename StateInformation>
    CARB_DEPRECATED("sInternalState is deprecated. Use sSharedState or sPerInstanceState instead")
    static StateInformation& sInternalState(const NodeObj& nodeObj, InstanceIndex index = {kAuthoringGraphIndex}) {
        return sm_stateManagerOgnDifferentialController.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sSharedState(const NodeObj& nodeObj) {
        return sm_stateManagerOgnDifferentialController.getState<StateInformation>(nodeObj.nodeHandle, kAuthoringGraphIndex);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, InstanceIndex index) {
        return sm_stateManagerOgnDifferentialController.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, GraphInstanceID instanceId) {
        return sm_stateManagerOgnDifferentialController.getState<StateInformation>(nodeObj.nodeHandle, instanceId);
    }
    template <typename StateInformation>
    CARB_DEPRECATED("internalState is deprecated. Use sharedState or perInstanceState instead")
    StateInformation& internalState(size_t relativeIdx = 0) {
        return sInternalState<StateInformation>(abi_node(), m_offset + relativeIdx);
    }
    template <typename StateInformation>
    StateInformation& sharedState() {
        return sSharedState<StateInformation>(abi_node());
    }
    template <typename StateInformation>
    StateInformation& perInstanceState(size_t relativeIdx = 0) {
        return sPerInstanceState<StateInformation>(abi_node(), m_offset + relativeIdx);
    }
    template <typename StateInformation>
    StateInformation& perInstanceState(GraphInstanceID instanceId) {
        return sPerInstanceState<StateInformation>(abi_node(), instanceId);
    }
    static ogn::StateManager sm_stateManagerOgnDifferentialController;
    static std::tuple<int, int, int>sm_generatorVersionOgnDifferentialController;
    static std::tuple<int, int, int>sm_targetVersionOgnDifferentialController;
    static constexpr size_t staticAttributeCount = 15;
    std::vector<ogn::DynamicInput> m_dynamicInputs;
    std::vector<ogn::DynamicOutput> m_dynamicOutputs;
    std::vector<ogn::DynamicState> m_dynamicStates;
    std::vector<NameToken> m_mappedAttributes;
    bool m_canCachePointers{true};

    struct inputsT {
        inputsT(size_t const& offset)
        : angularVelocity{offset}
        , dt{offset}
        , execIn{offset,AttributeRole::eExecution}
        , linearVelocity{offset}
        , maxAcceleration{offset}
        , maxAngularAcceleration{offset}
        , maxAngularSpeed{offset}
        , maxDeceleration{offset}
        , maxLinearSpeed{offset}
        , maxWheelSpeed{offset}
        , wheelDistance{offset}
        , wheelRadius{offset}
        {}
        ogn::SimpleInput<const double,ogn::kCpu> angularVelocity;
        ogn::SimpleInput<const double,ogn::kCpu> dt;
        ogn::SimpleInput<const uint32_t,ogn::kCpu> execIn;
        ogn::SimpleInput<const double,ogn::kCpu> linearVelocity;
        ogn::SimpleInput<const double,ogn::kCpu> maxAcceleration;
        ogn::SimpleInput<const double,ogn::kCpu> maxAngularAcceleration;
        ogn::SimpleInput<const double,ogn::kCpu> maxAngularSpeed;
        ogn::SimpleInput<const double,ogn::kCpu> maxDeceleration;
        ogn::SimpleInput<const double,ogn::kCpu> maxLinearSpeed;
        ogn::SimpleInput<const double,ogn::kCpu> maxWheelSpeed;
        ogn::SimpleInput<const double,ogn::kCpu> wheelDistance;
        ogn::SimpleInput<const double,ogn::kCpu> wheelRadius;
    } inputs;

    struct outputsT {
        outputsT(size_t const& offset)
        : velocityCommand{offset}
        {}
        ogn::ArrayOutput<double,ogn::kCpu> velocityCommand;
    } outputs;

    //Only use this constructor for temporary stack-allocated object:
    OgnDifferentialControllerDatabase(NodeObj const& nodeObjParam)
    : OmniGraphDatabase()
    , inputs{m_offset.index}
    , outputs{m_offset.index}
    {
        GraphContextObj const* contexts = nullptr;
        NodeObj const* nodes = nullptr;
        size_t handleCount = nodeObjParam.iNode->getAutoInstances(nodeObjParam, contexts, nodes);
        _ctor(contexts, nodes, handleCount);
        _init();
    }

    CARB_DEPRECATED("Passing the graph context to the temporary stack allocated database is not necessary anymore: you can safely remove this parameter")
    OgnDifferentialControllerDatabase(GraphContextObj const&, NodeObj const& nodeObjParam)
    : OgnDifferentialControllerDatabase(nodeObjParam)
    {}

    //Main constructor
    OgnDifferentialControllerDatabase(GraphContextObj const* contextObjParam, NodeObj const* nodeObjParam, size_t handleCount)
    : OmniGraphDatabase()
    , inputs{m_offset.index}
    , outputs{m_offset.index}
    {
        _ctor(contextObjParam, nodeObjParam, handleCount);
        _init();
    }

private:
    void _init() {
        GraphContextObj const& contextObj = abi_context();
        NodeObj const& nodeObj = abi_node();
        {
            auto inputDataHandles0 = getAttributesR<
                ConstAttributeDataHandle, ConstAttributeDataHandle, ConstAttributeDataHandle, ConstAttributeDataHandle,
                ConstAttributeDataHandle, ConstAttributeDataHandle, ConstAttributeDataHandle, ConstAttributeDataHandle,
                ConstAttributeDataHandle, ConstAttributeDataHandle, ConstAttributeDataHandle, ConstAttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    inputs::angularVelocity.m_token, inputs::dt.m_token, inputs::execIn.m_token, inputs::linearVelocity.m_token,
                    inputs::maxAcceleration.m_token, inputs::maxAngularAcceleration.m_token, inputs::maxAngularSpeed.m_token, inputs::maxDeceleration.m_token,
                    inputs::maxLinearSpeed.m_token, inputs::maxWheelSpeed.m_token, inputs::wheelDistance.m_token, inputs::wheelRadius.m_token
                )
            , kAccordingToContextIndex);
            auto outputDataHandles0 = getAttributesW<
                AttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    outputs::velocityCommand.m_token
                )
            , kAccordingToContextIndex);
            inputs.angularVelocity.setContext(contextObj);
            inputs.angularVelocity.setHandle(std::get<0>(inputDataHandles0));
            inputs.dt.setContext(contextObj);
            inputs.dt.setHandle(std::get<1>(inputDataHandles0));
            inputs.execIn.setContext(contextObj);
            inputs.execIn.setHandle(std::get<2>(inputDataHandles0));
            inputs.linearVelocity.setContext(contextObj);
            inputs.linearVelocity.setHandle(std::get<3>(inputDataHandles0));
            inputs.maxAcceleration.setContext(contextObj);
            inputs.maxAcceleration.setHandle(std::get<4>(inputDataHandles0));
            inputs.maxAngularAcceleration.setContext(contextObj);
            inputs.maxAngularAcceleration.setHandle(std::get<5>(inputDataHandles0));
            inputs.maxAngularSpeed.setContext(contextObj);
            inputs.maxAngularSpeed.setHandle(std::get<6>(inputDataHandles0));
            inputs.maxDeceleration.setContext(contextObj);
            inputs.maxDeceleration.setHandle(std::get<7>(inputDataHandles0));
            inputs.maxLinearSpeed.setContext(contextObj);
            inputs.maxLinearSpeed.setHandle(std::get<8>(inputDataHandles0));
            inputs.maxWheelSpeed.setContext(contextObj);
            inputs.maxWheelSpeed.setHandle(std::get<9>(inputDataHandles0));
            inputs.wheelDistance.setContext(contextObj);
            inputs.wheelDistance.setHandle(std::get<10>(inputDataHandles0));
            inputs.wheelRadius.setContext(contextObj);
            inputs.wheelRadius.setHandle(std::get<11>(inputDataHandles0));
            outputs.velocityCommand.setContext(contextObj);
            outputs.velocityCommand.setHandle(std::get<0>(outputDataHandles0));
        }
        tryGetDynamicAttributes<AttributePortType::kAttributePortType_Input>(staticAttributeCount, m_dynamicInputs);
        tryGetDynamicAttributes<AttributePortType::kAttributePortType_Output>(staticAttributeCount, m_dynamicOutputs);
        tryGetDynamicAttributes<AttributePortType::kAttributePortType_State>(staticAttributeCount, m_dynamicStates);

        collectMappedAttributes(m_mappedAttributes);

        m_canCachePointers = contextObj.iContext->canCacheAttributePointers ?
                                 contextObj.iContext->canCacheAttributePointers(contextObj) : true;
    }

public:
    static void initializeType(const NodeTypeObj& nodeTypeObj)
    {
        const INodeType* iNodeType = nodeTypeObj.iNodeType;
        auto iTokenPtr = carb::getCachedInterface<omni::fabric::IToken>();
        if( ! iTokenPtr ) {
            CARB_LOG_ERROR("IToken not found when initializing isaacsim.robot.wheeled_robots.DifferentialController");
            return;
        }
        auto& iToken{ *iTokenPtr };

        inputs::angularVelocity.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::dt.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::execIn.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::linearVelocity.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::maxAcceleration.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::maxAngularAcceleration.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::maxAngularSpeed.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::maxDeceleration.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::maxLinearSpeed.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::maxWheelSpeed.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::wheelDistance.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::wheelRadius.initialize(iToken, *iNodeType, nodeTypeObj);

        outputs::velocityCommand.initialize(iToken, *iNodeType, nodeTypeObj);

        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExtension, "isaacsim.robot.wheeled_robots");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataUiName, "Differential Controller");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataCategories, "isaacWheeledRobots");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataDescription, "Differential Controller");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataIconPath, "/home/user/Documents/zoo/sim/nvidia/SimFoundry/deps/BEHAVIOR-1K/OmniGibson/appdata/local/cache/ogn_generated/1.79.2/isaacsim.robot.wheeled_robots-4.0.24/isaacsim.robot.wheeled_robots/ogn/icons/isaacsim.robot.wheeled_robots.DifferentialController.svg");
    }
    static void initialize(const GraphContextObj&, const NodeObj& nodeObj)
    {
        const INode* iNode = nodeObj.iNode;
        AttributeObj attr;
        attr = iNode->getAttributeByToken(nodeObj, inputs::angularVelocity.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Desired rotation velocity in rad/s");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Desired Angular Velocity");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::dt.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Delta time in seconds");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::execIn.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The input execution");
        attr = iNode->getAttributeByToken(nodeObj, inputs::linearVelocity.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Desired linear velocity in m/s");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Desired Linear Velocity");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::maxAcceleration.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Maximum linear acceleration of the robot for forward and reverse in m/s^2, 0.0 means not set");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::maxAngularAcceleration.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Maximum angular acceleration of the robot in rad/s^2, 0.0 means not set");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::maxAngularSpeed.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Max angular speed allowed for vehicle in rad/s, 0.0 means not set");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::maxDeceleration.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Maximum linear braking of the robot in m/s^2, 0.0 means not set.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::maxLinearSpeed.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Max linear speed allowed for vehicle in m/s, 0.0 means not set");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::maxWheelSpeed.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Max wheel speed allowed in rad/s, 0.0 means not set");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::wheelDistance.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Distance between the two wheels in meters");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, inputs::wheelRadius.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Radius of the wheels in meters");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "0.0");
        attr = iNode->getAttributeByToken(nodeObj, outputs::velocityCommand.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Velocity commands\nUnits:\n    linear (m/s)\n    angular (rad/s)");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "[0.0, 0.0]");
    }
    std::vector<ogn::DynamicInput> const& getDynamicInputs() const
    {
        return m_dynamicInputs;
    }
    gsl::span<ogn::DynamicOutput> getDynamicOutputs()
    {
        return m_dynamicOutputs;
    }
    gsl::span<ogn::DynamicState> getDynamicStates()
    {
        return m_dynamicStates;
    }
    static void release(const NodeObj& nodeObj, GraphInstanceID instanceID)
    {
        sm_stateManagerOgnDifferentialController.removeState(nodeObj.nodeHandle, instanceID);
    }
    bool validate() const {
        return validateNode()
            && inputs.angularVelocity.isValid()
            && inputs.dt.isValid()
            && inputs.execIn.isValid()
            && inputs.linearVelocity.isValid()
            && inputs.maxAcceleration.isValid()
            && inputs.maxAngularAcceleration.isValid()
            && inputs.maxAngularSpeed.isValid()
            && inputs.maxDeceleration.isValid()
            && inputs.maxLinearSpeed.isValid()
            && inputs.maxWheelSpeed.isValid()
            && inputs.wheelDistance.isValid()
            && inputs.wheelRadius.isValid()
            && outputs.velocityCommand.isValid()
        ;
    }
    void preCompute() {
        if(m_canCachePointers == false) {
            inputs.angularVelocity.invalidateCachedPointer();
            inputs.dt.invalidateCachedPointer();
            inputs.execIn.invalidateCachedPointer();
            inputs.linearVelocity.invalidateCachedPointer();
            inputs.maxAcceleration.invalidateCachedPointer();
            inputs.maxAngularAcceleration.invalidateCachedPointer();
            inputs.maxAngularSpeed.invalidateCachedPointer();
            inputs.maxDeceleration.invalidateCachedPointer();
            inputs.maxLinearSpeed.invalidateCachedPointer();
            inputs.maxWheelSpeed.invalidateCachedPointer();
            inputs.wheelDistance.invalidateCachedPointer();
            inputs.wheelRadius.invalidateCachedPointer();
            outputs.velocityCommand.invalidateCachedPointer();
            return;
        }
        outputs.velocityCommand.invalidateCachedPointer();
        for(NameToken const& attrib : m_mappedAttributes) {
            if(attrib == inputs::angularVelocity.m_token) {
                inputs.angularVelocity.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::dt.m_token) {
                inputs.dt.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::execIn.m_token) {
                inputs.execIn.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::linearVelocity.m_token) {
                inputs.linearVelocity.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::maxAcceleration.m_token) {
                inputs.maxAcceleration.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::maxAngularAcceleration.m_token) {
                inputs.maxAngularAcceleration.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::maxAngularSpeed.m_token) {
                inputs.maxAngularSpeed.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::maxDeceleration.m_token) {
                inputs.maxDeceleration.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::maxLinearSpeed.m_token) {
                inputs.maxLinearSpeed.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::maxWheelSpeed.m_token) {
                inputs.maxWheelSpeed.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::wheelDistance.m_token) {
                inputs.wheelDistance.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::wheelRadius.m_token) {
                inputs.wheelRadius.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::velocityCommand.m_token) {
                outputs.velocityCommand.invalidateCachedPointer();
                continue;
            }
            bool found = false;
            for (auto& __a : m_dynamicInputs) {
                if (__a().name() == attrib) {
                    __a.invalidateCachedPointer();
                    found = true;
                    break;
                }
            }
            if(found) continue;
            for (auto& __a : m_dynamicOutputs) {
                if (__a().name() == attrib) {
                    __a.invalidateCachedPointer();
                    found = true;
                    break;
                }
            }
            if(found) continue;
            for (auto& __a : m_dynamicStates) {
                if (__a().name() == attrib) {
                    __a.invalidateCachedPointer();
                    found = true;
                    break;
                }
            }
            if(found) continue;
        }
    }
    bool canVectorize() const {
        if( !inputs.angularVelocity.canVectorize()
            || !inputs.dt.canVectorize()
            || !inputs.execIn.canVectorize()
            || !inputs.linearVelocity.canVectorize()
            || !inputs.maxAcceleration.canVectorize()
            || !inputs.maxAngularAcceleration.canVectorize()
            || !inputs.maxAngularSpeed.canVectorize()
            || !inputs.maxDeceleration.canVectorize()
            || !inputs.maxLinearSpeed.canVectorize()
            || !inputs.maxWheelSpeed.canVectorize()
            || !inputs.wheelDistance.canVectorize()
            || !inputs.wheelRadius.canVectorize()
        ) return false;
        for (auto const& __a : m_dynamicInputs) {
            if(!__a.canVectorize()) return false;
        }
        for (auto const& __a : m_dynamicOutputs) {
            if(!__a.canVectorize()) return false;
        }
        for (auto const& __a : m_dynamicStates) {
            if(!__a.canVectorize()) return false;
        }
        return true;
    }
    void onTypeResolutionChanged(AttributeObj const& attr) {
        if (! attr.isValid()) return;
        NameToken token = attr.iAttribute->getNameToken(attr);
        for (auto& __a : m_dynamicInputs) {
            if (__a().name() == token) {
                __a.fetchDetails(attr);
                return;
            }
        }
        for (auto& __a : m_dynamicOutputs) {
            if (__a().name() == token) {
                __a.fetchDetails(attr);
                return;
            }
        }
        for (auto& __a : m_dynamicStates) {
            if (__a().name() == token) {
                __a.fetchDetails(attr);
                return;
            }
        }
    }
    void onDynamicAttributesChanged(AttributeObj const& attribute, bool isAttributeCreated) {
        onDynamicAttributeCreatedOrRemoved(m_dynamicInputs, m_dynamicOutputs, m_dynamicStates, attribute, isAttributeCreated);
    }
    void onDataLocationChanged(AttributeObj const& attr) {
        if (! attr.isValid()) return;
        updateMappedAttributes(m_mappedAttributes, attr);
        NameToken token = attr.iAttribute->getNameToken(attr);
        if(token == inputs::angularVelocity.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.angularVelocity.setHandle(hdl);
            return;
        }
        if(token == inputs::dt.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.dt.setHandle(hdl);
            return;
        }
        if(token == inputs::execIn.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.execIn.setHandle(hdl);
            return;
        }
        if(token == inputs::linearVelocity.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.linearVelocity.setHandle(hdl);
            return;
        }
        if(token == inputs::maxAcceleration.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.maxAcceleration.setHandle(hdl);
            return;
        }
        if(token == inputs::maxAngularAcceleration.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.maxAngularAcceleration.setHandle(hdl);
            return;
        }
        if(token == inputs::maxAngularSpeed.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.maxAngularSpeed.setHandle(hdl);
            return;
        }
        if(token == inputs::maxDeceleration.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.maxDeceleration.setHandle(hdl);
            return;
        }
        if(token == inputs::maxLinearSpeed.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.maxLinearSpeed.setHandle(hdl);
            return;
        }
        if(token == inputs::maxWheelSpeed.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.maxWheelSpeed.setHandle(hdl);
            return;
        }
        if(token == inputs::wheelDistance.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.wheelDistance.setHandle(hdl);
            return;
        }
        if(token == inputs::wheelRadius.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.wheelRadius.setHandle(hdl);
            return;
        }
        if(token == outputs::velocityCommand.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.velocityCommand.setHandle(hdl);
            return;
        }
        for (auto& __a : m_dynamicInputs) {
            if (__a().name() == token) {
                __a.fetchDetails(attr);
                return;
            }
        }
        for (auto& __a : m_dynamicOutputs) {
            if (__a().name() == token) {
                __a.fetchDetails(attr);
                return;
            }
        }
        for (auto& __a : m_dynamicStates) {
            if (__a().name() == token) {
                __a.fetchDetails(attr);
                return;
            }
        }
    }
};
ogn::StateManager OgnDifferentialControllerDatabase::sm_stateManagerOgnDifferentialController;
std::tuple<int, int, int> OgnDifferentialControllerDatabase::sm_generatorVersionOgnDifferentialController{std::make_tuple(1,79,2)};
std::tuple<int, int, int> OgnDifferentialControllerDatabase::sm_targetVersionOgnDifferentialController{std::make_tuple(2,184,5)};
}
using namespace IOgnDifferentialController;
#define REGISTER_OGN_NODE() \
namespace { \
    ogn::NodeTypeBootstrapImpl<OgnDifferentialController, OgnDifferentialControllerDatabase> s_registration("isaacsim.robot.wheeled_robots.DifferentialController", 1, "isaacsim.robot.wheeled_robots"); \
}
