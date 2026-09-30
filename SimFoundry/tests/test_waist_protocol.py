"""Protocol regression: enabling yaw never bypasses zero/wait/slew gates."""
import unittest
import numpy as np
from simfoundry.data.paired_sorting import audit_rollout

class WaistProtocolTests(unittest.TestCase):
    def fixture(self):
        q = np.zeros((160, 23))
        trace = {k: np.tile(v, (160, 1)) for k, v in {
            'box': [8, 0, .02], 'mailer': [9, 0, .02],
            'palm_left': [.1, .2, .6], 'palm_right': [.1, -.2, .6]}.items()}
        return q, q.copy(), trace

    def test_old_protocol_still_rejects_nonzero_waist(self):
        q,a,t=self.fixture();a[:,12]=np.linspace(0,.1,len(a))
        self.assertIn('waist action is not locked',audit_rollout('wait_no_package',q,a,t)['reasons'])

    def test_enabled_movement_preserves_other_gates(self):
        q,a,t=self.fixture();a[:,12]=q[:,12]=np.linspace(0,.1,len(a))
        r=audit_rollout('push_box_to_bin',q,a,t,motion_protocol='waist_yaw_enabled_v1')
        self.assertFalse(any('waist' in x for x in r['reasons']))
        self.assertFalse(r['passed'])  # No object on table: still not a demonstration.
        q[0,12]=.02;a[20:,12]=.3
        r=audit_rollout('push_box_to_bin',q,a,t,motion_protocol='waist_yaw_enabled_v1')
        self.assertIn('waist working range exceeded',r['reasons'])
        self.assertTrue(any('state is not zero' in x for x in r['reasons']))
        self.assertTrue(any('abrupt' in x for x in r['reasons']))

    def test_wait_must_stay_still(self):
        q,a,t=self.fixture()
        self.assertTrue(audit_rollout('wait_no_package',q,a,t,motion_protocol='waist_yaw_enabled_v1')['passed'])
        q[:,12]=np.linspace(0,.05,len(q))
        self.assertIn('idle waist drift',audit_rollout('wait_no_package',q,a,t,motion_protocol='waist_yaw_enabled_v1')['reasons'])

    def test_unknown_protocol_rejected(self):
        with self.assertRaises(ValueError):
            audit_rollout('wait_no_package',*self.fixture(),motion_protocol='typo')
