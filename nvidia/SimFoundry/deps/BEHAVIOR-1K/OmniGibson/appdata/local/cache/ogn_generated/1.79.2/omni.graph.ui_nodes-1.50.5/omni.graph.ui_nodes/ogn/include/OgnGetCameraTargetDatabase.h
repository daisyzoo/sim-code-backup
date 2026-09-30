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

namespace OgnGetCameraTargetAttributes
{
namespace inputs
{
using prim_t = const ogn::const_array<TargetPath>&;
ogn::AttributeInitializer<const TargetPath*, ogn::kOgnInput> prim("inputs:prim", "target", kExtendedAttributeType_Regular, nullptr, 0);
using primPath_t = const NameToken&;
ogn::AttributeInitializer<const NameToken, ogn::kOgnInput> primPath("inputs:primPath", "token", kExtendedAttributeType_Regular);
using usePath_t = const bool&;
ogn::AttributeInitializer<const bool, ogn::kOgnInput> usePath("inputs:usePath", "bool", kExtendedAttributeType_Regular, true);
}
namespace outputs
{
using target_t = pxr::GfVec3d&;
ogn::AttributeInitializer<pxr::GfVec3d, ogn::kOgnOutput> target("outputs:target", "point3d", kExtendedAttributeType_Regular);
}
namespace state
{
}
}
using namespace OgnGetCameraTargetAttributes;
namespace IOgnGetCameraTarget
{
// Gets a viewport camera's target point.
class OgnGetCameraTargetDatabase : public omni::graph::core::ogn::OmniGraphDatabase
{
public:
    template <typename StateInformation>
    CARB_DEPRECATED("sInternalState is deprecated. Use sSharedState or sPerInstanceState instead")
    static StateInformation& sInternalState(const NodeObj& nodeObj, InstanceIndex index = {kAuthoringGraphIndex}) {
        return sm_stateManagerOgnGetCameraTarget.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sSharedState(const NodeObj& nodeObj) {
        return sm_stateManagerOgnGetCameraTarget.getState<StateInformation>(nodeObj.nodeHandle, kAuthoringGraphIndex);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, InstanceIndex index) {
        return sm_stateManagerOgnGetCameraTarget.getState<StateInformation>(nodeObj.nodeHandle, index);
    }
    template <typename StateInformation>
    static StateInformation& sPerInstanceState(const NodeObj& nodeObj, GraphInstanceID instanceId) {
        return sm_stateManagerOgnGetCameraTarget.getState<StateInformation>(nodeObj.nodeHandle, instanceId);
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
    static ogn::StateManager sm_stateManagerOgnGetCameraTarget;
    static std::tuple<int, int, int>sm_generatorVersionOgnGetCameraTarget;
    static std::tuple<int, int, int>sm_targetVersionOgnGetCameraTarget;
    static constexpr size_t staticAttributeCount = 6;
    std::vector<ogn::DynamicInput> m_dynamicInputs;
    std::vector<ogn::DynamicOutput> m_dynamicOutputs;
    std::vector<ogn::DynamicState> m_dynamicStates;
    std::vector<NameToken> m_mappedAttributes;
    bool m_canCachePointers{true};

    struct inputsT {
        inputsT(size_t const& offset)
        : prim{offset,AttributeRole::eTarget}
        , primPath{offset}
        , usePath{offset}
        {}
        ogn::ArrayInput<const TargetPath,ogn::kCpu> prim;
        bool has_prim() const { return prim.isValid(); };
        ogn::SimpleInput<const NameToken,ogn::kCpu> primPath;
        ogn::SimpleInput<const bool,ogn::kCpu> usePath;
    } inputs;

    struct outputsT {
        outputsT(size_t const& offset)
        : target{offset,AttributeRole::ePosition}
        {}
        ogn::SimpleOutput<pxr::GfVec3d,ogn::kCpu> target;
    } outputs;

    //Only use this constructor for temporary stack-allocated object:
    OgnGetCameraTargetDatabase(NodeObj const& nodeObjParam)
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
    OgnGetCameraTargetDatabase(GraphContextObj const&, NodeObj const& nodeObjParam)
    : OgnGetCameraTargetDatabase(nodeObjParam)
    {}

    //Main constructor
    OgnGetCameraTargetDatabase(GraphContextObj const* contextObjParam, NodeObj const* nodeObjParam, size_t handleCount)
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
                ConstAttributeDataHandle, ConstAttributeDataHandle, ConstAttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    inputs::prim.m_token, inputs::primPath.m_token, inputs::usePath.m_token
                )
            , kAccordingToContextIndex);
            auto outputDataHandles0 = getAttributesW<
                AttributeDataHandle
                >(contextObj, nodeObj.nodeContextHandle, std::make_tuple(
                    outputs::target.m_token
                )
            , kAccordingToContextIndex);
            inputs.prim.setContext(contextObj);
            inputs.prim.setHandle(std::get<0>(inputDataHandles0));
            inputs.primPath.setContext(contextObj);
            inputs.primPath.setHandle(std::get<1>(inputDataHandles0));
            inputs.usePath.setContext(contextObj);
            inputs.usePath.setHandle(std::get<2>(inputDataHandles0));
            outputs.target.setContext(contextObj);
            outputs.target.setHandle(std::get<0>(outputDataHandles0));
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
            CARB_LOG_ERROR("IToken not found when initializing omni.graph.ui_nodes.GetCameraTarget");
            return;
        }
        auto& iToken{ *iTokenPtr };

