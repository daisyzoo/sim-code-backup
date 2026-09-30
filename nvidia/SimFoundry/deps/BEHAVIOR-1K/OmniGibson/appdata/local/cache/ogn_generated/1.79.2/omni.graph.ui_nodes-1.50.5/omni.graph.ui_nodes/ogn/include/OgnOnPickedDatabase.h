#pragma once

#include <omni/graph/core/ogn/UsdTypes.h>
using namespace pxr;

#include <omni/graph/core/ISchedulingHints2.h>
#include <omni/graph/core/IInternal.h>
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
#include <array>
#include <omni/graph/core/Type.h>
#include <omni/graph/core/ogn/ArrayAttribute.h>
#include <omni/graph/core/ogn/SimpleAttribute.h>
#include <omni/graph/core/tuple.h>

namespace OgnOnPickedAttributes
{
namespace inputs
{
using gesture_t = const NameToken&;
ogn::AttributeInitializer<const NameToken, ogn::kOgnInput> gesture("inputs:gesture", "token", kExtendedAttributeType_Regular);
using onlyPlayback_t = const bool&;
ogn::AttributeInitializer<const bool, ogn::kOgnInput> onlyPlayback("inputs:onlyPlayback", "bool", kExtendedAttributeType_Regular, true);
using trackedPrims_t = const ogn::const_array<TargetPath>&;
ogn::AttributeInitializer<const TargetPath*, ogn::kOgnInput> trackedPrims("inputs:trackedPrims", "target", kExtendedAttributeType_Regular, nullptr, 0);
using viewport_t = const NameToken&;
ogn::AttributeInitializer<const NameToken, ogn::kOgnInput> viewport("inputs:viewport", "token", kExtendedAttributeType_Regular);
}
namespace outputs
{
using isTrackedPrimPicked_t = bool&;
ogn::AttributeInitializer<bool, ogn::kOgnOutput> isTrackedPrimPicked("outputs:isTrackedPrimPicked", "bool", kExtendedAttributeType_Regular);
using missed_t = uint32_t&;
ogn::AttributeInitializer<uint32_t, ogn::kOgnOutput> missed("outputs:missed", "execution", kExtendedAttributeType_Regular);
using picked_t = uint32_t&;
ogn::AttributeInitializer<uint32_t, ogn::kOgnOutput> picked("outputs:picked", "execution", kExtendedAttributeType_Regular);
using pickedPrim_t = ogn::array<TargetPath>&;
ogn::AttributeInitializer<TargetPath*, ogn::kOgnOutput> pickedPrim("outputs:pickedPrim", "target", kExtendedAttributeType_Regular, nullptr, 0);
using pickedPrimPath_t = NameToken&;
ogn::AttributeInitializer<NameToken, ogn::kOgnOutput> pickedPrimPath("outputs:pickedPrimPath", "token", kExtendedAttributeType_Regular);
using pickedWorldPos_t = pxr::GfVec3d&;
ogn::AttributeInitializer<pxr::GfVec3d, ogn::kOgnOutput> pickedWorldPos("outputs:pickedWorldPos", "point3d", kExtendedAttributeType_Regular);
using trackedPrimPaths_t = ogn::array<NameToken>&;
ogn::AttributeInitializer<NameToken*, ogn::kOgnOutput> trackedPrimPaths("outputs:trackedPrimPaths", "token[]", kExtendedAttributeType_Regular, nullptr, 0);
}
namespace state
{
}
}
using namespace OgnOnPickedAttributes;
namespace IOgnOnPicked
{
// Event node which fires when a picking event occurs in the specified viewport. Note
// that picking events must be enabled on the specified viewport using a SetViewportMode
// node.
class OgnOnPickedDatabase : public omni::graph::core::ogn::OmniGraphDatabase
{
public:
    struct TokenManager
    {
        NameToken LeftMouseClick;
        NameToken RightMouseClick;
        NameToken MiddleMouseClick;
        NameToken LeftMousePress;
        NameToken RightMousePress;
        NameToken MiddleMousePress;
    };
    static TokenManager tokens;
    template <typename StateInformation>
    CARB_DEPRECATED("sInternalState is deprecated. Use sSharedState or sPerInstanceState instead")
    static StateInformation& sInternalState(const NodeObj& nodeObj, InstanceIndex index = {kAuthoringGraphIndex}) {
        return sm_stateManagerOgnOnPicked.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sSharedState(const NodeObj& nodeObj) {
        return sm_stateManagerOgnOnPicked.getState<StateInformation>(nodeObj.nodeHandle, kAuthoringGraphIndex);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, InstanceIndex index) {
        return sm_stateManagerOgnOnPicked.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, GraphInstanceID instanceId) {
        return sm_stateManagerOgnOnPicked.getState<StateInformation>(nodeObj.nodeHandle, instanceId);
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
    static ogn::StateManager sm_stateManagerOgnOnPicked;
    static std::tuple<int, int, int>sm_generatorVersionOgnOnPicked;
    static std::tuple<int, int, int>sm_targetVersionOgnOnPicked;
    static constexpr size_t staticAttributeCount = 13;
    std::vector<ogn::DynamicInput> m_dynamicInputs;
    std::vector<ogn::DynamicOutput> m_dynamicOutputs;
    std::vector<ogn::DynamicState> m_dynamicStates;
    std::vector<NameToken> m_mappedAttributes;
    bool m_canCachePointers{true};

    struct inputsT {
        inputsT(size_t const& offset)
        : gesture{offset}
        , onlyPlayback{offset}
        , trackedPrims{offset,AttributeRole::eTarget}
        , viewport{offset}
        {}
        ogn::SimpleInput<const NameToken,ogn::kCpu> gesture;
        ogn::SimpleInput<const bool,ogn::kCpu> onlyPlayback;
        ogn::ArrayInput<const TargetPath,ogn::kCpu> trackedPrims;
        bool has_trackedPrims() const { return trackedPrims.isValid(); };
        ogn::SimpleInput<const NameToken,ogn::kCpu> viewport;
    } inputs;

    struct outputsT {
        outputsT(size_t const& offset)
        : isTrackedPrimPicked{offset}
        , missed{offset,AttributeRole::eExecution}
        , picked{offset,AttributeRole::eExecution}
        , pickedPrim{offset,AttributeRole::eTarget}
        , pickedPrimPath{offset}
        , pickedWorldPos{offset,AttributeRole::ePosition}
        , trackedPrimPaths{offset}
        {}
        ogn::SimpleOutput<bool,ogn::kCpu> isTrackedPrimPicked;
        ogn::SimpleOutput<uint32_t,ogn::kCpu> missed;
        ogn::SimpleOutput<uint32_t,ogn::kCpu> picked;
        ogn::ArrayOutput<TargetPath,ogn::kCpu> pickedPrim;
        ogn::SimpleOutput<NameToken,ogn::kCpu> pickedPrimPath;
        ogn::SimpleOutput<pxr::GfVec3d,ogn::kCpu> pickedWorldPos;
        ogn::ArrayOutput<NameToken,ogn::kCpu> trackedPrimPaths;
    } outputs;

    //Only use this constructor for temporary stack-allocated object:
    OgnOnPickedDatabase(NodeObj const& nodeObjParam)
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
    OgnOnPickedDatabase(GraphContextObj const&, NodeObj const& nodeObjParam)
    : OgnOnPickedDatabase(nodeObjParam)
    {}

    //Main constructor
    OgnOnPickedDatabase(GraphContextObj const* contextObjParam, NodeObj const* nodeObjParam, size_t handleCount)
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
                    inputs::gesture.m_token, inputs::onlyPlayback.m_token, inputs::trackedPrims.m_token, inputs::viewport.m_token
                )
            , kAccordingToContextIndex);
            auto outputDataHandles0 = getAttributesW<
                AttributeDataHandle, AttributeDataHandle, AttributeDataHandle, AttributeDataHandle,
                AttributeDataHandle, AttributeDataHandle, AttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    outputs::isTrackedPrimPicked.m_token, outputs::missed.m_token, outputs::picked.m_token, outputs::pickedPrim.m_token,
                    outputs::pickedPrimPath.m_token, outputs::pickedWorldPos.m_token, outputs::trackedPrimPaths.m_token
                )
            , kAccordingToContextIndex);
            inputs.gesture.setContext(contextObj);
            inputs.gesture.setHandle(std::get<0>(inputDataHandles0));
            inputs.onlyPlayback.setContext(contextObj);
            inputs.onlyPlayback.setHandle(std::get<1>(inputDataHandles0));
            inputs.trackedPrims.setContext(contextObj);
            inputs.trackedPrims.setHandle(std::get<2>(inputDataHandles0));
            inputs.viewport.setContext(contextObj);
            inputs.viewport.setHandle(std::get<3>(inputDataHandles0));
            outputs.isTrackedPrimPicked.setContext(contextObj);
            outputs.isTrackedPrimPicked.setHandle(std::get<0>(outputDataHandles0));
            outputs.missed.setContext(contextObj);
            outputs.missed.setHandle(std::get<1>(outputDataHandles0));
            outputs.picked.setContext(contextObj);
            outputs.picked.setHandle(std::get<2>(outputDataHandles0));
            outputs.pickedPrim.setContext(contextObj);
            outputs.pickedPrim.setHandle(std::get<3>(outputDataHandles0));
            outputs.pickedPrimPath.setContext(contextObj);
            outputs.pickedPrimPath.setHandle(std::get<4>(outputDataHandles0));
            outputs.pickedWorldPos.setContext(contextObj);
            outputs.pickedWorldPos.setHandle(std::get<5>(outputDataHandles0));
            outputs.trackedPrimPaths.setContext(contextObj);
            outputs.trackedPrimPaths.setHandle(std::get<6>(outputDataHandles0));
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
            CARB_LOG_ERROR("IToken not found when initializing omni.graph.ui_nodes.OnPicked");
            return;
        }
        auto& iToken{ *iTokenPtr };
        OgnOnPickedDatabase::tokens.LeftMouseClick = iToken.getHandle("Left Mouse Click");
        OgnOnPickedDatabase::tokens.RightMouseClick = iToken.getHandle("Right Mouse Click");
        OgnOnPickedDatabase::tokens.MiddleMouseClick = iToken.getHandle("Middle Mouse Click");
        OgnOnPickedDatabase::tokens.LeftMousePress = iToken.getHandle("Left Mouse Press");
        OgnOnPickedDatabase::tokens.RightMousePress = iToken.getHandle("Right Mouse Press");
        OgnOnPickedDatabase::tokens.MiddleMousePress = iToken.getHandle("Middle Mouse Press");

        static omni::fabric::Token inputs_gesture_token {"Left Mouse Click"};
        inputs::gesture.setDefault(inputs_gesture_token.asTokenC());
        static omni::fabric::Token inputs_viewport_token {"Viewport"};
        inputs::viewport.setDefault(inputs_viewport_token.asTokenC());
        inputs::gesture.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::onlyPlayback.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::trackedPrims.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::viewport.initialize(iToken, *iNodeType, nodeTypeObj);

        outputs::isTrackedPrimPicked.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::missed.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::picked.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::pickedPrim.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::pickedPrimPath.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::pickedWorldPos.initialize(iToken, *iNodeType, nodeTypeObj);
        outputs::trackedPrimPaths.initialize(iToken, *iNodeType, nodeTypeObj);

        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExtension, "omni.graph.ui_nodes");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataUiName, "On Picked (BETA)");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataCategories, "graph:action,ui");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataDescription, "Event node which fires when a picking event occurs in the specified viewport. Note that picking events must be enabled on the specified viewport using a SetViewportMode node.");
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
        const IInternal* iInternal = carb::getCachedInterface<omni::graph::core::IInternal>();
        if( ! iInternal ) {
            CARB_LOG_ERROR("IInternal not found when initializing omni.graph.ui_nodes.OnPicked");
            return;
        }
        AttributeObj attr;
        attr = iNode->getAttributeByToken(nodeObj, inputs::gesture.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The input gesture to trigger a picking event");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Gesture");
        attr.iAttribute->setMetadata(attr, "displayGroup", "parameters");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokens, "Left Mouse Click,Right Mouse Click,Middle Mouse Click,Left Mouse Press,Right Mouse Press,Middle Mouse Press");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowedTokensRaw, "{\"LeftMouseClick\": \"Left Mouse Click\", \"RightMouseClick\": \"Right Mouse Click\", \"MiddleMouseClick\": \"Middle Mouse Click\", \"LeftMousePress\": \"Left Mouse Press\", \"RightMousePress\": \"Right Mouse Press\", \"MiddleMousePress\": \"Middle Mouse Press\"}");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "\"Left Mouse Click\"");
        attr = iNode->getAttributeByToken(nodeObj, inputs::onlyPlayback.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When true, the node is only executed while Stage is being played.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Only Simulate On Play");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "true");
        attr = iNode->getAttributeByToken(nodeObj, inputs::trackedPrims.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Optionally specify a set of tracked prims that will cause 'Picked' to fire when picked");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Tracked Prims");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataAllowMultiInputs, "1");
        attr.iAttribute->setIsOptionalForCompute(attr, true);
        attr = iNode->getAttributeByToken(nodeObj, inputs::viewport.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Name of the viewport window to watch for picking events");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Viewport");
        attr.iAttribute->setMetadata(attr, kOgnMetadataLiteralOnly, "1");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "\"Viewport\"");
        attr = iNode->getAttributeByToken(nodeObj, outputs::isTrackedPrimPicked.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "True if a tracked prim got picked, or if any prim got picked if no tracked prims are specified\n(will always be true when 'Picked' fires, and false when 'Missed' fires)");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Is Tracked Prim Picked");
        attr = iNode->getAttributeByToken(nodeObj, outputs::missed.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When an attempted picking did not pick a tracked prim,\nor when nothing gets picked if no tracked prims are specified,\nsignal to the graph that execution can continue downstream on this path.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Missed");
        attr = iNode->getAttributeByToken(nodeObj, outputs::picked.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When a tracked prim is picked,\nor when any prim is picked if no tracked prims are specified,\nsignal to the graph that execution can continue downstream on this path.");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Picked");
        attr = iNode->getAttributeByToken(nodeObj, outputs::pickedPrim.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The picked prim, or an empty target if nothing got picked");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Picked Prim");
        attr = iNode->getAttributeByToken(nodeObj, outputs::pickedPrimPath.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The path of the picked prim, or an empty string if nothing got picked");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Picked Prim Path");
        iInternal->deprecateAttribute(attr, "Use the pickedPrim output instead");
        attr = iNode->getAttributeByToken(nodeObj, outputs::pickedWorldPos.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The XYZ-coordinates of the point in world space at which the prim got picked,\nor (0,0,0) if nothing got picked");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Picked World Position");
        attr = iNode->getAttributeByToken(nodeObj, outputs::trackedPrimPaths.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "A list of the paths of the prims specified in 'Tracked Prims'");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Tracked Prim Paths");
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
        sm_stateManagerOgnOnPicked.removeState(nodeObj.nodeHandle, instanceID);
    }
    bool validate() const {
        return validateNode()
            && inputs.gesture.isValid()
            && inputs.onlyPlayback.isValid()
            && inputs.viewport.isValid()
            && outputs.isTrackedPrimPicked.isValid()
            && outputs.missed.isValid()
            && outputs.picked.isValid()
            && outputs.pickedPrim.isValid()
            && outputs.pickedPrimPath.isValid()
            && outputs.pickedWorldPos.isValid()
            && outputs.trackedPrimPaths.isValid()
        ;
    }
    void preCompute() {
        if(m_canCachePointers == false) {
            inputs.gesture.invalidateCachedPointer();
            inputs.onlyPlayback.invalidateCachedPointer();
            inputs.trackedPrims.invalidateCachedPointer();
            inputs.viewport.invalidateCachedPointer();
            outputs.isTrackedPrimPicked.invalidateCachedPointer();
            outputs.missed.invalidateCachedPointer();
            outputs.picked.invalidateCachedPointer();
            outputs.pickedPrim.invalidateCachedPointer();
            outputs.pickedPrimPath.invalidateCachedPointer();
            outputs.pickedWorldPos.invalidateCachedPointer();
            outputs.trackedPrimPaths.invalidateCachedPointer();
            return;
        }
        inputs.trackedPrims.invalidateCachedPointer();
        outputs.pickedPrim.invalidateCachedPointer();
        outputs.trackedPrimPaths.invalidateCachedPointer();
        for(NameToken const& attrib : m_mappedAttributes) {
            if(attrib == inputs::gesture.m_token) {
                inputs.gesture.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::onlyPlayback.m_token) {
                inputs.onlyPlayback.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::trackedPrims.m_token) {
                inputs.trackedPrims.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::viewport.m_token) {
                inputs.viewport.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::isTrackedPrimPicked.m_token) {
                outputs.isTrackedPrimPicked.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::missed.m_token) {
                outputs.missed.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::picked.m_token) {
                outputs.picked.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::pickedPrim.m_token) {
                outputs.pickedPrim.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::pickedPrimPath.m_token) {
                outputs.pickedPrimPath.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::pickedWorldPos.m_token) {
                outputs.pickedWorldPos.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::trackedPrimPaths.m_token) {
                outputs.trackedPrimPaths.invalidateCachedPointer();
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
            || !inputs.viewport.canVectorize()
            || !outputs.isTrackedPrimPicked.canVectorize()
            || !outputs.missed.canVectorize()
            || !outputs.picked.canVectorize()
            || !outputs.pickedPrimPath.canVectorize()
            || !outputs.pickedWorldPos.canVectorize()
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
        if(token == inputs::trackedPrims.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.trackedPrims.setHandle(hdl);
            return;
        }
        if(token == inputs::viewport.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.viewport.setHandle(hdl);
            return;
        }
        if(token == outputs::isTrackedPrimPicked.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.isTrackedPrimPicked.setHandle(hdl);
            return;
        }
        if(token == outputs::missed.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.missed.setHandle(hdl);
            return;
        }
        if(token == outputs::picked.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.picked.setHandle(hdl);
            return;
        }
        if(token == outputs::pickedPrim.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.pickedPrim.setHandle(hdl);
            return;
        }
        if(token == outputs::pickedPrimPath.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.pickedPrimPath.setHandle(hdl);
            return;
        }
        if(token == outputs::pickedWorldPos.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.pickedWorldPos.setHandle(hdl);
            return;
        }
        if(token == outputs::trackedPrimPaths.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.trackedPrimPaths.setHandle(hdl);
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
ogn::StateManager OgnOnPickedDatabase::sm_stateManagerOgnOnPicked;
std::tuple<int, int, int> OgnOnPickedDatabase::sm_generatorVersionOgnOnPicked{std::make_tuple(1,79,2)};
std::tuple<int, int, int> OgnOnPickedDatabase::sm_targetVersionOgnOnPicked{std::make_tuple(2,184,5)};
OgnOnPickedDatabase::TokenManager OgnOnPickedDatabase::tokens;
}
using namespace IOgnOnPicked;
#define REGISTER_OGN_NODE() \
namespace { \
    ogn::NodeTypeBootstrapImpl<OgnOnPicked, OgnOnPickedDatabase> s_registration("omni.graph.ui_nodes.OnPicked", 3, "omni.graph.ui_nodes"); \
}
