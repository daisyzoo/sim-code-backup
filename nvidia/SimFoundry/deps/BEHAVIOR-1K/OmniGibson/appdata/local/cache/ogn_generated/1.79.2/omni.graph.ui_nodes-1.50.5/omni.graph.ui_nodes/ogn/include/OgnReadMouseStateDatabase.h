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

namespace OgnReadMouseStateAttributes
{
namespace inputs
{
using mouseElement_t = const NameToken&;
ogn::AttributeInitializer<const NameToken, ogn::kOgnInput> mouseElement("inputs:mouseElement", "token", kExtendedAttributeType_Regular);
using useRelativeCoords_t = const bool&;
ogn::AttributeInitializer<const bool, ogn::kOgnInput> useRelativeCoords("inputs:useRelativeCoords", "bool", kExtendedAttributeType_Regular, false);
}
namespace outputs
{
using coords_t = pxr::GfVec2f&;
ogn::AttributeInitializer<pxr::GfVec2f, ogn::kOgnOutput> coords("outputs:coords", "float2", kExtendedAttributeType_Regular);
using isPressed_t = bool&;
ogn::AttributeInitializer<bool, ogn::kOgnOutput> isPressed("outputs:isPressed", "bool", kExtendedAttributeType_Regular);
using window_t = NameToken&;
ogn::AttributeInitializer<NameToken, ogn::kOgnOutput> window("outputs:window", "token", kExtendedAttributeType_Regular);
}
namespace state
{
}
}
using namespace OgnReadMouseStateAttributes;
namespace IOgnReadMouseState
{
// Reads the current state of the mouse. You can choose which mouse element this node
// is associated with. When mouse element is chosen to be a button, only outputs:isPressed
// is meaningful. When coordinates are chosen, only outputs:coords and outputs:window
// are meaningful.
// Pixel coordinates are the position of the mouse cursor in screen pixel units with
// (0,0) top left. Normalized coordinates are values between 0-1 where 0 is top/left
// and 1 is bottom/right. By default, coordinates are relative to the application window,
// but if 'Use Relative Coords' is set to true, then coordinates are relative to the
// workspace window containing the mouse pointer.
class OgnReadMouseStateDatabase : public omni::graph::core::ogn::OmniGraphDatabase
{
public:
    struct TokenManager
    {
        NameToken LeftButton;
        NameToken RightButton;
        NameToken MiddleButton;
        NameToken ForwardButton;
        NameToken BackButton;
        NameToken MouseCoordsNormalized;
        NameToken MouseCoordsPixel;
    };
    static TokenManager tokens;
    template <typename StateInformation>
    CARB_DEPRECATED("sInternalState is deprecated. Use sSharedState or sPerInstanceState instead")
    static StateInformation& sInternalState(const NodeObj& nodeObj, InstanceIndex index = {kAuthoringGraphIndex}) {
        return sm_stateManagerOgnReadMouseState.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sSharedState(const NodeObj& nodeObj) {
        return sm_stateManagerOgnReadMouseState.getState<StateInformation>(nodeObj.nodeHandle, kAuthoringGraphIndex);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, InstanceIndex index) {
        return sm_stateManagerOgnReadMouseState.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, GraphInstanceID instanceId) {
        return sm_stateManagerOgnReadMouseState.getState<StateInformation>(nodeObj.nodeHandle, instanceId);
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
    static ogn::StateManager sm_stateManagerOgnReadMouseState;
    static std::tuple<int, int, int>sm_generatorVersionOgnReadMouseState;
    static std::tuple<int, int, int>sm_targetVersionOgnReadMouseState;
    static constexpr size_t staticAttributeCount = 7;
    std::vector<ogn::DynamicInput> m_dynamicInputs;
    std::vector<ogn::DynamicOutput> m_dynamicOutputs;
    std::vector<ogn::DynamicState> m_dynamicStates;
    std::vector<NameToken> m_mappedAttributes;
    bool m_canCachePointers{true};

    struct inputsT {
        inputsT(size_t const& offset)
        : mouseElement{offset}
        , useRelativeCoords{offset}
        {}
        ogn::SimpleInput<const NameToken,ogn::kCpu> mouseElement;
        ogn::SimpleInput<const bool,ogn::kCpu> useRelativeCoords;
    } inputs;

    struct outputsT {
        outputsT(size_t const& offset)
        : coords{offset}
        , isPressed{offset}
        , window{offset}
        {}
        ogn::SimpleOutput<pxr::GfVec2f,ogn::kCpu> coords;
        ogn::SimpleOutput<bool,ogn::kCpu> isPressed;
        ogn::SimpleOutput<NameToken,ogn::kCpu> window;
    } outputs;

    //Only use this constructor for temporary stack-allocated object:
    OgnReadMouseStateDatabase(NodeObj const& nodeObjParam)
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
    OgnReadMouseStateDatabase(GraphContextObj const&, NodeObj const& nodeObjParam)
    : OgnReadMouseStateDatabase(nodeObjParam)
    {}

    //Main constructor
    OgnReadMouseStateDatabase(GraphContextObj const* contextObjParam, NodeObj const* nodeObjParam, size_t handleCount)
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
                    inputs::mouseElement.m_token, inputs::useRelativeCoords.m_token
                )
            , kAccordingToContextIndex);
            auto outputDataHandles0 = getAttributesW<
                AttributeDataHandle, AttributeDataHandle, AttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    outputs::coords.m_token, outputs::isPressed.m_token, outputs::window.m_token
                )
            , kAccordingToContextIndex);
            inputs.mouseElement.setContext(contextObj);
            inputs.mouseElement.setHandle(std::get<0>(inputDataHandles0));
            inputs.useRelativeCoords.setContext(contextObj);
            inputs.useRelativeCoords.setHandle(std::get<1>(inputDataHandles0));
            outputs.coords.setContext(contextObj);
            outputs.coords.setHandle(std::get<0>(outputDataHandles0));
            outputs.isPressed.setContext(contextObj);
            outputs.isPressed.setHandle(std::get<1>(outputDataHandles0));
            outputs.window.setContext(contextObj);
            outputs.window.setHandle(std::get<2>(outputDataHandles0));
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
            CARB_LOG_ERROR("IToken not found when initializing omni.graph.ui_nodes.ReadMouseState");
            return;
        }
        auto& iToken{ *iTokenPtr };
        OgnReadMouseStateDatabase::tokens.LeftButton = iToken.getHandle("Left Button");
        OgnReadMouseStateDatabase::tokens.RightButton = iToken.getHandle("Right Button");
        OgnReadMouseStateDatabase::tokens.MiddleButton = iToken.getHandle("Middle Button");
        OgnReadMouseStateDatabase::tokens.ForwardButton = iToken.getHandle("Forward Button");
        OgnReadMouseStateDatabase::tokens.BackButton = iToken.getHandle("Back Button");
        OgnReadMouseStateDatabase::tokens.MouseCoordsNormalized = iToken.getHandle("Normalized Mouse Coordinates");
        OgnReadMouseStateDatabase::tokens.MouseCoordsPixel = iToken.getHandle("Pixel Mouse Coordinates");

        static omni::fabric::Token inputs_mouseElement_token {"Left Button"};
        inputs::mouseElement.setDefault(inputs_mouseElement_token.asTokenC());
        inputs::mouseElement.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::useRelativeCoords.initialize(iToken, *iNodeType, nodeTypeObj);

        outputs::coords.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::isPressed.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::window.initialize(iToken, *iNodeType, nodeTypeObj);

        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExtension, "omni.graph.ui_nodes");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataUiName, "Read Mouse State");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataCategories, "input:mouse");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataDescription, "Reads the current state of the mouse. You can choose which mouse element this node is associated with. When mouse element is chosen to be a button, only outputs:isPressed is meaningful. When coordinates are chosen, only outputs:coords and outputs:window are meaningful.\nPixel coordinates are the position of the mouse cursor in screen pixel units with (0,0) top left. Normalized coordinates are values between 0-1 where 0 is top/left and 1 is bottom/right. By default, coordinates are relative to the application window, but if 'Use Relative Coords' is set to true, then coordinates are relative to the workspace window containing the mouse pointer.");
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
        attr = iNode->getAttributeByToken(nodeObj, inputs::mouseElement.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The mouse input to check the state of");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Mouse Element");
        attr.iAttribute->setMetadata(attr, "displayGroup", "parameters");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokens, "Left Button,Right Button,Middle Button,Forward Button,Back Button,Normalized Mouse Coordinates,Pixel Mouse Coordinates");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokensRaw, "{\"LeftButton\": \"Left Button\", \"RightButton\": \"Right Button\", \"MiddleButton\": \"Middle Button\", \"ForwardButton\": \"Forward Button\", \"BackButton\": \"Back Button\", \"MouseCoordsNormalized\": \"Normalized Mouse Coordinates\", \"MouseCoordsPixel\": \"Pixel Mouse Coordinates\"}");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "\"Left Button\"");
        attr = iNode->getAttributeByToken(nodeObj, inputs::useRelativeCoords.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When true, the output 'coords' is made relative to the workspace window containing the\nmouse pointer instead of the entire application window");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Use Relative Coords");
        attr = iNode->getAttributeByToken(nodeObj, outputs::coords.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The coordinates of the mouse. If the mouse element selected is a button, this will output a zero vector.");
        attr = iNode->getAttributeByToken(nodeObj, outputs::isPressed.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "True if the button is currently pressed, false otherwise. If the mouse element selected\nis a coordinate, this will output false.");
        attr = iNode->getAttributeByToken(nodeObj, outputs::window.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The name of the workspace window containing the mouse pointer if 'Use Relative Coords' is true\nand the mouse element selected is a coordinate");
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
        sm_stateManagerOgnReadMouseState.removeState(nodeObj.nodeHandle, instanceID);
    }
    bool validate() const {
        return validateNode()
            && inputs.mouseElement.isValid()
            && inputs.useRelativeCoords.isValid()
            && outputs.coords.isValid()
            && outputs.isPressed.isValid()
            && outputs.window.isValid()
        ;
    }
    void preCompute() {
        if(m_canCachePointers == false) {
            inputs.mouseElement.invalidateCachedPointer();
            inputs.useRelativeCoords.invalidateCachedPointer();
            outputs.coords.invalidateCachedPointer();
            outputs.isPressed.invalidateCachedPointer();
            outputs.window.invalidateCachedPointer();
            return;
        }
        for(NameToken const& attrib : m_mappedAttributes) {
            if(attrib == inputs::mouseElement.m_token) {
                inputs.mouseElement.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::useRelativeCoords.m_token) {
                inputs.useRelativeCoords.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::coords.m_token) {
                outputs.coords.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::isPressed.m_token) {
                outputs.isPressed.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::window.m_token) {
                outputs.window.invalidateCachedPointer();
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
        if( !inputs.mouseElement.canVectorize()
            || !inputs.useRelativeCoords.canVectorize()
            || !outputs.coords.canVectorize()
            || !outputs.isPressed.canVectorize()
            || !outputs.window.canVectorize()
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
        if(token == inputs::mouseElement.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.mouseElement.setHandle(hdl);
            return;
        }
        if(token == inputs::useRelativeCoords.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.useRelativeCoords.setHandle(hdl);
            return;
        }
        if(token == outputs::coords.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.coords.setHandle(hdl);
            return;
        }
        if(token == outputs::isPressed.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.isPressed.setHandle(hdl);
            return;
        }
        if(token == outputs::window.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.window.setHandle(hdl);
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
ogn::StateManager OgnReadMouseStateDatabase::sm_stateManagerOgnReadMouseState;
std::tuple<int, int, int> OgnReadMouseStateDatabase::sm_generatorVersionOgnReadMouseState{std::make_tuple(1,79,2)};
std::tuple<int, int, int> OgnReadMouseStateDatabase::sm_targetVersionOgnReadMouseState{std::make_tuple(2,184,5)};
OgnReadMouseStateDatabase::TokenManager OgnReadMouseStateDatabase::tokens;
}
using namespace IOgnReadMouseState;
#define REGISTER_OGN_NODE() \
namespace { \
    ogn::NodeTypeBootstrapImpl<OgnReadMouseState, OgnReadMouseStateDatabase> s_registration("omni.graph.ui_nodes.ReadMouseState", 1, "omni.graph.ui_nodes"); \
}
