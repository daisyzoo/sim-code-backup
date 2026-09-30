import unittest
from copy import deepcopy
from types import SimpleNamespace
from simfoundry.data.waist_pilot_audit import audit_waist_pilot_episode


class WaistPilotRejectionTests(unittest.TestCase):
    def test_diagnostic_or_assisted_rejected_before_contract_or_data_read(self):
        base=dict(collection_role='pilot',motion_protocol='waist_yaw_enabled_v1',assist_frames=0,push_assist=False,idle_diagnostic=False,wait_force_n=0.,push_force_n=0.,collision_pipeline='newton')
        for key,value in [('collection_role','diagnostic'),('assist_frames',1),('push_assist',True),('idle_diagnostic',True),('motion_protocol','waist_locked_v1'),('push_force_n',2.),('wait_force_n',2.),('collision_pipeline','unknown')]:
            meta=deepcopy(base);meta[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'cannot train'):
                audit_waist_pilot_episode('/nonexistent/raw.npz',SimpleNamespace(collect_meta=meta),{})
