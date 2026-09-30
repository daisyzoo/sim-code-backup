"""Training-scope guards: reject accidental backbone unfreeze or frozen expert."""
import os,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
import torch
from lerobot.policies.pi05.configuration_pi05 import PI05Config
from lerobot.utils.pi05_training import audit_parameters
class ScopeTests(unittest.TestCase):
 def config(self,**kw):
  args=dict(train_expert_with_language_lora=True,lora_rank=8,lora_target_language_model=True,lora_target_action_expert=False,train_expert_only=False,mask_action_padding=True);args.update(kw);return PI05Config(**args)
 def test_config_rejects_conflicting_modes(self):
  self.config()
  for kw in [dict(lora_rank=0),dict(lora_target_language_model=False),dict(lora_target_action_expert=True),dict(train_expert_only=True)]:
   with self.assertRaises(ValueError):self.config(**kw)
 def run_audit(self,change=None):
  params={n:torch.nn.Parameter(torch.zeros(1),requires_grad=train) for n,train in [('model.paligemma.language_model.lora_A.weight',True),('model.paligemma.language_model.base.weight',False),('model.vision.weight',False),('model.gemma_expert.weight',True),('model.action_in_proj.weight',True),('model.action_out_proj.weight',True),('model.time_mlp_in.weight',True),('model.time_mlp_out.weight',True)]}
  if change:params[change[0]].requires_grad_(change[1])
  policy=SimpleNamespace(config=self.config(),named_parameters=lambda:params.items())
  optimizer=torch.optim.AdamW([p for p in params.values() if p.requires_grad])
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'PI05_PARAMETER_AUDIT':'1','PI05_REQUIRE_EXPERT_ONLY':'0','PI05_REQUIRE_LANGUAGE_ADAPTER':'1'}):audit_parameters(policy,optimizer,d,True)
 def test_valid_scope(self):self.run_audit()
 def test_backbone_unfreeze_rejected(self):
  with self.assertRaises(ValueError):self.run_audit(('model.vision.weight',True))
 def test_frozen_expert_rejected(self):
  with self.assertRaises(ValueError):self.run_audit(('model.gemma_expert.weight',False))
 def test_missing_adapter_rejected(self):
  with self.assertRaises(ValueError):self.run_audit(('model.paligemma.language_model.lora_A.weight',False))
if __name__=='__main__':unittest.main()
