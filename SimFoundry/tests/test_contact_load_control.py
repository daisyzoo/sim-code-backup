import unittest
import math
from simfoundry.data.contact_load_control import ContactLoadControl,hand_target_vertical_load

class ContactLoadTests(unittest.TestCase):
    def test_overload_raises_waypoint_smoothly_and_is_bounded(self):
        s=ContactLoadControl(2.);prev=0.
        for _ in range(30):
            r=s.update(20.,True);bias=r['applied_z_bias_m'];self.assertGreaterEqual(bias,prev);self.assertLessEqual(bias-prev,.00300001);prev=bias
        self.assertEqual(s.bias_m,.025)
    def test_no_contact_recovers_without_lowering_below_nominal(self):
        s=ContactLoadControl(2.,bias_m=.01)
        for _ in range(40):s.update(0.,True)
        self.assertEqual(s.bias_m,0.)
        self.assertEqual(s.update(20.,False)['applied_z_bias_m'],0.)
    def test_other_object_contact_does_not_regulate_target_pressure(self):
        r={'parcel_contacts':[{'shapes':['left_wrist_roll','/World/mailer/mesh'],'force_world_N':[1,2,-3]}, {'shapes':['right_wrist_roll','/World/mailer/mesh'],'force_world_N':[0,0,99]}, {'shapes':['left_wrist_roll','/World/parcel_box/mesh'],'force_world_N':[0,0,88]}]}
        self.assertEqual(hand_target_vertical_load(r,'left','mailer'),3.)
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):ContactLoadControl(2.).update(math.nan,True)

    def test_signed_recovery_lowers_boundedly_and_does_not_bias_lift(self):
        c=ContactLoadControl(3.,min_bias_m=-.025)
        prior=0.
        for _ in range(100):
            r=c.update(0.,True)
            self.assertGreaterEqual(r['applied_z_bias_m']-prior,-.00050001)
            prior=r['applied_z_bias_m']
        self.assertAlmostEqual(prior,-.025)
        self.assertEqual(c.update(0.,False)['applied_z_bias_m'],0.)
        for _ in range(20):c.update(10.,True)
        self.assertGreater(c.bias_m,-.025)
        with self.assertRaises(ValueError):ContactLoadControl(3.,min_bias_m=-.04).update(0.,True)
