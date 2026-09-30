import unittest
from simfoundry.data.front_clearance_progress import FrontClearanceProgress

class FrontClearanceProgressTests(unittest.TestCase):
    def test_resume_needs_tracking_reserve(self):
        s=FrontClearanceProgress(.012,.12)
        self.assertEqual(s.update(.0121,.12)['route_stage'],'front_x')
        self.assertEqual(s.update(.0126,.12)['route_stage'],'lateral_y')
    def test_restore_before_10mm_stop_and_hold_current_y(self):
        s=FrontClearanceProgress(.012,.12);s.update(.015,.12)
        r=s.update(.0119,-.049)
        self.assertTrue(r['clearance_recovery_entered']);self.assertEqual(r['front_hold_y'],-.049)
        self.assertGreater(r['recover_clearance_m'],.01)
        self.assertEqual(s.update(.0123,-.052)['front_hold_y'],-.049)
        self.assertEqual(s.update(.0126,-.05)['route_stage'],'lateral_y')
        self.assertEqual(s.recoveries,1)
    def test_repeated_recovery_never_returns_to_initial_y(self):
        s=FrontClearanceProgress(.012,.12)
        for i,y in enumerate((.08,.02,-.06)):
            s.update(.015,y);r=s.update(.0115,y)
            self.assertEqual(r['front_hold_y'],y);self.assertEqual(r['clearance_recovery_count'],i+1)
    def test_reject_invalid_geometry(self):
        with self.assertRaises(ValueError):FrontClearanceProgress(.005,0).update(.02,0)
        with self.assertRaises(ValueError):FrontClearanceProgress(.012,0).update(float('nan'),0)

if __name__=='__main__':unittest.main()
