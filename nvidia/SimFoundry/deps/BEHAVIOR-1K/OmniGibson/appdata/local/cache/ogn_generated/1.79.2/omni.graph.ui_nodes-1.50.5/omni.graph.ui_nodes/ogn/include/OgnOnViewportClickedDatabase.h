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

namespace OgnOnViewportClickedAttributes
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
using clicked_t = uint32_t&;
ogn::AttributeInitializer<uint32_t, ogn::kOgnOutput> clicked("outputs:clicked", "execution", kExtendedAttributeType_Regular);
using position_t = pxr::GfVec2d&;
ogn::AttributeInitializer<pxr::GfVec2d, ogn::kOgnOutput> position("outputs:position", "double2", kExtendedAttributeType_Regular);
}
namespace state
{
}
}
using namespace OgnOnViewportClickedAttributes;
namespace IOgnOnViewportClicked
{
// Event node which fires when a click event occurs in the specified viewport. A press
// event differs from a click event only in timing. Press events are held down while
// click events are pressed and then immediately (within a small amount of time) released.
// Note that viewport mouse events must be enabled on the specified viewport using a
// SetViewportMode node.
class OgnOnViewportClickedDatabase : public omni::graph::core::ogn::OmniGraphDatabase
{
public:
    struct TokenManager
    {
        NameToken LeftMouseClick;
        NameToken RightMouseClick;
        NameToken MiddleMouseClick;
    };
    static TokenManager tokens;
    template <typename StateInformation>
    CARB_DEPRECATED("sInternalState is deprecated. Use sSharedState or sPerInstanceState instead")
    static StateInformation& sInternalState(const NodeObj& nodeObj, InstanceIndex index = {kAuthoringGraphIndex}) {
        return sm_stateManagerOgnOnViewportClicked.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sSharedState(const NodeObj& nodeObj) {
        return sm_stateManagerOgnOnViewportClicked.getState<StateInformation>(nodeObj.nodeHandle, kAuthoringGraphIndex);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, InstanceIndex index) {
        return sm_stateManagerOgnOnViewportClicked.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, GraphInstanceID instanceId) {
        return sm_stateManagerOgnOnViewportClicked.getState<StateInformation>(nodeObj.nodeHandle, instanceId);
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
    static ogn::StateManager sm_stateManagerOgnOnViewportClicked;
    static std::tuple<int, int, int>sm_generatorVersionOgnOnViewportClicked;
    static std::tuple<int, int, int>sm_targetVersionOgnOnViewportClicked;
    static constexpr size_t staticAttributeCount = 8;
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
        : clicked{offset,AttributeRole::eExecution}
        , position{offset}
        {}
        ogn::SimpleOutput<uint32_t,ogn::kCpu> clicked;
        ogn::SimpleOutput<pxr::GfVec2d,ogn::kCpu> position;
    } outputs;

    //Only use this constructor for temporary stack-allocated object:
    OgnOnViewportClickedDatabase(NodeObj const& nodeObjParam)
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
    OgnOnViewportClickedDatabase(GraphContextObj const&, NodeObj const& nodeObjParam)
    : OgnOnViewportClickedDatabase(nodeObjParam)
    {}

    //Main constructor
    OgnOnViewportClickedDatabase(GraphContextObj const* contextObjParam, NodeObj const* nodeObjParam, size_t handleCount)
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
                AttributeDataHandle, AttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    outputs::clicked.m_token, outputs::position.m_token
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
            outputs.clicked.setContext(contextObj);
            outputs.clicked.setHandle(std::get<0>(outputDataHandles0));
            outputs.position.setContext(contextObj);
            outputs.position.setHandle(std::get<1>(outputDataHandles0));
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
            CARB_LOG_ERROR("IToken not found when initializing omni.graph.ui_nodes.OnViewportClicked");
            return;
        }
        auto& iToken{ *iTokenPtr };
        OgnOnViewportClickedDatabase::tokens.LeftMouseClick = iToken.getHandle("Left Mouse Click");
        OgnOnViewportClickedDatabase::tokens.RightMouseClick = iToken.getHandle("Right Mouse Click");
        OgnOnViewportClickedDatabase::tokens.MiddleMouseClick = iToken.getHandle("Middle Mouse Click");

