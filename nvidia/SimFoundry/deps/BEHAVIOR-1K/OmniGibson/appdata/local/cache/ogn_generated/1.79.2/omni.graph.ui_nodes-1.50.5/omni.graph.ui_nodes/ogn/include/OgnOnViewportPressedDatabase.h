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

namespace OgnOnViewportPressedAttributes
{
namespace inputs
{
using gesture_t = const NameToken&;
ogn::AttributeInitializer<const NameToken, ogn::kOgnInput> gesture("inputs:gesture", "token", kExtendedAttributeType_Regular);
using onlyPlayback_t = const bool&;
ogn::AttributeInitializer<const bool, ogn::kOgnInput> onlyPlayback("inputs:onlyPlayback", "bool", kExtendedAttributeType_Regular, true);
using useNormalizedCoords_t = const bool&;
ogn::AttributeInitializer<const bool, ogn::kOgnInput> useNormalizedCoords("inputs:useNormalizedCoords", "bool", kExtendedAttributeType_Regular, false);
using viewport_t = const NameToken&;
ogn::AttributeInitializer<const NameToken, ogn::kOgnInput> viewport("inputs:viewport", "token", kExtendedAttributeType_Regular);
}
namespace outputs
{
using isReleasePositionValid_t = bool&;
ogn::AttributeInitializer<bool, ogn::kOgnOutput> isReleasePositionValid("outputs:isReleasePositionValid", "bool", kExtendedAttributeType_Regular);
using pressPosition_t = pxr::GfVec2d&;
ogn::AttributeInitializer<pxr::GfVec2d, ogn::kOgnOutput> pressPosition("outputs:pressPosition", "double2", kExtendedAttributeType_Regular);
using pressed_t = uint32_t&;
ogn::AttributeInitializer<uint32_t, ogn::kOgnOutput> pressed("outputs:pressed", "execution", kExtendedAttributeType_Regular);
using releasePosition_t = pxr::GfVec2d&;
ogn::AttributeInitializer<pxr::GfVec2d, ogn::kOgnOutput> releasePosition("outputs:releasePosition", "double2", kExtendedAttributeType_Regular);
using released_t = uint32_t&;
ogn::AttributeInitializer<uint32_t, ogn::kOgnOutput> released("outputs:released", "execution", kExtendedAttributeType_Regular);
}
namespace state
{
}
}
using namespace OgnOnViewportPressedAttributes;
namespace IOgnOnViewportPressed
{
// Event node which fires when a press event is initiated in a viewport, and when that
// press is released. A press event differs from a click event only in timing. Press
// events are held down while click events are pressed and then immediately (within
// a small amount of time) released. Note that viewport mouse events must be enabled
// on the specified viewport using a SetViewportMode node.
class OgnOnViewportPressedDatabase : public omni::graph::core::ogn::OmniGraphDatabase
{
public:
    struct TokenManager
    {
        NameToken LeftMouseDrag;
        NameToken RightMouseDrag;
        NameToken MiddleMouseDrag;
    };
    static TokenManager tokens;
    template <typename StateInformation>
    CARB_DEPRECATED("sInternalState is deprecated. Use sSharedState or sPerInstanceState instead")
    static StateInformation& sInternalState(const NodeObj& nodeObj, InstanceIndex index = {kAuthoringGraphIndex}) {
        return sm_stateManagerOgnOnViewportPressed.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sSharedState(const NodeObj& nodeObj) {
        return sm_stateManagerOgnOnViewportPressed.getState<StateInformation>(nodeObj.nodeHandle, kAuthoringGraphIndex);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, InstanceIndex index) {
        return sm_stateManagerOgnOnViewportPressed.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, GraphInstanceID instanceId) {
        return sm_stateManagerOgnOnViewportPressed.getState<StateInformation>(nodeObj.nodeHandle, instanceId);
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
    static ogn::StateManager sm_stateManagerOgnOnViewportPressed;
    static std::tuple<int, int, int>sm_generatorVersionOgnOnViewportPressed;
    static std::tuple<int, int, int>sm_targetVersionOgnOnViewportPressed;
    static constexpr size_t staticAttributeCount = 11;
    std::vector<ogn::DynamicInput> m_dynamicInputs;
    std::vector<ogn::DynamicOutput> m_dynamicOutputs;
    std::vector<ogn::DynamicState> m_dynamicStates;
    std::vector<NameToken> m_mappedAttributes;
    bool m_canCachePointers{true};

    struct inputsT {
        inputsT(size_t const& offset)
        : gesture{offset}
        , onlyPlayback{offset}
        , useNormalizedCoords{offset}
        , viewport{offset}
        {}
        ogn::SimpleInput<const NameToken,ogn::kCpu> gesture;
        ogn::SimpleInput<const bool,ogn::kCpu> onlyPlayback;
        ogn::SimpleInput<const bool,ogn::kCpu> useNormalizedCoords;
        ogn::SimpleInput<const NameToken,ogn::kCpu> viewport;
    } inputs;

    struct outputsT {
        outputsT(size_t const& offset)
        : isReleasePositionValid{offset}
        , pressPosition{offset}
        , pressed{offset,AttributeRole::eExecution}
        , releasePosition{offset}
        , released{offset,AttributeRole::eExecution}
        {}
        ogn::SimpleOutput<bool,ogn::kCpu> isReleasePositionValid;
        ogn::SimpleOutput<pxr::GfVec2d,ogn::kCpu> pressPosition;
        ogn::SimpleOutput<uint32_t,ogn::kCpu> pressed;
        ogn::SimpleOutput<pxr::GfVec2d,ogn::kCpu> releasePosition;
        ogn::SimpleOutput<uint32_t,ogn::kCpu> released;
    } outputs;

    //Only use this constructor for temporary stack-allocated object:
    OgnOnViewportPressedDatabase(NodeObj const& nodeObjParam)
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
    OgnOnViewportPressedDatabase(GraphContextObj const&, NodeObj const& nodeObjParam)
    : OgnOnViewportPressedDatabase(nodeObjParam)
    {}

    //Main constructor
    OgnOnViewportPressedDatabase(GraphContextObj const* contextObjParam, NodeObj const* nodeObjParam, size_t handleCount)
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
                ConstAttributeDataHandle, ConstAttributeDataHandle, ConstAttributeDataHandle, ConstAttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    inputs::gesture.m_token, inputs::onlyPlayback.m_token, inputs::useNormalizedCoords.m_token, inputs::viewport.m_token
                )
            , kAccordingToContextIndex);
            auto outputDataHandles0 = getAttributesW<
                AttributeDataHandle, AttributeDataHandle, AttributeDataHandle, AttributeDataHandle,
                AttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    outputs::isReleasePositionValid.m_token, outputs::pressPosition.m_token, outputs::pressed.m_token, outputs::releasePosition.m_token,
                    outputs::released.m_token
                )
            , kAccordingToContextIndex);
            inputs.gesture.setContext(contextObj);
            inputs.gesture.setHandle(std::get<0>(inputDataHandles0));
            inputs.onlyPlayback.setContext(contextObj);
            inputs.onlyPlayback.setHandle(std::get<1>(inputDataHandles0));
            inputs.useNormalizedCoords.setContext(contextObj);
            inputs.useNormalizedCoords.setHandle(std::get<2>(inputDataHandles0));
            inputs.viewport.setContext(contextObj);
            inputs.viewport.setHandle(std::get<3>(inputDataHandles0));
            outputs.isReleasePositionValid.setContext(contextObj);
            outputs.isReleasePositionValid.setHandle(std::get<0>(outputDataHandles0));
            outputs.pressPosition.setContext(contextObj);
            outputs.pressPosition.setHandle(std::get<1>(outputDataHandles0));
            outputs.pressed.setContext(contextObj);
            outputs.pressed.setHandle(std::get<2>(outputDataHandles0));
            outputs.releasePosition.setContext(contextObj);
            outputs.releasePosition.setHandle(std::get<3>(outputDataHandles0));
            outputs.released.setContext(contextObj);
            outputs.released.setHandle(std::get<4>(outputDataHandles0));
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
            CARB_LOG_ERROR("IToken not found when initializing omni.graph.ui_nodes.OnViewportPressed");
            return;
        }
        auto& iToken{ *iTokenPtr };
        OgnOnViewportPressedDatabase::tokens.LeftMouseDrag = iToken.getHandle("Left Mouse Press");
        OgnOnViewportPressedDatabase::tokens.RightMouseDrag = iToken.getHandle("Right Mouse Press");
        OgnOnViewportPressedDatabase::tokens.MiddleMouseDrag = iToken.getHandle("Middle Mouse Press");

        static omni::fabric::Token inputs_gesture_token {"Left Mouse Press"};
        inputs::gesture.setDefault(inputs_gesture_token.asTokenC());
        static omni::fabric::Token inputs_viewport_token {"Viewport"};
        inputs::viewport.setDefault(inputs_viewport_token.asTokenC());
        inputs::gesture.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::onlyPlayback.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::useNormalizedCoords.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::viewport.initialize(iToken, *iNodeType, nodeTypeObj);

        outputs::isReleasePositionValid.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::pressPosition.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::pressed.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::releasePosition.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::released.initialize(iToken, *iNodeType, nodeTypeObj);

        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExtension, "omni.graph.ui_nodes");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataUiName, "On Viewport Pressed (BETA)");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataCategories, "graph:action,ui");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataDescription, "Event node which fires when a press event is initiated in a viewport, and when that press is released. A press event differs from a click event only in timing. Press events are held down while click events are pressed and then immediately (within a small amount of time) released. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExclusions, "tests");
        auto __schedulingInfo = nodeTypeObj.iNodeType->getSchedulingHints(nodeTypeObj);
        CARB_ASSERT(__schedulingInfo, "Could not acquire the scheduling hints");
        if (__schedulingInfo)
        {
            __schedulingInfo->setThreadSafety(eThreadSafety::eSafe);
            __schedulingInfo->setComputeRule(eComputeRule::eOnRequest);
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
        attr = iNode->getAttributeByToken(nodeObj, inputs::gesture.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The input gesture that will trigger press events");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Gesture");
        attr.iAttribute->setMetadata(attr, "displayGroup", "parameters");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokens, "Left Mouse Press,Right Mouse Press,Middle Mouse Press");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokensRaw, "{\"LeftMouseDrag\": \"Left Mouse Press\", \"RightMouseDrag\": \"Right Mouse Press\", \"MiddleMouseDrag\": \"Middle Mouse Press\"}");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "\"Left Mouse Press\"");
        attr = iNode->getAttributeByToken(nodeObj, inputs::onlyPlayback.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When true, the node is only executed while Stage is being played");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Only Simulate On Play");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "true");
        attr = iNode->getAttributeByToken(nodeObj, inputs::useNormalizedCoords.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When true, the components of 2D position outputs are scaled to between 0 and 1,\nwhere 0 is top/left and 1 is bottom/right.\nWhen false, components are in viewport render resolution pixels.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Use Normalized Coords");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "false");
        attr = iNode->getAttributeByToken(nodeObj, inputs::viewport.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Name of the viewport window to watch for press events");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Viewport");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "\"Viewport\"");
        attr = iNode->getAttributeByToken(nodeObj, outputs::isReleasePositionValid.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "True if the press was released inside of the viewport, and false otherwise");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Is Release Position Valid");
        attr = iNode->getAttributeByToken(nodeObj, outputs::pressPosition.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The position at which the press occurred (valid when either 'Pressed' or 'Released' is enabled)");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Press Position");
        attr = iNode->getAttributeByToken(nodeObj, outputs::pressed.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When a press event is initiated in the viewport, signal to the graph that execution can continue\ndownstream on this path. 'Press Position' will also be populated when this signal is set.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Pressed");
        attr = iNode->getAttributeByToken(nodeObj, outputs::releasePosition.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The position at which the press was released, or (0,0) if the press was released outside of the viewport\nor the viewport is currently pressed (valid when 'Ended' is enabled and 'Is Release Position Valid' is true)");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Release Position");
        attr = iNode->getAttributeByToken(nodeObj, outputs::released.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When a press in the viewport is released, signal to the graph that execution can continue\ndownstream on this path. 'Release Position' and 'Is Release Position Valid' will also be\npopulated when this signal is set.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Released");
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
        sm_stateManagerOgnOnViewportPressed.removeState(nodeObj.nodeHandle, instanceID);
    }
    bool validate() const {
        return validateNode()
            && inputs.gesture.isValid()
            && inputs.onlyPlayback.isValid()
            && inputs.useNormalizedCoords.isValid()
            && inputs.viewport.isValid()
            && outputs.isReleasePositionValid.isValid()
            && outputs.pressPosition.isValid()
            && outputs.pressed.isValid()
            && outputs.releasePosition.isValid()
            && outputs.released.isValid()
        ;
    }
    void preCompute() {
        if(m_canCachePointers == false) {
            inputs.gesture.invalidateCachedPointer();
            inputs.onlyPlayback.invalidateCachedPointer();
            inputs.useNormalizedCoords.invalidateCachedPointer();
            inputs.viewport.invalidateCachedPointer();
            outputs.isReleasePositionValid.invalidateCachedPointer();
            outputs.pressPosition.invalidateCachedPointer();
            outputs.pressed.invalidateCachedPointer();
            outputs.releasePosition.invalidateCachedPointer();
            outputs.released.invalidateCachedPointer();
            return;
        }
        for(NameToken const& attrib : m_mappedAttributes) {
            if(attrib == inputs::gesture.m_token) {
                inputs.gesture.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::onlyPlayback.m_token) {
                inputs.onlyPlayback.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::useNormalizedCoords.m_token) {
                inputs.useNormalizedCoords.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::viewport.m_token) {
                inputs.viewport.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::isReleasePositionValid.m_token) {
                outputs.isReleasePositionValid.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::pressPosition.m_token) {
                outputs.pressPosition.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::pressed.m_token) {
                outputs.pressed.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::releasePosition.m_token) {
                outputs.releasePosition.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::released.m_token) {
                outputs.released.invalidateCachedPointer();
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
        if( !inputs.gesture.canVectorize()
            || !inputs.onlyPlayback.canVectorize()
            || !inputs.useNormalizedCoords.canVectorize()
            || !inputs.viewport.canVectorize()
            || !outputs.isReleasePositionValid.canVectorize()
            || !outputs.pressPosition.canVectorize()
            || !outputs.pressed.canVectorize()
            || !outputs.releasePosition.canVectorize()
            || !outputs.released.canVectorize()
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
        if(token == inputs::gesture.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.gesture.setHandle(hdl);
            return;
        }
        if(token == inputs::onlyPlayback.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.onlyPlayback.setHandle(hdl);
            return;
        }
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
        if(token == outputs::isReleasePositionValid.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.isReleasePositionValid.setHandle(hdl);
            return;
        }
        if(token == outputs::pressPosition.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.pressPosition.setHandle(hdl);
            return;
        }
        if(token == outputs::pressed.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.pressed.setHandle(hdl);
            return;
        }
        if(token == outputs::releasePosition.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.releasePosition.setHandle(hdl);
            return;
        }
        if(token == outputs::released.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.released.setHandle(hdl);
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
ogn::StateManager OgnOnViewportPressedDatabase::sm_stateManagerOgnOnViewportPressed;
std::tuple<int, int, int> OgnOnViewportPressedDatabase::sm_generatorVersionOgnOnViewportPressed{std::make_tuple(1,79,2)};
std::tuple<int, int, int> OgnOnViewportPressedDatabase::sm_targetVersionOgnOnViewportPressed{std::make_tuple(2,184,5)};
OgnOnViewportPressedDatabase::TokenManager OgnOnViewportPressedDatabase::tokens;
}
using namespace IOgnOnViewportPressed;
#define REGISTER_OGN_NODE() \
namespace { \
    ogn::NodeTypeBootstrapImpl<OgnOnViewportPressed, OgnOnViewportPressedDatabase> s_registration("omni.graph.ui_nodes.OnViewportPressed", 1, "omni.graph.ui_nodes"); \
}
