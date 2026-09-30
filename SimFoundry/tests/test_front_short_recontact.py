import unittest
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState,frontal_bypass_plan
Q=(0.,0.,0.,1.)
class FrontShortRecontactTests(unittest.TestCase):
    def state(self,z=.86):
        plan=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),0.,0.,-1)
        return FrontTopRouteState(FrontalBypassState(plan),'right',(.14,.09,.045),guarded_descent=True,continuous_drag=True,recontact_travel_z=z)
    def call(self,s,load=5.,gap=.1,tip=(.35,.12,.795)):
        return s.update(tip,(.4,.12,.7725),(.55,-.12,.77),.07,.075,tip=tip,quat=Q,obstacle_quat=Q,control_offset_local=(.2,0,0),load_n=load,hand_obstacle_gap_m=gap)
    def test_initial_approach_is_unchanged(self):
        self.assertEqual(self.call(self.state())['target_xyz'][2],.91)
    def test_recovery_height_only_after_three_lost_load_frames(self):
        s=self.state();self.call(s);s.top_mode='top_push';s.command=(.35,.12,.795)
        for _ in range(2): self.assertEqual(self.call(s,load=0.)['mode'],'top_push')
        r=self.call(s,load=0.);self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['target_xyz'][2],.86)
        self.assertEqual(r['recontacts'],1)
    def test_default_recovery_remains_point91(self):
        s=self.state(.91);self.call(s);s.top_mode='top_push';s.command=(.35,.12,.795)
        for _ in range(3):r=self.call(s,load=0.)
        self.assertEqual(r['target_xyz'][2],.91)
    def test_emergency_lift_remains_point91(self):
        s=self.state();self.call(s);s.recontacts=1
        r=self.call(s,gap=.004);self.assertEqual(r['mode'],'front_guard_lift');self.assertGreaterEqual(r['target_xyz'][2],.91)
    def test_no_downward_lift_if_already_above_recovery_height(self):
        s=self.state();self.call(s);s._start_recontact((.35,.12,.88),'lost_contact')
        r=self.call(s,tip=(.35,.12,.80));self.assertGreaterEqual(r['target_xyz'][2],.88)
    def test_invalid_and_unguarded_short_recovery_rejected(self):
        for z in (.83,.92,float('nan')):
            with self.assertRaises(ValueError):self.call(self.state(z))
        s=self.state();s.guarded_descent=False
        with self.assertRaises(ValueError):self.call(s)
if __name__=='__main__':unittest.main()
