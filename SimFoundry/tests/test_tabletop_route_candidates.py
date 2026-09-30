import unittest,math
from simfoundry.data.tabletop_route_candidates import tabletop_route_candidates


def quat(yaw):return (0.,0.,math.sin(yaw/2),math.cos(yaw/2))


class RouteCandidateTests(unittest.TestCase):
    def plan(self,target,other,yaw=.13,other_yaw=-.11,direction=-1):
        return tabletop_route_candidates(target,other,(.14,.09,.045),(.15,.145,.04),quat(yaw),quat(other_yaw),direction)

    def test_diagonal_front_route_shorter_but_no_robot_success_claim(self):
        p=self.plan((.40,.12,.7725),(.55,-.12,.77));c={x['route']:x for x in p['candidates']}
        self.assertFalse(c['direct']['object_envelope_eligible'])
        self.assertTrue(c['front']['object_envelope_eligible']);self.assertTrue(c['rear']['object_envelope_eligible'])
        self.assertLess(c['front']['object_path_length_m'],c['rear']['object_path_length_m'])
        self.assertGreater(c['front']['target_table_margin_m'],.015)
        self.assertFalse(p['training_ready'])

    def test_original_lateral_front_route_remains_rejected(self):
        p=self.plan((.43,.15,.7725),(.46,-.15,.77),.12,-.08);c={x['route']:x for x in p['candidates']}
        self.assertFalse(c['front']['object_envelope_eligible']);self.assertIn('target envelope crosses tabletop edge',c['front']['reasons'])
        self.assertTrue(c['rear']['object_envelope_eligible'])

    def test_separated_depth_route_direct_is_shortest(self):
        p=self.plan((.39,.01,.7725),(.60,-.01,.77),.06,-.05);c={x['route']:x for x in p['candidates']}
        self.assertTrue(c['direct']['object_envelope_eligible'])
        self.assertLessEqual(c['direct']['object_path_length_m'],min(x['object_path_length_m'] for x in c.values() if x['object_envelope_eligible']))

    def test_mirrored_y_direction_and_yaws_preserve_clearance(self):
        a=self.plan((.40,.12,.7725),(.55,-.12,.77));b=self.plan((.40,-.12,.7725),(.55,.12,.77),-.13,.11,1)
        for x,y in zip(a['candidates'],b['candidates']):
            self.assertAlmostEqual(x['object_path_length_m'],y['object_path_length_m'])
            self.assertAlmostEqual(x['min_object_axis_separation_m'],y['min_object_axis_separation_m'])
            self.assertEqual(x['object_envelope_eligible'],y['object_envelope_eligible'])

    def test_rear_endpoint_clearance_does_not_hide_collision_on_first_leg(self):
        p=self.plan((.40,0.,.7725),(.55,0.,.77),0.,0.)
        rear=next(x for x in p['candidates'] if x['route']=='rear')
        self.assertFalse(rear['object_envelope_eligible'])

    def test_invalid_geometry_rejected(self):
        with self.assertRaises(ValueError):self.plan((float('nan'),0.,.7725),(.55,-.12,.77))
        with self.assertRaises(ValueError):self.plan((.4,.12,.7725),(.55,-.12,.77),direction=0)
