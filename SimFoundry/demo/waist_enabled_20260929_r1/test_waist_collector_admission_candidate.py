"""Wiring/negative fixtures only; mocked validator never certifies physics."""
import unittest,tempfile,json,hashlib
from pathlib import Path
from unittest.mock import patch
from waist_collector_admission_candidate import prepare_waist_pilot, finalize_waist_pilot
from simfoundry.data.waist_pilot_protocol import semantic_settings
class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.collector=self.root/'collector.py';self.collector.write_text('# fixture, no simulator\n');self.path=self.root/'contract.json'
  self.contract=dict(pilot_collector_sha256=hashlib.sha256(self.collector.read_bytes()).hexdigest(),layouts=[dict(layout_id=81000,box_xyz=[.4,.1,.77],planned_split='train'),dict(layout_id=81001,box_xyz=[.5,-.1,.77],planned_split='train')],wait_layouts=[dict(layout_id=82000,box_xyz=[.4,.1,.77],planned_split='train')]);self.path.write_text(json.dumps(self.contract));self.digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
  self.settings=dict(waist_pilot_contract=str(self.path),role='pilot',motion_protocol='waist_yaw_enabled_v1',policy_port=0,idle=False,waist_probe=False,layout_start=81000,layouts=2,wait_layout_start=82000,wait_episodes=1,waist_limit_rad=1.,environment_seed=0)
  self.contract['prelaunch_collector_settings']=semantic_settings(self.settings);self.path.write_text(json.dumps(self.contract));self.digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
 def call(self,**changes):
  with patch('waist_collector_admission_candidate.validate_waist_contract',return_value=(self.contract,self.digest)) as validator:
   s=dict(self.settings,**changes);answer=prepare_waist_pilot(s,self.collector);validator.assert_called_once_with(str(self.path));return answer
 def test_schedule_kind_and_deep_copies(self):
  a=self.call();self.assertEqual(set(a.push_layouts),{81000,81001});self.assertEqual(set(a.wait_layouts),{82000})
  d=a.layout(81000);d['box_xyz'][0]=999;self.assertEqual(a.layout(81000)['box_xyz'][0],.4)
  with self.assertRaises(ValueError):a.layout(82000)
  with self.assertRaises(ValueError):a.layout(81000,wait=True)
 def test_default_does_not_admit(self):
  with patch('waist_collector_admission_candidate.validate_waist_contract') as v:self.assertIsNone(prepare_waist_pilot({},self.collector));v.assert_not_called()
 def test_role_protocol_conflicts_and_model_rejected(self):
  for k,v in [('role','diagnostic'),('motion_protocol','waist_locked_v1'),('diagnostic_layout_json','x'),('spatial_pilot_contract','x'),('recovery_pilot_contract','x'),('policy_port',8080),('idle',True),('waist_probe',True)]:
   with self.subTest(k=k),self.assertRaises(ValueError):prepare_waist_pilot(dict(self.settings,**{k:v}),self.collector)
 def test_collector_source_change_rejected(self):
  self.collector.write_text('# modified\n')
  with self.assertRaisesRegex(ValueError,'collector'):self.call()
 def test_unregistered_empty_or_malformed_schedule_rejected(self):
  for change in [dict(layout_start=81002),dict(layouts=3),dict(wait_layout_start=81000),dict(layouts=0,wait_episodes=0),dict(layouts=True),dict(wait_episodes=-1)]:
   with self.subTest(change=change),self.assertRaises(ValueError):self.call(**change)
 def test_contract_change_during_validation_rejected(self):
  self.path.write_text('{}')
  with self.assertRaisesRegex(ValueError,'changed during'):self.call()
 def test_full_validator_failure_propagates(self):
  with patch('waist_collector_admission_candidate.validate_waist_contract',side_effect=ValueError('Physical group failed')):
   with self.assertRaisesRegex(ValueError,'Physical group'):prepare_waist_pilot(self.settings,self.collector)
 def test_prelaunch_semantic_change_rejected(self):
  with self.assertRaisesRegex(ValueError,'prelaunch'):self.call(environment_seed=1)
 def test_resolved_settings_and_contract_identity_rechecked(self):
  admission=self.call();resolved=dict(self.settings,headless=True,physics_gpu=0)
  with patch('waist_collector_admission_candidate.validate_waist_contract',return_value=(self.contract,self.digest)) as v:
   finalize_waist_pilot(admission,resolved,self.collector);v.assert_called_once_with(self.path,settings=resolved)
  with patch('waist_collector_admission_candidate.validate_waist_contract',return_value=(self.contract,'0'*64)):
   with self.assertRaisesRegex(ValueError,'changed during launcher'):finalize_waist_pilot(admission,resolved,self.collector)
if __name__=='__main__':unittest.main()