        static omni::fabric::Token inputs_gesture_token {"Left Mouse Click"};
        inputs::gesture.setDefault(inputs_gesture_token.asTokenC());
        static omni::fabric::Token inputs_viewport_token {"Viewport"};
        inputs::viewport.setDefault(inputs_viewport_token.asTokenC());
        inputs::gesture.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::onlyPlayback.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::useNormalizedCoords.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::viewport.initialize(iToken, *iNodeType, nodeTypeObj);

        outputs::clicked.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::position.initialize(iToken, *iNodeType, nodeTypeObj);

        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExtension, "omni.graph.ui_nodes");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataUiName, "On Viewport Clicked (BETA)");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataCategories, "graph:action,ui");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataDescription, "Event node which fires when a click event occurs in the specified viewport. A press event differs from a click event only in timing. Press events are held down while click events are pressed and then immediately (within a small amount of time) released. Note that viewport mouse events must be enabled on the specified viewport using a SetViewportMode node.");
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
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The input gesture to trigger viewport click events.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Gesture");
        attr.iAttribute->setMetadata(attr, "displayGroup", "parameters");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokens, "Left Mouse Click,Right Mouse Click,Middle Mouse Click");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokensRaw, "{\"LeftMouseClick\": \"Left Mouse Click\", \"RightMouseClick\": \"Right Mouse Click\", \"MiddleMouseClick\": \"Middle Mouse Click\"}");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "\"Left Mouse Click\"");
        attr = iNode->getAttributeByToken(nodeObj, inputs::onlyPlayback.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When true, the node is only executed while the Stage is being played.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Only Simulate On Play");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "true");
        attr = iNode->getAttributeByToken(nodeObj, inputs::useNormalizedCoords.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When true, the components of the 2D position output are scaled to between 0 and 1,\nwhere 0 is top/left and 1 is bottom/right.\nWhen false, components are in viewport render resolution pixels.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Use Normalized Coords");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "false");
        attr = iNode->getAttributeByToken(nodeObj, inputs::viewport.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Name of the viewport window to watch for click events.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Viewport");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "\"Viewport\"");
        attr = iNode->getAttributeByToken(nodeObj, outputs::clicked.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When the specified input gesture triggers a click event in the specified viewport,\nsignal to the graph that execution can continue downstream.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Clicked");
        attr = iNode->getAttributeByToken(nodeObj, outputs::position.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The position at which the click event occurred.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Position");
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
        sm_stateManagerOgnOnViewportClicked.removeState(nodeObj.nodeHandle, instanceID);
    }
    bool validate() const {
        return validateNode()
            && inputs.gesture.isValid()
            && inputs.onlyPlayback.isValid()
            && inputs.useNormalizedCoords.isValid()
            && inputs.viewport.isValid()
            && outputs.clicked.isValid()
            && outputs.position.isValid()
        ;
    }
    void preCompute() {
        if(m_canCachePointers == false) {
            inputs.gesture.invalidateCachedPointer();
            inputs.onlyPlayback.invalidateCachedPointer();
            inputs.useNormalizedCoords.invalidateCachedPointer();
            inputs.viewport.invalidateCachedPointer();
            outputs.clicked.invalidateCachedPointer();
            outputs.position.invalidateCachedPointer();
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
            if(attrib == outputs::clicked.m_token) {
                outputs.clicked.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::position.m_token) {
                outputs.position.invalidateCachedPointer();
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
            || !outputs.clicked.canVectorize()
            || !outputs.position.canVectorize()
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
        if(token == outputs::clicked.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.clicked.setHandle(hdl);
            return;
        }
        if(token == outputs::position.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.position.setHandle(hdl);
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
ogn::StateManager OgnOnViewportClickedDatabase::sm_stateManagerOgnOnViewportClicked;
std::tuple<int, int, int> OgnOnViewportClickedDatabase::sm_generatorVersionOgnOnViewportClicked{std::make_tuple(1,79,2)};
std::tuple<int, int, int> OgnOnViewportClickedDatabase::sm_targetVersionOgnOnViewportClicked{std::make_tuple(2,184,5)};
OgnOnViewportClickedDatabase::TokenManager OgnOnViewportClickedDatabase::tokens;
}
using namespace IOgnOnViewportClicked;
#define REGISTER_OGN_NODE() \
namespace { \
    ogn::NodeTypeBootstrapImpl<OgnOnViewportClicked, OgnOnViewportClickedDatabase> s_registration("omni.graph.ui_nodes.OnViewportClicked", 1, "omni.graph.ui_nodes"); \
}
