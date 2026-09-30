"""Tests of query anchoring, serialization and opt-in/legacy isolation."""
import copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import torch
from lerobot.configs.policies import PreTrainedConfig
from lerobot.configs.types import PolicyFeature,FeatureType,NormalizationMode
from lerobot.policies.pi05.configuration_pi05 import PI05Config
from lerobot.policies.pi05.joint_relative import joint_action_transform,QueryRelativeArm10,install_relative_training_step,validate_relative_pipeline
from lerobot.processor import PolicyProcessorPipeline,NormalizerProcessorStep,UnnormalizerProcessorStep
from lerobot.processor.core import TransitionKey
from lerobot.processor.converters import batch_to_transition,transition_to_batch

class RelativeTests(unittest.TestCase):
    def setUp(self):
        self.features={'observation.state':PolicyFeature(FeatureType.STATE,(11,)),'action':PolicyFeature(FeatureType.ACTION,(11,))}
        self.stats={k:{'min':torch.full((11,),-2.),'max':torch.full((11,),2.)} for k in self.features}
        self.normmap={'STATE':NormalizationMode.MIN_MAX,'ACTION':NormalizationMode.MIN_MAX}
        self.config=PI05Config(joint_action_representation='state_relative_arm10',input_features={'observation.state':self.features['observation.state']},output_features={'action':self.features['action']})
    def pipeline(self):
        return PolicyProcessorPipeline(steps=[NormalizerProcessorStep(features=self.features,norm_map=self.normmap,stats=self.stats)],to_transition=batch_to_transition,to_output=transition_to_batch)
    def test_same_query_anchor_and_waist(self):
        q=torch.arange(22,dtype=torch.float32).reshape(2,11)/10
        a=torch.zeros((2,10,11));a[:,:,0]=torch.arange(10,dtype=torch.float32)/10
        r=joint_action_transform(a,q)
        self.assertTrue(torch.equal(r[:,:,10],a[:,:,10]))
        self.assertTrue(torch.equal(r[:,:,0],a[:,:,0]-q[:,None,0]))
        self.assertTrue(torch.allclose(joint_action_transform(r,q,inverse=True),a,atol=2e-7))
        self.assertEqual(float(a[0,0,0]),0.)
    def test_bad_shape_and_nonfinite(self):
        for a,q in [(torch.zeros(10,11),torch.zeros(1,11)),(torch.zeros(2,10,11),torch.zeros(1,11)),(torch.zeros(1,10,10),torch.zeros(1,11)),(torch.zeros(1,10,11),torch.full((1,11),float('nan')))]:
            with self.assertRaises(ValueError): joint_action_transform(a,q)
    def test_observation_only_inference_and_no_mutation(self):
        q=torch.randn(2,11);a=torch.randn(2,10,11);source={TransitionKey.OBSERVATION:{'observation.state':q},TransitionKey.ACTION:a}
        before=a.clone();qb=q.clone();r=QueryRelativeArm10()(source)
        self.assertTrue(torch.equal(a,before) and torch.equal(q,qb));self.assertIsNot(r,source)
        obs={TransitionKey.OBSERVATION:{'observation.state':q}}
        self.assertIs(QueryRelativeArm10()(obs),obs)
    def test_legacy_unchanged_and_fail_closed(self):
        p=self.pipeline();legacy=copy.deepcopy(self.config);legacy.joint_action_representation='absolute'
        before=list(p.steps);install_relative_training_step(legacy,p);self.assertEqual(list(p.steps),before)
        with self.assertRaises(ValueError):validate_relative_pipeline(self.config,p)
        install_relative_training_step(self.config,p);install_relative_training_step(self.config,p)
        self.assertEqual(sum(isinstance(x,QueryRelativeArm10) for x in p.steps),1)
        with self.assertRaises(ValueError):validate_relative_pipeline(legacy,p)
        p.steps=list(reversed(p.steps))
        with self.assertRaises(ValueError):validate_relative_pipeline(self.config,p)
    def test_serialized_pipeline_roundtrip(self):
        p=self.pipeline();install_relative_training_step(self.config,p)
        q=torch.randn(2,11);a=torch.randn(2,10,11);batch={'observation.state':q,'action':a};expected=p(batch)
        with tempfile.TemporaryDirectory() as tmp:
            p.save_pretrained(tmp,config_filename='policy_preprocessor.json')
            loaded=PolicyProcessorPipeline.from_pretrained(tmp,config_filename='policy_preprocessor.json',to_transition=batch_to_transition,to_output=transition_to_batch)
            validate_relative_pipeline(self.config,loaded);actual=loaded(batch)
            self.assertTrue(torch.equal(expected['action'],actual['action']))
            self.config.save_pretrained(tmp);restored=PreTrainedConfig.from_pretrained(tmp)
            self.assertEqual(restored.joint_action_representation,'state_relative_arm10')
    def test_unknown_config(self):
        with self.assertRaises(ValueError):PI05Config(joint_action_representation='delta')

class ServerDecodeTests(unittest.TestCase):
    def run_server(self, representation):
        import sys
        import numpy as np
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from pi05_policy_server import Pi05Server
        from lerobot.utils.constants import OBS_LANGUAGE_TOKENS, OBS_LANGUAGE_ATTENTION_MASK
        class Pre:
            def reset(self):pass
            def __call__(self, observation):
                self.state=observation['observation.state'].clone()
                return {OBS_LANGUAGE_TOKENS:torch.zeros(1,2,dtype=torch.long),OBS_LANGUAGE_ATTENTION_MASK:torch.ones(1,2,dtype=torch.bool)}
        class Post:
            def reset(self):pass
            def __call__(self, action):return action*0.2
        model_output=torch.arange(110,dtype=torch.float32).reshape(1,10,11)/100
        model_output[:,:,-1]=0
        class Model:
            def sample_actions(self,*args,**kwargs):return model_output.clone()
        server=Pi05Server.__new__(Pi05Server)
        server.args=SimpleNamespace(num_inference_steps=10)
        server.action_dim=11;server.noise_shape=(1,10,32);server.device=torch.device('cpu')
        server.joint_action_representation=representation
        server.preprocessor=Pre();server.postprocessor=Post()
        server.policy=SimpleNamespace(model=Model(),_preprocess_images=lambda batch:([torch.zeros(1,3,2,2)],[torch.ones(1,dtype=torch.bool)]))
        state=np.linspace(-.7,.7,11,dtype=np.float32);state[-1]=.007
        before=state.copy()
        actual=server.infer(np.zeros((480,640,3),dtype=np.uint8),state,'test')
        expected=(model_output*0.2).squeeze(0).numpy()
        if representation=='state_relative_arm10':expected[:,:10]+=state[None,:10]
        self.assertTrue(np.array_equal(actual,expected))
        self.assertTrue(np.array_equal(state,before))
        self.assertTrue(np.all(actual[:,-1]==0))
        self.assertTrue(np.array_equal(server.preprocessor.state.numpy()[0],state))
    def test_actual_server_relative_decode_after_unnormalization(self):
        self.run_server('state_relative_arm10')
    def test_actual_server_absolute_output_unchanged(self):
        self.run_server('absolute')

if __name__=='__main__':unittest.main()
