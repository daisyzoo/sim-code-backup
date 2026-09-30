import unittest
from simfoundry.data.front_top_route import FrontTopRouteState, select_front_route
from simfoundry.data.frontal_bypass import FrontalBypassState, frontal_bypass_plan

Q=(0.,0.,0.,1.)
class FrontRouteTests(unittest.TestCase):
    def state(self):
        plan=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),0.,0.,-1)
        return FrontTopRouteState(FrontalBypassState(plan),'right',(.14,.09,.045),
                                 guarded_descent=True,continuous_drag=True)
    def call(self,s,target=(.4,.12,.7725),tip=(.35,.12,.795),other=(.55,-.12,.77),gap=.1,load=5.):
        return s.update(tip,target,other,.07,.075,tip=tip,quat=Q,obstacle_quat=Q,
                        control_offset_local=(.2,0,0),load_n=load,hand_obstacle_gap_m=gap)
    def pushing(self,s):
        self.call(s)
        s.top_mode='top_push';s.command=(.35,.12,.795)
    def test_front_selected_only_if_shorter_and_table_safe(self):
        chosen,_=select_front_route((.4,.12,.7725),(.55,-.12,.77),(.14,.09,.045),(.15,.145,.04),Q,Q,-1)
        self.assertEqual(chosen['route'],'front')
        chosen,_=select_front_route((.46,-.15,.77),(.43,.15,.7725),(.15,.145,.04),(.14,.09,.045),Q,Q,1)
        self.assertIsNone(chosen)
    def test_starts_above_without_rear_push(self):
        r=self.call(self.state(),tip=(.1,.2,.6))
        self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['target_xyz'],(.1,.2,.91))
    def test_no_lateral_advance_before_measured_front_clearance(self):
        s=self.state();self.pushing(s)
        r=self.call(s)
        self.assertEqual(r['route_stage'],'front_x')
        self.assertLess(r['target_xyz'][0],.35)
        self.assertEqual(r['target_xyz'][1],.12)
    def test_lateral_only_after_actual_displacement(self):
        s=self.state();self.pushing(s)
        r=self.call(s,target=(.382,.12,.7725),tip=(.332,.12,.795))
        self.assertEqual(r['route_stage'],'lateral_y')
        self.assertLess(r['target_xyz'][1],.12)
        self.assertLessEqual(abs(r['target_xyz'][0]-.35),.00300001)
    def test_target_or_hand_interference_latches_lift(self):
        for kw,reason in [({'gap':.004},'hand_obstacle_gap_5mm'),
                          ({'other':(.55,-.108,.77)},'non_target_motion_10mm'),
                          ({'target':(.352,.12,.7725)},'target_table_margin_5mm')]:
            s=self.state();self.pushing(s);r=self.call(s,**kw)
            self.assertEqual(r['route_stop_reason'],reason)
            self.assertEqual(r['mode'],'front_guard_lift')
            r=self.call(s);self.assertEqual(r['route_stop_reason'],reason)
            self.assertGreaterEqual(r['target_xyz'][2],.91)
    def test_loss_of_load_recontacts_not_unloaded_drag(self):
        s=self.state();self.pushing(s)
        for _ in range(3):r=self.call(s,load=0.)
        self.assertEqual(r['mode'],'top_lift')
        self.assertEqual(r['last_recontact_reason'],'lost_contact')
    def test_goal_uses_actual_target_and_original_release(self):
        s=self.state();self.pushing(s)
        r=self.call(s,target=(.382,-.21,.7725),tip=(.332,-.21,.795))
        self.assertEqual(r['mode'],'top_release')

if __name__=='__main__':unittest.main()