        inputs::prim.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::primPath.initialize(iToken, *iNodeType, nodeTypeObj);
        inputs::usePath.initialize(iToken, *iNodeType, nodeTypeObj);

        outputs::target.initialize(iToken, *iNodeType, nodeTypeObj);

        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataExtension, "omni.graph.ui_nodes");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataUiName, "Get Camera Target");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataCategories, "sceneGraph:camera");
        iNodeType->setMetadata(nodeTypeObj, kOgnMetadataDescription, "Gets a viewport camera's target point.");
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
        const IInternal* iInternal = carb::getCachedInterface<omni::graph::core::IInternal>();
        if( ! iInternal ) {
            CARB_LOG_ERROR("IInternal not found when initializing omni.graph.ui_nodes.GetCameraTarget");
            return;
        }
        AttributeObj attr;
        attr = iNode->getAttributeByToken(nodeObj, inputs::prim.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The camera prim, when 'usePath' is false");
        attr.iAttribute->setIsOptionalForCompute(attr, true);
        attr = iNode->getAttributeByToken(nodeObj, inputs::primPath.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "Path of the camera, used when 'usePath' is true");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Camera Path");
        iInternal->deprecateAttribute(attr, "Use prim input with a ToTarget node instead");
        attr = iNode->getAttributeByToken(nodeObj, inputs::usePath.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "When true, the 'primPath' attribute is used as the path to the prim being read, otherwise it will read the connection at the 'prim' attribute");
        attr.iAttribute->setMetadata(attr, kOgnMetadataDefault, "true");
        iInternal->deprecateAttribute(attr, "Use prim input with a ToTarget node instead");
        attr = iNode->getAttributeByToken(nodeObj, outputs::target.token());
        attr.iAttribute->setMetadata(attr, kOgnMetadataDescription, "The target point");
        attr.iAttribute->setMetadata(attr, kOgnMetadataUiName, "Target");
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
        sm_stateManagerOgnGetCameraTarget.removeState(nodeObj.nodeHandle, instanceID);
    }
    bool validate() const {
        return validateNode()
            && inputs.primPath.isValid()
            && inputs.usePath.isValid()
            && outputs.target.isValid()
        ;
    }
    void preCompute() {
        if(m_canCachePointers == false) {
            inputs.prim.invalidateCachedPointer();
            inputs.primPath.invalidateCachedPointer();
            inputs.usePath.invalidateCachedPointer();
            outputs.target.invalidateCachedPointer();
            return;
        }
        inputs.prim.invalidateCachedPointer();
        for(NameToken const& attrib : m_mappedAttributes) {
            if(attrib == inputs::prim.m_token) {
                inputs.prim.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::primPath.m_token) {
                inputs.primPath.invalidateCachedPointer();
                continue;
            }
            if(attrib == inputs::usePath.m_token) {
                inputs.usePath.invalidateCachedPointer();
                continue;
            }
            if(attrib == outputs::target.m_token) {
                outputs.target.invalidateCachedPointer();
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
        if( !inputs.primPath.canVectorize()
            || !inputs.usePath.canVectorize()
            || !outputs.target.canVectorize()
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
        if(token == inputs::prim.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.prim.setHandle(hdl);
            return;
        }
        if(token == inputs::primPath.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.primPath.setHandle(hdl);
            return;
        }
        if(token == inputs::usePath.m_token) {
            ConstAttributeDataHandle hdl = attr.iAttribute->getConstAttributeDataHandle(attr, m_offset);
            inputs.usePath.setHandle(hdl);
            return;
        }
        if(token == outputs::target.m_token) {
            AttributeDataHandle hdl = attr.iAttribute->getAttributeDataHandle(attr, m_offset);
            outputs.target.setHandle(hdl);
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
ogn::StateManager OgnGetCameraTargetDatabase::sm_stateManagerOgnGetCameraTarget;
std::tuple<int, int, int> OgnGetCameraTargetDatabase::sm_generatorVersionOgnGetCameraTarget{std::make_tuple(1,79,2)};
std::tuple<int, int, int> OgnGetCameraTargetDatabase::sm_targetVersionOgnGetCameraTarget{std::make_tuple(2,184,5)};
}
using namespace IOgnGetCameraTarget;
#define REGISTER_OGN_NODE() \
namespace { \
    ogn::NodeTypeBootstrapImpl<OgnGetCameraTarget, OgnGetCameraTargetDatabase> s_registration("omni.graph.ui_nodes.GetCameraTarget", 2, "omni.graph.ui_nodes"); \
}
