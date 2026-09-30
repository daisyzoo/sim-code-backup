import unittest
import math
from simfoundry.data.frontal_bypass import frontal_bypass_plan,FrontalBypassState,extent_x_from_quat,rear_contact_world_y

class FrontalBypassTests(unittest.TestCase):
    def plan(self):
        return frontal_bypass_plan([.43,-.15,.77],[.46,.15,.77],[.15,.145],[.14,.09],.12,-.08,1)
    def test_opposing_path_blocks_but_own_side_does_not(self):
        self.assertTrue(self.plan()['required'])
        p=frontal_bypass_plan([.43,.15,.77],[.46,-.15,.77],[.15,.145],[.14,.09],.12,-.08,1)
        self.assertFalse(p['required'])
    def test_depth_separated_path_does_not_require_bypass(self):
        p=frontal_bypass_plan([.6,-.01,.77],[.39,.01,.77],[.15,.145],[.14,.09],-.05,.06,1)
        self.assertFalse(p['required'])
    def test_transition_requires_object_clearance_not_elapsed_time_or_hand_reach(self):
        p=self.plan();s=FrontalBypassState(p,mode='rear_push',push_command_x=.40,start_palm=(.4,-.15,.9))
        for _ in range(400):s.update([.7,-.15,.81],[.43,-.15,.77])
        self.assertEqual(s.mode,'rear_push')
        self.assertLessEqual(s.push_command_x,p['rear_goal_x']-p['target_radius_x']-.035)
        r=s.update([.53,-.15,.82],[p['rear_goal_x']+.001,-.15,.77])
        self.assertEqual(r['mode'],'bypass_sweep');self.assertEqual(r['target_xyz'],(.53,-.15,.82))
    def test_release_uses_original_direction_and_keeps_actual_xy(self):
        s=FrontalBypassState(self.plan(),mode='bypass_sweep',sweep_start=(.53,-.15,.82),start_palm=(.4,.15,.9))
        r=s.update([.51,.26,.82],[.64,.21,.77])
        self.assertEqual(r['mode'],'bypass_release');self.assertEqual(r['target_xyz'],(.51,.26,.92))
    def test_invalid_observation_rejected(self):
        with self.assertRaises(ValueError):FrontalBypassState(self.plan()).update([math.nan,0,1],[.4,0,.77])

    def test_current_rotation_changes_required_clearance(self):
        p=self.plan();s=FrontalBypassState(p,mode='rear_push',push_command_x=.4,start_palm=(.4,0,.9))
        r=s.update([.55,-.15,.82],[p['rear_goal_x']+.001,-.15,.77],target_radius_x=p['target_radius_x']+.03)
        self.assertEqual(r['mode'],'rear_push')
        self.assertAlmostEqual(extent_x_from_quat([.14,.09,.045],[0,0,0,1]),.07)
        self.assertAlmostEqual(extent_x_from_quat([.14,.09,.045],[0,0,math.sin(math.pi/8),math.cos(math.pi/8)]),(.07+.045)/math.sqrt(2))

    def test_feedback_can_extend_early_endpoint_without_false_clearance(self):
        p=self.plan();s=FrontalBypassState(p,mode='rear_push',push_command_x=.49,feedback_rear_endpoint=True)
        old=p['rear_goal_x']-p['target_radius_x']-.035
        for _ in range(100):
            prior=s.push_command_x
            r=s.update([.51,-.15,.81],[.56,-.15,.77])
            self.assertLessEqual(abs(s.push_command_x-prior),.00300001)
        self.assertGreater(s.push_command_x,old)
        self.assertLessEqual(s.push_command_x,.53)
        self.assertEqual(r['mode'],'rear_push')
        self.assertFalse(r['rear_clearance_measured'])

    def test_y_tracking_uses_actual_object_without_jumping(self):
        p=self.plan();s=FrontalBypassState(p,mode='rear_push',push_command_x=.49,feedback_rear_endpoint=True,follow_target_y=True)
        r=s.update([.49,-.15,.81],[.56,-.08,.77])
        self.assertAlmostEqual(r['target_xyz'][1],-.148)
        for _ in range(80):r=s.update([.49,-.15,.81],[.56,-.08,.77])
        self.assertAlmostEqual(r['target_xyz'][1],-.08)
        self.assertEqual(r['mode'],'rear_push')

    def test_recontact_lifts_before_cross_and_uses_actual_pose_transitions(self):
        p=self.plan();s=FrontalBypassState(p,mode='rear_push',push_command_x=.53,recontact_after_rear=True)
        obj=[.66,-.06,.77]
        r=s.update([.53,-.06,.82],obj)
        self.assertEqual(r['mode'],'bypass_lift');self.assertEqual(r['target_xyz'],(.53,-.06,.92))
        for _ in range(100):r=s.update([.53,-.06,.82],obj)
        self.assertEqual(r['mode'],'bypass_lift')
        r=s.update([.53,-.06,.92],obj);self.assertEqual(r['mode'],'bypass_cross')
        self.assertAlmostEqual(r['target_xyz'][0],.60);self.assertAlmostEqual(r['target_xyz'][1],-.12)
        r=s.update([.60,-.12,.92],obj);self.assertEqual(r['mode'],'bypass_press')
        for _ in range(3):r=s.update([.60,-.12,.85],obj)
        self.assertEqual(r['mode'],'bypass_sweep');self.assertEqual(r['target_xyz'],(.60,-.12,.85))

    def test_planned_sweep_x_starts_continuously_then_recovers_flank_target(self):
        s=FrontalBypassState(self.plan(),mode='bypass_sweep',sweep_start=(.55,-.12,.85),recontact_xy=(.58,-.12),planned_sweep_x=True)
        r=s.update([.55,-.12,.85],[.65,-.06,.77])
        self.assertAlmostEqual(r['target_xyz'][0],.55)
        xs=[r['target_xyz'][0]]
        for _ in range(40):xs.append(s.update([.55,-.12,.85],[.65,-.06,.77])['target_xyz'][0])
        self.assertAlmostEqual(xs[-1],.58)
        self.assertTrue(all(0<=b-a<=.00151 for a,b in zip(xs,xs[1:])))
        self.assertEqual(s.mode,'bypass_sweep')

    def test_tracked_sweep_waits_with_stationary_object_and_follows_new_position(self):
        s=FrontalBypassState(self.plan(),mode='bypass_sweep',sweep_start=(.55,-.12,.85),tracked_sweep=True)
        previous=(.55,-.12)
        for _ in range(100):
            r=s.update([.55,-.12,.85],[.65,-.06,.77])
            self.assertLessEqual(abs(r['target_xyz'][0]-previous[0]),.0030001)
            self.assertLessEqual(abs(r['target_xyz'][1]-previous[1]),.0060001)
            previous=r['target_xyz'][:2]
        self.assertAlmostEqual(previous[0],.59);self.assertAlmostEqual(previous[1],-.02)
        self.assertEqual(s.mode,'bypass_sweep')
        r=s.update([.55,-.12,.85],[.67,-.03,.77])
        self.assertGreater(r['target_xyz'][0],previous[0]);self.assertGreater(r['target_xyz'][1],previous[1])

    def test_lead_tracks_direction_and_rejects_invalid_value(self):
        p=self.plan();p['direction']=-1;p['initial_target_xyz'][1]=.15
        s=FrontalBypassState(p,mode='bypass_sweep',sweep_start=(.55,.10,.85),tracked_sweep=True,sweep_lead_y=.01)
        for _ in range(100):r=s.update([.55,.10,.85],[.65,.02,.77])
        self.assertAlmostEqual(r['target_xyz'][1],.01)
        s.sweep_lead_y=math.nan
        with self.assertRaises(ValueError):s.update([.55,.10,.85],[.65,.02,.77])

    def test_off_center_rear_contact_opposes_sorting_direction_and_is_rate_limited(self):
        for direction in [-1,1]:
            p=self.plan();p['direction']=direction
            s=FrontalBypassState(p,mode='rear_push',push_command_x=.49,follow_target_y=True,rear_contact_y_offset_m=.03)
            previous=p['initial_target_xyz'][1]
            for _ in range(50):
                r=s.update([.49,-.15,.81],[.56,-.08,.77])
                self.assertLessEqual(abs(r['target_xyz'][1]-previous),.00200001)
                previous=r['target_xyz'][1]
            self.assertAlmostEqual(previous,-.08-direction*.03)
            self.assertEqual(r['mode'],'rear_push')
        s.rear_contact_y_offset_m=math.nan
        with self.assertRaises(ValueError):s.update([.49,-.15,.81],[.56,-.08,.77])

    def test_object_frame_contact_rotates_front_face_lever(self):
        self.assertAlmostEqual(rear_contact_world_y(-.1,.15,1,.03,[0,0,0,1]),-.13)
        yaw=math.pi/6;quat=[0,0,math.sin(yaw/2),math.cos(yaw/2)]
        desired=-.1-.075*math.sin(yaw)-.03*math.cos(yaw)
        self.assertAlmostEqual(rear_contact_world_y(-.1,.15,1,.03,quat),desired)
        p=self.plan();s=FrontalBypassState(p,mode='rear_push',push_command_x=.49,follow_target_y=True,rear_contact_y_offset_m=.03,rear_contact_object_frame=True)
        for _ in range(100):r=s.update([.49,-.15,.81],[.56,-.1,.77],target_quat=quat)
        self.assertAlmostEqual(r['target_xyz'][1],desired)
        with self.assertRaises(ValueError):s.update([.49,-.15,.81],[.56,-.1,.77])
