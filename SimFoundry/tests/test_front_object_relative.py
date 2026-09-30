import unittest
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState, frontal_bypass_plan

Q=(0.,0.,0.,1.)
class FrontObjectRelativeTests(unittest.TestCase):
    def state(self):
        plan=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),0.,0.,-1)
        return FrontTopRouteState(FrontalBypassState(plan),'right',(.14,.09,.045),
            guarded_descent=True,continuous_drag=True,route_clearance_m=.012,
            recover_clearance=True,confirm_nominal_clearance=True,object_relative_lead=True)
    def call(self,s,target=(.382,.12,.7725),tip=(.38,.122,.795),load=5.,gap=.1):
        return s.update(tip,target,(.55,-.12,.77),.07,.075,tip=tip,quat=Q,obstacle_quat=Q,
            control_offset_local=(.2,0,0),load_n=load,hand_obstacle_gap_m=gap)
    def pushing(self):
        s=self.state();self.call(s,target=(.4,.12,.7725));s.top_mode='top_push';s.command=(.38,.122,.795)
        return s
    def test_slipping_tip_does_not_move_latched_anchor(self):
        s=self.pushing();first=self.call(s);anchor=s.relative_contact_anchor
        for _ in range(100): last=self.call(s,tip=(.33,.03,.795))
        self.assertEqual(s.relative_contact_anchor,anchor)
        self.assertEqual(last['target_xyz'][:2],last['object_relative_desired_xy_m'])
        self.assertAlmostEqual(last['target_xyz'][1],.12+anchor[1]-.012)
    def test_loss_of_contact_clears_anchor_and_new_contact_relatches(self):
        s=self.pushing();self.call(s)
        for _ in range(3): r=self.call(s,load=0.)
        self.assertEqual(r['mode'],'top_lift');self.assertIsNone(s.relative_contact_anchor)
        s.top_mode='top_push';s.command=(.378,.119,.795)
        self.call(s,tip=(.378,.119,.795))
        self.assertAlmostEqual(s.relative_contact_anchor[1],-.001)
    def test_emergency_guard_still_latches_and_lifts(self):
        s=self.pushing();self.call(s)
        r=self.call(s,gap=.004)
        self.assertEqual(r['mode'],'front_guard_lift')
        self.assertEqual(r['route_stop_reason'],'hand_obstacle_gap_5mm')
        self.assertEqual(self.call(s)['mode'],'front_guard_lift')
    def test_release_requires_measured_target(self):
        s=self.pushing();self.call(s)
        r=self.call(s,target=(.382,-.21,.7725),tip=(.38,-.2,.795))
        self.assertEqual(r['mode'],'top_release')
        self.assertIsNone(s.relative_contact_anchor)

if __name__=='__main__':unittest.main()
