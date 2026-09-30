import unittest,math
from simfoundry.data.top_contact_visibility import visible_waist_preference

class VisibilityPreferenceTests(unittest.TestCase):
    def preference(self,center=(.63,-.15,.7725),current=.9):
        return visible_waist_preference(center,(0,0,0,1),(.14,.09,.045),(420.,420.,320.,240.),640,480,current,.98)
    def test_returns_visible_candidate_within_working_range(self):
        r=self.preference();self.assertTrue(r['has_visible_candidate']);self.assertGreaterEqual(r['candidate_bbox_fraction'],.5);self.assertLess(abs(r['preferred_waist_rad']),.98)
        fixed=self.preference(current=r['preferred_waist_rad']);self.assertAlmostEqual(fixed['preferred_waist_rad'],r['preferred_waist_rad'])
    def test_unobservable_height_does_not_invent_pose_target(self):
        r=self.preference(center=(.63,-.15,100.));self.assertFalse(r['has_visible_candidate']);self.assertEqual(r['preferred_waist_rad'],.9)
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):self.preference(current=math.nan)
