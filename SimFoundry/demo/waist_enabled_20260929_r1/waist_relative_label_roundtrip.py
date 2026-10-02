"""Validate arm10 query-relative encoding and unchanged absolute waist labels."""
import torch
from lerobot.policies.pi05.joint_relative import QueryRelativeArm10,joint_action_transform
from lerobot.processor import NormalizerProcessorStep,UnnormalizerProcessorStep
from lerobot.processor.core import TransitionKey

def verify_restored(actions,states,restored):
 if actions.ndim!=3 or actions.shape[-1]!=11 or states.shape!=(len(actions),11) or restored.shape!=actions.shape:
  raise ValueError('Expected batched physical11D action chunks and query states')
 if not all(torch.isfinite(x).all() for x in [actions,states,restored]):raise ValueError('Nonfinite label roundtrip')
 error=float((restored-actions).abs().max())
 waist_error=float((restored[...,-1]-actions[...,-1]).abs().max())
 if error>=1e-6 or waist_error>=1e-6:raise ValueError('Physical labels changed during relative roundtrip')
 return dict(max_float32_encode_normalize_decode_restore_error=error,waist_absolute_roundtrip_max_error=waist_error,recorded_waist_max_abs_rad=float(actions[...,-1].abs().max()),waist_nonzero_label_count=int((actions[...,-1].abs()>1e-4).sum()))

def roundtrip(actions,states,stats,features,norm_map):
 original_states=states.clone();original_actions=actions.clone()
 transition={TransitionKey.OBSERVATION:{'observation.state':states},TransitionKey.ACTION:actions}
 encoded=QueryRelativeArm10()(transition)
 if not torch.equal(encoded[TransitionKey.ACTION][...,-1],original_actions[...,-1]):raise ValueError('Absolute waist changed during encoding')
 if not torch.equal(states,original_states):raise ValueError('Query state mutated during encoding')
 norm=NormalizerProcessorStep(features=features,norm_map=norm_map,stats=stats)
 unnorm=UnnormalizerProcessorStep(features={k:v for k,v in features.items() if k=='action'},norm_map=norm_map,stats=stats)
 normalized=norm(encoded);decoded=unnorm(normalized)[TransitionKey.ACTION]
 restored=joint_action_transform(decoded,original_states,inverse=True)
 result=verify_restored(original_actions,original_states,restored)
 if not torch.equal(states,original_states):raise ValueError('Query state mutated during normalization')
 return result
