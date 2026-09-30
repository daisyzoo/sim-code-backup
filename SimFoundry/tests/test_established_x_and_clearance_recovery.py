import unittest
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState,frontal_bypass_plan
from simfoundry.data.top_contact_bypass import TopContactBypassState
Q=(0,0,0,1)

class EstablishedXTests(unittest.TestCase):
    def state(self,hold):
        p=frontal_bypass_plan((.55,-.12,.77),(.4,.12,.7725),(.15,.145),(.14,.09),0,0,1)
        s=TopContactBypassState(FrontalBypassState(p),'left',(.15,.145,.04),continuous_drag=True,front_inset_fraction=1,hold_established_x=hold)
        s.top_mode='top_push';s.command=(.58,0,.79);return s
    def update(self,s,x):
        return s.update((.58,0,.84),(x,0,.77),(.4,.12,.7725),.075,.07,tip=(.58,0,.79),quat=Q,control_offset_local=(.2,0,0),load_n=3.)
    def test_hold_does_not_follow_object_x_and_survives_recontact(self):
        s=self.state(True);self.update(s,.58);r=self.update(s,.60)
        self.assertEqual(s.push_x_anchor,.58);self.assertEqual(r['target_xyz'][0],.58)
        s._start_recontact((.59,0,.8),'lost_contact');self.assertEqual(s.push_x_anchor,.58)
        s.top_mode='top_push';s.command=(.595,0,.79);r=self.update(s,.60)
        self.assertAlmostEqual(r['target_xyz'][0],.593);self.assertEqual(s.push_x_anchor,.58)
    def test_default_still_tracks_surface_x(self):
        s=self.state(False);self.update(s,.58);r=self.update(s,.60)
        self.assertAlmostEqual(r['target_xyz'][0],.582)
        s._start_recontact((.59,0,.8),'lost_contact');self.assertIsNone(s.push_x_anchor)
    def test_integrated_front_correction_holds_current_y_not_initial_y(self):
        p=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),0,0,-1)
        s=FrontTopRouteState(FrontalBypassState(p),'right',(.14,.09,.045),continuous_drag=True,recover_clearance=True,route_clearance_m=.012)
        def call(target,tip=(.33,-.06,.795)):
            return s.update(tip,target,(.55,-.12,.77),.07,.075,tip=tip,quat=Q,obstacle_quat=Q,control_offset_local=(.2,0,0),load_n=3.,hand_obstacle_gap_m=.1)
        call((.4,.12,.7725));r=call((.391,.12,.7725));self.assertEqual(r['route_stage'],'lateral_y')
        s.top_mode='top_push';s.command=(.33,-.06,.795)
        r=call((.3935,-.04,.7725));self.assertEqual(r['route_stage'],'front_x')
        self.assertEqual(r['clearance_progress']['front_hold_y'],-.04)
        self.assertAlmostEqual(r['target_xyz'][1],-.06)
        self.assertEqual(call((.396,-.04,.7725))['route_stop_reason'],'parcel_clearance_10mm')

class ConfirmedFrontIntegrationTests(unittest.TestCase):
    def test_nominal_confirmation_and_emergency_guard_integration(self):
        p=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),0,0,-1)
        s=FrontTopRouteState(FrontalBypassState(p),'right',(.14,.09,.045),continuous_drag=True,recover_clearance=True,confirm_nominal_clearance=True,route_clearance_m=.012)
        def call(x,y=.12):
            tip=(.33,y,.795)
            return s.update(tip,(x,y,.7725),(.55,-.12,.77),.07,.075,tip=tip,quat=Q,obstacle_quat=Q,control_offset_local=(.2,0,0),load_n=3.,hand_obstacle_gap_m=.1)
        call(.4)
        self.assertEqual(call(.39251)['route_stage'],'front_x')
        self.assertEqual(call(.39251)['route_stage'],'front_x')
        r=call(.39251);self.assertEqual(r['route_stage'],'lateral_y')
        self.assertEqual(r['clearance_progress']['clearance_resume_reason'],'nominal_clearance_confirmed_3')
        self.assertEqual(call(.396,-.04)['route_stop_reason'],'parcel_clearance_10mm')

if __name__=='__main__':unittest.main()
