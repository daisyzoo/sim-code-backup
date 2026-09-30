import math,unittest
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState,frontal_bypass_plan
from simfoundry.data.top_contact_bypass import TopContactBypassState
from simfoundry.data.tabletop_route_candidates import footprint_radii


def quat(yaw):return (0,0,math.sin(yaw/2),math.cos(yaw/2))

class ProjectedRouteParameterTests(unittest.TestCase):
    def test_recorded_8p7mm_residual_enters_press_only_with_explicit_10mm(self):
        plan=frontal_bypass_plan((.55,-.12,.77),(.4,.12,.7725),(.15,.145),(.14,.09),0,0,1)
        for tol,expected in ((.008,'top_descend'),(.010,'top_press')):
            s=TopContactBypassState(FrontalBypassState(plan),'left',(.15,.145,.04),guarded_descent=True,continuous_drag=True,front_inset_fraction=1.,alignment_tolerance_m=tol)
            s.top_mode='top_descend';s.descent_z=.802
            for _ in range(20):
                row=s.update((.6,0,.84),(.6,0,.77),(.4,.12,.7725),.075,.07,tip=(.5913,.0039,.7943),quat=quat(0),control_offset_local=(.2,0,0),load_n=0.)
            self.assertEqual(row['mode'],expected)
            self.assertNotEqual(row['mode'],'top_push') # Force confirmation remains mandatory.
    def front(self,margin):
        plan=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),.13,-.11,-1)
        s=FrontTopRouteState(FrontalBypassState(plan),'right',(.14,.09,.045),guarded_descent=True,continuous_drag=True,route_clearance_m=margin)
        self.call(s,(.4,.12,.7725),.13)
        return s
    def call(self,s,target,yaw,gap=.18):
        tr=footprint_radii(s.size,quat(yaw))[0];other=footprint_radii(s.obstacle_size,quat(-.11))[0]
        return s.update((.4,.12,.85),target,(.55,-.12,.77),tr,other,tip=(.343,.109,.795),quat=quat(yaw),obstacle_quat=quat(-.11),control_offset_local=(.2,0,0),load_n=0.,hand_obstacle_gap_m=gap)
    def test_static_rotated_front_corridor_12mm_retains_table_and_hand_guards(self):
        old=self.call(self.front(.02),(.383,.1195,.7723),math.radians(16.434))
        self.assertEqual(old['route_stop_reason'],'front_corridor_no_table_margin')
        s=self.front(.012);row=self.call(s,(.383,.1195,.7723),math.radians(16.434))
        self.assertIsNone(row['route_stop_reason']);self.assertEqual(row['route_stage'],'front_x')
        row=self.call(s,(.383,.1195,.7723),math.radians(16.434),gap=.004)
        self.assertEqual(row['route_stop_reason'],'hand_obstacle_gap_5mm')
    def test_front_margin_below_emergency_buffer_rejected(self):
        with self.assertRaises(ValueError):self.front(.005)

if __name__=='__main__':unittest.main()
