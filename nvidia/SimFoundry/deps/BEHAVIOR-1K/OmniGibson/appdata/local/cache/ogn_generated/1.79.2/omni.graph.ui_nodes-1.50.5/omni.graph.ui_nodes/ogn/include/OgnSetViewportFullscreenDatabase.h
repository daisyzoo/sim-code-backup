#pragma once

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

namespace OgnSetViewportFullscreenAttributes
{
namespace inputs
{
using exec_t = const uint32_t&;
ogn::AttributeInitializer<const uint32_t, ogn::kOgnInput> exec("inputs:exec", "execution", kExtendedAttributeType_Regular);
using mode_t = const NameToken&;
ogn::AttributeInitializer<const NameToken, ogn::kOgnInput> mode("inputs:mode", "token", kExtendedAttributeType_Regular);
}
namespace outputs
{
using exec_t = uint32_t&;
ogn::AttributeInitializer<uint32_t, ogn::kOgnOutput> exec("outputs:exec", "execution", kExtendedAttributeType_Regular);
}
namespace state
{
}
}
using namespace OgnSetViewportFullscreenAttributes;
namespace IOgnSetViewportFullscreen
{
// Toggles fullscreen on/off for viewport(s) and visibility on/off for all other panes.
class OgnSetViewportFullscreenDatabase : public omni::graph::core::ogn::OmniGraphDatabase
{
public:
    struct TokenManager
    {
        NameToken Default;
        NameToken Fullscreen;
        NameToken HideUI;
    };
    static TokenManager tokens;
    template <typename StateInformation>
    CARB_DEPRECATED("sInternalState is deprecated. Use sSharedState or sPerInstanceState instead")
    static StateInformation& sInternalState(const NodeObj& nodeObj, InstanceIndex index = {kAuthoringGraphIndex}) {
        return sm_stateManagerOgnSetViewportFullscreen.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sSharedState(const NodeObj& nodeObj) {
        return sm_stateManagerOgnSetViewportFullscreen.getState<StateInformation>(nodeObj.nodeHandle, kAuthoringGraphIndex);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, InstanceIndex index) {
        return sm_stateManagerOgnSetViewportFullscreen.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, GraphInstanceID instanceId) {
        return sm_stateManagerOgnSetViewportFullscreen.getState<StateInformation>(nodeObj.nodeHandle, instanceId);
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
    static ogn::StateManager sm_stateManagerOgnSetViewportFullscreen;
    static std::tuple<int, int, int>sm_generatorVersionOgnSetViewportFullscreen;
    static std::tuple<int, int, int>sm_targetVersionOgnSetViewportFullscreen;
    static constexpr size_t staticAttributeCount = 5;
    std::vector<ogn::DynamicInput> m_dynamicInputs;
    std::vector<ogn::DynamicOutput> m_dynamicOutputs;
    std::vector<ogn::DynamicState> m_dynamicStates;
    std::vector<NameToken> m_mappedAttributes;
    bool m_canCachePointers{true};

    struct inputsT {
        inputsT(size_t const& offset)
        : exec{offset,AttributeRole::eExecution}
        , mode{offset}
        {}
        ogn::SimpleInput<const uint32_t,ogn::kCpu> exec;
        ogn::SimpleInput<const NameToken,ogn::kCpu> mode;
    } inputs;

    struct outputsT {
        outputsT(size_t const& offset)
        : exec{offset,AttributeRole::eExecution}
        {}
        ogn::SimpleOutput<uint32_t,ogn::kCpu> exec;
    } outputs;

    //Only use this constructor for temporary stack-allocated object:
    OgnSetViewportFullscreenDatabase(NodeObj const& nodeObjParam)
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
    OgnSetViewportFullscreenDatabase(GraphContextObj const&, NodeObj const& nodeObjParam)
    : OgnSetViewportFullscreenDatabase(nodeObjParam)
    {}

    //Main constructor
    OgnSetViewportFullscreenDatabase(GraphContextObj const* contextObjParam, NodeObj const* nodeObjParam, size_t handleCount)
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
                    inputs::exec.m_token, inputs::mode.m_token
                )
            , kAccordingToContextIndex);
            auto outputDataHandles0 = getAttributesW<
                AttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    outputs::exec.m_token
                )
            , kAccordingToContextIndex);
            inputs.exec.setContext(contextObj);
            inputs.exec.setHandle(std::get<0>(inputDataHandles0));
            inputs.mode.setContext(contextObj);
            inputs.mode.setHandle(std::get<1>(inputDataHandles0));
            outputs.exec.setContext(contextObj);
            outputs.exec.setHandle(std::get<0>(outputDataHandles0));
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
            CARB_LOG_ERROR("IToken not found when initializing omni.graph.ui_nodes.SetViewportFullscreen");
            return;
        }
        auto& iToken{ *iTokenPtr };
        OgnSetViewportFullscreenDatabase::tokens.Default = iToken.getHandle("Default");
        OgnSetViewportFullscreenDatabase::tokens.Fullscreen = iToken.getHandle("Fullscreen");
        OgnSetViewportFullscreenDatabase::tokens.HideUI = iToken.getHandle("Hide UI");

        static omni::fabric::Token inputs_mode_token {"Default"};
        inputs::mode.setDefault(inputs_mode_token.asTokenC());
        inputs::exec.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::mode.initialize(iToken, *iNodeType, nodeTypeObj);

        outputs::exec.initialize(iToken, *iNodeType, nodeTypeObj);

        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExtension, "omni.graph.ui_nodes");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataUiName, "Set Viewport Fullscreen");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataCategories, "graph:action,viewport");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataDescription, "Toggles fullscreen on/off for viewport(s) and visibility on/off for all other panes.");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExclusions, "tests");
        auto __schedulingInfo = nodeTypeObj.iNodeType->getSchedulingHints(nodeTypeObj);
        CARB_ASSERT(__schedulingInfo, "Could not acquire the scheduling hints");
        if (__schedulingInfo)
        {
            __schedulingInfo->setDataAccess(eAccessLocation::eUsd, eAccessType::eWrite);
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
        attr = iNode->getAttributeByToken(nodeObj, inputs::exec.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Signal to the graph that this node is ready to be executed.");
        attr = iNode->getAttributeByToken(nodeObj, inputs::mode.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The mode to toggle fullscreen on/off for viewport(s) and visibility on/off for all other panes:\n\n\"Default\" - Windowed viewport(s) with all other panes shown.\n\"Fullscreen\" - Fullscreen viewport(s) with all other panes hidden.\n\"Hide UI\" - Windowed viewport(s) with all other panes hidden.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Mode");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokens, "Default,Fullscreen,Hide UI");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokensRaw, "{\"Default\": \"Default\", \"Fullscreen\": \"Fullscreen\", \"HideUI\": \"Hide UI\"}");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "\"Default\"");
        attr = iNode->getAttributeByToken(nodeObj, outputs::exec.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Signal to the graph that execution can continue downstream.");
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
        sm_stateManagerOgnSetViewportFullscreen.removeState(nodeObj.nodeHandle, instanceID);
    }
    bool validate() const {
        return validateNode()
            && inputs.exec.isValid()
            && inputs.mode.isValid()
            && outputs.exec.isValid()
        ;
    }
    void preCompute() {
        if(m_canCachePointers == false) {
            inputs.exec.invalidateCachedPointer();
            inputs.mode.invalidateCachedPointer();
            outputs.exec.invalidateCachedPointer();
            return;
        }
        for(NameToken const& attrib : m_mappedAttributes) {
            if(attrib == inputs::exec.m_token) {
                inputs.exec.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::mode.m_token) {
                inputs.mode.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::exec.m_token) {
                outputs.exec.invalidateCachedPointer();
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
        if( !inputs.exec.canVectorize()
            || !inputs.mode.canVectorize()
            || !outputs.exec.canVectorize()
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
        if(token == inputs::exec.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.exec.setHandle(hdl);
            return;
        }
        if(token == inputs::mode.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.mode.setHandle(hdl);
            return;
        }
        if(token == outputs::exec.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.exec.setHandle(hdl);
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
ogn::StateManager OgnSetViewportFullscreenDatabase::sm_stateManagerOgnSetViewportFullscreen;
std::tuple<int, int, int> OgnSetViewportFullscreenDatabase::sm_generatorVersionOgnSetViewportFullscreen{std::make_tuple(1,79,2)};
std::tuple<int, int, int> OgnSetViewportFullscreenDatabase::sm_targetVersionOgnSetViewportFullscreen{std::make_tuple(2,184,5)};
OgnSetViewportFullscreenDatabase::TokenManager OgnSetViewportFullscreenDatabase::tokens;
}
using namespace IOgnSetViewportFullscreen;
#define REGISTER_OGN_NODE() \
namespace { \
    ogn::NodeTypeBootstrapImpl<OgnSetViewportFullscreen, OgnSetViewportFullscreenDatabase> s_registration("omni.graph.ui_nodes.SetViewportFullscreen", 1, "omni.graph.ui_nodes"); \
}
