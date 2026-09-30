"""Opt-in query-state-relative arm10 labels; physical waist action stays absolute."""
from dataclasses import dataclass
import torch
from lerobot.processor import ProcessorStep, ProcessorStepRegistry, NormalizerProcessorStep
from lerobot.processor.core import TransitionKey


def joint_action_transform(action, state, inverse=False):
    if action.ndim != 3 or state.ndim != 2 or action.shape[0] != state.shape[0] or action.shape[-1] != 11 or state.shape[-1] != 11:
        raise ValueError("Expected action[B,T,11] and query state[B,11]")
    if not torch.isfinite(action).all() or not torch.isfinite(state).all():
        raise ValueError("Nonfinite action/state")
    result=action.clone()
    anchor=state[:,None,:10].to(device=action.device,dtype=action.dtype)
    result[:,:,:10]=action[:,:,:10]+anchor if inverse else action[:,:,:10]-anchor
    return result


@ProcessorStepRegistry.register(name="pi05_query_relative_arm10")
@dataclass
class QueryRelativeArm10(ProcessorStep):
    def __call__(self, transition):
        action=transition.get(TransitionKey.ACTION)
        if action is None: return transition
        state=transition.get(TransitionKey.OBSERVATION,{}).get("observation.state")
        if state is None: raise ValueError("Raw query state required for relative action labels")
        result=transition.copy()
        result[TransitionKey.ACTION]=joint_action_transform(action,state)
        return result

    def transform_features(self, features): return features


def validate_relative_pipeline(config, preprocessor):
    steps=list(preprocessor.steps)
    found=[i for i,s in enumerate(steps) if isinstance(s,QueryRelativeArm10)]
    if config.joint_action_representation=="absolute":
        if found: raise ValueError("Absolute policy cannot have relative labels")
        return
    if config.joint_action_representation!="state_relative_arm10": raise ValueError("Unknown representation")
    for key,features in [("observation.state",config.input_features),("action",config.output_features)]:
        if key not in features or tuple(features[key].shape)!=(11,): raise ValueError("Relative arm10 requires 11D features")
    normalizers=[i for i,s in enumerate(steps) if isinstance(s,NormalizerProcessorStep)]
    if len(found)!=1 or len(normalizers)!=1 or found[0]+1!=normalizers[0]:
        raise ValueError("Relative encoding must occur exactly once immediately before normalization")


def install_relative_training_step(config, preprocessor):
    if config.joint_action_representation=="state_relative_arm10" and not any(isinstance(s,QueryRelativeArm10) for s in preprocessor.steps):
        steps=list(preprocessor.steps);indices=[i for i,s in enumerate(steps) if isinstance(s,NormalizerProcessorStep)]
        if len(indices)!=1: raise ValueError("Expected exactly one normalizer")
        steps.insert(indices[0],QueryRelativeArm10());preprocessor.steps=steps
    validate_relative_pipeline(config,preprocessor)
