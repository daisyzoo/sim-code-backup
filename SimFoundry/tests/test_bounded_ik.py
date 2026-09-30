import unittest
import numpy as np
from simfoundry.data.bounded_ik import bounded_damped_step

class BoundedIKTests(unittest.TestCase):
    def test_saturated_waist_redistributes_to_arm(self):
        # Both coordinates contribute equally, but waist already at upper bound.
        dq=bounded_damped_step([[1,1]],[.03],[.18,0],[-.18,-1],[.18,1],[.015,.04],[.01,.01])
        self.assertLessEqual(dq[0],1e-9)
        self.assertGreater(dq[1],.029)
        self.assertLess(abs(dq.sum()-.03),1e-5)

    def test_infeasible_target_stays_within_joint_and_step_limits(self):
        dq=bounded_damped_step(np.eye(2),[10,-10],[.179,0],[-.18,-1],[.18,1],[.015,.04],[.12,.045])
        self.assertLessEqual(dq[0],.001+1e-9)
        self.assertGreaterEqual(dq[1],-.04-1e-9)

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            bounded_damped_step([[1]],[np.nan],[0],[-1],[1],[.04],[.1])

    def test_preference_uses_redundancy_and_preserves_bounds(self):
        dq=bounded_damped_step([[1.,1.]],[0.],[.6,0.],[-1.,-1.],[1.,1.],[.015,.04],[.12,.045],preferred_step=[-.015,0.])
        self.assertLess(dq[0],-.01);self.assertGreater(dq[1],.01);self.assertLess(abs(dq.sum()),1e-4)
        self.assertLessEqual(abs(dq[0]),.015);self.assertLessEqual(abs(dq[1]),.04)
    def test_default_preference_unchanged_and_invalid_shape_rejected(self):
        args=([[1.,1.]],[.02],[0.,0.],[-1.,-1.],[1.,1.],[.015,.04],[.12,.045])
        np.testing.assert_array_equal(bounded_damped_step(*args),bounded_damped_step(*args,preferred_step=[0.,0.]))
        with self.assertRaises(ValueError):bounded_damped_step(*args,preferred_step=[0.])
