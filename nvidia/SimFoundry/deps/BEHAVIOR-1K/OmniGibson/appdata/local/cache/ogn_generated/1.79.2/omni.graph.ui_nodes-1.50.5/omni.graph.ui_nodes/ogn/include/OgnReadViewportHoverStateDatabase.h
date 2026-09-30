#pragma once

#include <omni/graph/core/ogn/UsdTypes.h>
using namespace pxr;

#include <omni/graph/core/ISchedulingHints2.h>
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
#include <omni/graph/core/Type.h>
#include <omni/graph/core/ogn/SimpleAttribute.h>
#include <omni/graph/core/tuple.h>

namespace OgnReadViewportHoverStateAttributes
{
namespace inputs
{
using useNormalizedCoords_t = const bool&;
ogn::AttributeInitializer<const bool, ogn::kOgnInput> useNormalizedCoords("inputs:useNormalizedCoords", "bool", kExtendedAttributeType_Regular, false);
using viewport_t = const NameToken&;
ogn::AttributeInitializer<const NameToken, ogn::kOgnInput> viewport("inputs:viewport", "token", kExtendedAttributeType_Regular);
}
namespace outputs
{
using isHovered_t = bool&;
ogn::AttributeInitializer<bool, ogn::kOgnOutput> isHovered("outputs:isHovered", "bool", kExtendedAttributeType_Regular);
using isValid_t = bool&;
ogn::AttributeInitializer<bool, ogn::kOgnOutput> isValid("outputs:isValid", "bool", kExtendedAttributeType_Regular);
using position_t = pxr::GfVec2d&;
ogn::AttributeInitializer<pxr::GfVec2d, ogn::kOgnOutput> position("outputs:position", "double2", kExtendedAttributeType_Regular);
using velocity_t = pxr::GfVec2d&;
ogn::AttributeInitializer<pxr::GfVec2d, ogn::kOgnOutput> velocity("outputs:velocity", "double2", kExtendedAttributeType_Regular);
}
namespace state
{
}
}
using namespace OgnReadViewportHoverStateAttributes;
namespace IOgnReadViewportHoverState
{
// Read the state of the last viewport hover event from the specified viewport. Note
// that viewport mouse events must be enabled on the specified viewport using a SetViewportMode
// node.
class OgnReadViewportHoverStateDatabase : public omni::graph::core::ogn::OmniGraphDatabase
{
public:
    template <typename StateInformation>
    CARB_DEPRECATED("sInternalState is deprecated. Use sSharedState or sPerInstanceState instead")
    static StateInformation& sInternalState(const NodeObj& nodeObj, InstanceIndex index = {kAuthoringGraphIndex}) {
        return sm_stateManagerOgnReadViewportHoverState.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sSharedState(const NodeObj& nodeObj) {
        return sm_stateManagerOgnReadViewportHoverState.getState<StateInformation>(nodeObj.nodeHandle, kAuthoringGraphIndex);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, InstanceIndex index) {
        return sm_stateManagerOgnReadViewportHoverState.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, GraphInstanceID instanceId) {
        return sm_stateManagerOgnReadViewportHoverState.getState<StateInformation>(nodeObj.nodeHandle, instanceId);
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
    static ogn::StateManager sm_stateManagerOgnReadViewportHoverState;
    static std::tuple<int, int, int>sm_generatorVersionOgnReadViewportHoverState;
    static std::tuple<int, int, int>sm_targetVersionOgnReadViewportHoverState;
    static constexpr size_t staticAttributeCount = 8;
    std::vector<ogn::DynamicInput> m_dynamicInputs;
    std::vector<ogn::DynamicOutput> m_dynamicOutputs;
    std::vector<ogn::DynamicState> m_dynamicStates;
    std::vector<NameToken> m_mappedAttributes;
    bool m_canCachePointers{true};

    struct inputsT {
        inputsT(size_t const& offset)
        : useNormalizedCoords{offset}
        , viewport{offset}
        {}
        ogn::SimpleInput<const bool,ogn::kCpu> useNormalizedCoords;
        ogn::SimpleInput<const NameToken,ogn::kCpu> viewport;
    } inputs;

    struct outputsT {
        outputsT(size_t const& offset)
        : isHovered{offset}
        , isValid{offset}
        , position{offset}
        , velocity{offset}
        {}
        ogn::SimpleOutput<bool,ogn::kCpu> isHovered;
        ogn::SimpleOutput<bool,ogn::kCpu> isValid;
        ogn::SimpleOutput<pxr::GfVec2d,ogn::kCpu> position;
        ogn::SimpleOutput<pxr::GfVec2d,ogn::kCpu> velocity;
    } outputs;

    //Only use this constructor for temporary stack-allocated object:
    OgnReadViewportHoverStateDatabase(NodeObj const& nodeObjParam)
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
    OgnReadViewportHoverStateDatabase(GraphContextObj const&, NodeObj const& nodeObjParam)
    : OgnReadViewportHoverStateDatabase(nodeObjParam)
    {}

    //Main constructor
    OgnReadViewportHoverStateDatabase(GraphContextObj const* contextObjParam, NodeObj const* nodeObjParam, size_t handleCount)
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
                ConstAttributeDataHandle, ConstAttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    inputs::useNormalizedCoords.m_token, inputs::viewport.m_token
                )
            , kAccordingToContextIndex);
            auto outputDataHandles0 = getAttributesW<
                AttributeDataHandle, AttributeDataHandle, AttributeDataHandle, AttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    outputs::isHovered.m_token, outputs::isValid.m_token, outputs::position.m_token, outputs::velocity.m_token
                )
            , kAccordingToContextIndex);
            inputs.useNormalizedCoords.setContext(contextObj);
            inputs.useNormalizedCoords.setHandle(std::get<0>(inputDataHandles0));
            inputs.viewport.setContext(contextObj);
            inputs.viewport.setHandle(std::get<1>(inputDataHandles0));
            outputs.isHovered.setContext(contextObj);
            outputs.isHovered.setHandle(std::get<0>(outputDataHandles0));
            outputs.isValid.setContext(contextObj);
            outputs.isValid.setHandle(std::get<1>(outputDataHandles0));
            outputs.position.setContext(contextObj);
            outputs.position.setHandle(std::get<2>(outputDataHandles0));
            outputs.velocity.setContext(contextObj);
            outputs.velocity.setHandle(std::get<3>(outputDataHandles0));
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
            CARB_LOG_ERROR("IToken not found when initializing omni.graph.ui_nodes.ReadViewportHoverState");
            return;
        }
        auto& iToken{ *iTokenPtr };

        static omni::fabric::Token inputs_viewport_token {"Viewport"};
        inputs::viewport.setDefault(inputs_viewport_token.asTokenC());
        inputs::useNormalizedCoords.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::viewport.initialize(iToken, *iNodeType, nodeTypeObj);

        outputs::isHovered.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::isValid.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::position.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::velocity.initialize(iToken, *iNodeType, nodeTypeObj);

        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExtension, "omni.graph.ui_nodes");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataUiName, "Read Viewport Hover State (BETA)");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataCategories, "ui");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataDescription, "Read the state of the last viewport hover event from the specified viewport. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExclusions, "tests");
        auto __schedulingInfo = nodeTypeObj.iNodeType->getSchedulingHints(nodeTypeObj);
        CARB_ASSERT(__schedulingInfo, "Could not acquire the scheduling hints");
        if (__schedulingInfo)
        {
            __schedulingInfo->setThreadSafety(eThreadSafety::eSafe);
            auto __schedulingInfo2 = omni::core::cast<ISchedulingHints2>(__schedulingInfo).get();
            if (__schedulingInfo2)
            {
            }
        }
    }
    static void initialize(const GraphContextObj&, const NodeObj& nodeObj)
    {
        const INode* iNode = nodeObj.iNode;
        AttributeObj attr;
        attr = iNode->getAttributeByToken(nodeObj, inputs::useNormalizedCoords.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When true, the components of 2D position and velocity outputs are scaled to between 0 and 1,\nwhere 0 is top/left and 1 is bottom/right.\nWhen false, components are in viewport render resolution pixels.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Use Normalized Coords");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "false");
        attr = iNode->getAttributeByToken(nodeObj, inputs::viewport.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Name of the viewport window to watch for hover events");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Viewport");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "\"Viewport\"");
        attr = iNode->getAttributeByToken(nodeObj, outputs::isHovered.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "True if the specified viewport is currently hovered");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Is Hovered");
        attr = iNode->getAttributeByToken(nodeObj, outputs::isValid.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "True if a valid event state was detected and the outputs of this node are valid, and false otherwise");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Is Valid");
        attr = iNode->getAttributeByToken(nodeObj, outputs::position.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The current mouse position if the specified viewport is currently hovered, otherwise (0,0)");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Position");
        attr = iNode->getAttributeByToken(nodeObj, outputs::velocity.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "A vector representing the change in position of the mouse since the previous frame\nif the specified viewport is currently hovered, otherwise (0,0)");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Velocity");
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
        sm_stateManagerOgnReadViewportHoverState.removeState(nodeObj.nodeHandle, instanceID);
    }
    bool validate() const {
        return validateNode()
            && inputs.useNormalizedCoords.isValid()
            && inputs.viewport.isValid()
            && outputs.isHovered.isValid()
            && outputs.isValid.isValid()
            && outputs.position.isValid()
            && outputs.velocity.isValid()
        ;
    }
    void preCompute() {
        if(m_canCachePointers == false) {
            inputs.useNormalizedCoords.invalidateCachedPointer();
            inputs.viewport.invalidateCachedPointer();
            outputs.isHovered.invalidateCachedPointer();
            outputs.isValid.invalidateCachedPointer();
            outputs.position.invalidateCachedPointer();
            outputs.velocity.invalidateCachedPointer();
            return;
        }
        for(NameToken const& attrib : m_mappedAttributes) {
            if(attrib == inputs::useNormalizedCoords.m_token) {
                inputs.useNormalizedCoords.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::viewport.m_token) {
                inputs.viewport.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::isHovered.m_token) {
                outputs.isHovered.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::isValid.m_token) {
                outputs.isValid.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::position.m_token) {
                outputs.position.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::velocity.m_token) {
                outputs.velocity.invalidateCachedPointer();
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
        if( !inputs.useNormalizedCoords.canVectorize()
            || !inputs.viewport.canVectorize()
            || !outputs.isHovered.canVectorize()
            || !outputs.isValid.canVectorize()
            || !outputs.position.canVectorize()
            || !outputs.velocity.canVectorize()
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
        if(token == inputs::useNormalizedCoords.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.useNormalizedCoords.setHandle(hdl);
            return;
        }
        if(token == inputs::viewport.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.viewport.setHandle(hdl);
            return;
        }
        if(token == outputs::isHovered.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.isHovered.setHandle(hdl);
            return;
        }
        if(token == outputs::isValid.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.isValid.setHandle(hdl);
            return;
        }
        if(token == outputs::position.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.position.setHandle(hdl);
            return;
        }
        if(token == outputs::velocity.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.velocity.setHandle(hdl);
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
ogn::StateManager OgnReadViewportHoverStateDatabase::sm_stateManagerOgnReadViewportHoverState;
std::tuple<int, int, int> OgnReadViewportHoverStateDatabase::sm_generatorVersionOgnReadViewportHoverState{std::make_tuple(1,79,2)};
std::tuple<int, int, int> OgnReadViewportHoverStateDatabase::sm_targetVersionOgnReadViewportHoverState{std::make_tuple(2,184,5)};
}
using namespace IOgnReadViewportHoverState;
#define REGISTER_OGN_NODE() \
namespace { \
    ogn::NodeTypeBootstrapImpl<OgnReadViewportHoverState, OgnReadViewportHoverStateDatabase> s_registration("omni.graph.ui_nodes.ReadViewportHoverState", 1, "omni.graph.ui_nodes"); \
}
