import math,unittest
from simfoundry.data.top_contact_bypass import support_mesh,support_vertex,top_surface_point,TopContactBypassState
from simfoundry.data.frontal_bypass import frontal_bypass_plan,FrontalBypassState

class TopContactTests(unittest.TestCase):
    def state(self):
        p=frontal_bypass_plan([.46,-.15,.77],[.43,.15,.7725],[.15,.145],[.14,.09],0.,0.,1)
        return TopContactBypassState(FrontalBypassState(p,mode='rear_push',push_command_x=.5),'left',(.15,.145,.04))
    def update(self,s,tip,load=0.,target=(.62,-.04,.77),**extra):
        return s.update([.53,-.06,.82],target,[.43,.15,.7725],.075,.07,tip=tip,quat=(0,0,0,1),control_offset_local=(.2,0,0),load_n=load,**extra)
    def test_hand_obstacle_guard_lifts_then_shifts_next_contact_inward(self):
        s=self.state();s.corner_contact=True;s.forward_margin_m=.04;s.edge_guard_m=.012;s.hand_obstacle_guard_m=.005
        s.top_mode='top_press';s.load.bias_m=-.003
        r=self.update(s,[.555,-.04,.79],load=3.,hand_obstacle_gap_m=.004)
        self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['last_recontact_reason'],'hand_obstacle_clearance')
        self.assertEqual(r['contact_load']['applied_z_bias_m'],0.);self.assertEqual(s.contact_rear_shift_m,.01)
        self.assertIsNone(s.corner_local)
        from simfoundry.data.top_push_contact_geometry import top_front_contact_local
        original=top_front_contact_local((0,0,0,1),s.size,1,.04)
        r=self.update(s,[.555,-.04,.91],hand_obstacle_gap_m=.05)
        self.assertAlmostEqual(s.corner_local[0],original[0]+.01)
        for _ in range(5):
            s.top_mode='top_press';self.update(s,[.565,-.04,.79],load=3.,hand_obstacle_gap_m=.001)
        self.assertEqual(s.contact_rear_shift_m,.03)
        with self.assertRaises(ValueError):self.update(s,[.565,-.04,.91])
    def test_support_is_lowest_and_rotates_in_xyzw_convention(self):
        for side in ['left','right']:
            v=support_vertex(side,[0,0,0,1],[0,0,0,1]);self.assertEqual(v[2],min(p[2] for p in support_mesh()[side]))
            v=support_vertex(side,[0,math.sin(math.pi/4),0,math.cos(math.pi/4)],[0,0,0,1]);self.assertAlmostEqual(v[0],max(p[0] for p in support_mesh()[side]))
    def test_top_point_inside_face_and_toward_robot_after_rotation(self):
        for yaw in [0,math.pi/2,math.pi]:
            p=top_surface_point([.6,0,.77],[0,0,math.sin(yaw/2),math.cos(yaw/2)],[.15,.145,.04]);self.assertLess(p[0],.6);self.assertAlmostEqual(p[2],.79)
    def test_rear_clearance_required(self):
        r=self.update(self.state(),[.55,-.1,.8],target=(.5,-.04,.77));self.assertEqual(r['mode'],'rear_push');self.assertIsNone(r['control_offset_local'])
    def test_no_force_no_push_and_bounded_downward_bias(self):
        s=self.state();self.assertEqual(self.update(s,[.55,-.1,.8])['mode'],'top_lift')
        r=self.update(s,[.55,-.1,.91]);self.assertEqual(r['mode'],'top_cross')
        xy=r['target_xyz'][:2];r=self.update(s,[*xy,.91]);self.assertEqual(r['mode'],'top_press')
        for _ in range(80):r=self.update(s,[*xy,.79])
        self.assertEqual(r['mode'],'top_press');self.assertAlmostEqual(r['contact_load']['applied_z_bias_m'],-.006)
        self.assertGreaterEqual(r['target_xyz'][2],.786-1e-10)
        for _ in range(5):r=self.update(s,[*xy,.79],load=3.)
        self.assertEqual(r['mode'],'top_push')
    def test_goal_releases_measured_support_point(self):
        s=self.state();s.top_mode='top_push';s.command=(.56,.18,.79)
        r=self.update(s,[.56,.18,.79],load=3.,target=(.62,.21,.77));self.assertEqual(r['mode'],'top_release');self.assertEqual(r['target_xyz'],(.56,.18,.91))

    def test_guarded_descent_pauses_when_horizontal_tracking_is_lost(self):
        s=self.state();s.guarded_descent=True
        self.update(s,[.55,-.1,.8]);r=self.update(s,[.55,-.1,.91]);xy=r['target_xyz'][:2]
        r=self.update(s,[*xy,.91]);self.assertEqual(r['mode'],'top_descend');height=r['target_xyz'][2]
        for _ in range(30):
            r=self.update(s,[xy[0]-.02,xy[1],.9]);self.assertEqual(r['target_xyz'][2],height)
            self.assertEqual(r['contact_load']['applied_z_bias_m'],0.)
        r=self.update(s,[*xy,.9]);self.assertAlmostEqual(r['target_xyz'][2],height-.0015)
        r=self.update(s,[xy[0]-.02,xy[1],.8]);self.assertGreater(r['target_xyz'][2],height-.0015)
    def test_guarded_press_retreats_instead_of_chasing_front_contact(self):
        s=self.state();s.guarded_descent=True;s.top_mode='top_press';s.load.bias_m=-.004
        point=top_surface_point([.62,-.04,.77],[0,0,0,1],s.size)
        r=self.update(s,[point[0]-.02,point[1],point[2]],load=2.)
        self.assertEqual(r['mode'],'top_descend');self.assertGreaterEqual(r['target_xyz'][2],point[2]+.025);self.assertEqual(s.load.bias_m,0.);self.assertEqual(r['contact_load']['applied_z_bias_m'],0.)

    def test_continuous_drag_advances_then_lifts_on_three_lost_contact_samples(self):
        s=self.state();s.guarded_descent=True;s.continuous_drag=True;s.top_mode='top_push';s.command=(.565,-.04,.79)
        previous=-.04
        for _ in range(20):
            r=self.update(s,[.565,-.04,.79],load=3.)
            self.assertAlmostEqual(r['target_xyz'][1]-previous,.003);previous=r['target_xyz'][1]
            self.assertEqual(r['mode'],'top_push')
        for _ in range(3):r=self.update(s,[.565,-.04,.79],load=0.)
        self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['recontacts'],1);self.assertEqual(r['contact_load']['applied_z_bias_m'],0.)

    def test_drag_advance_is_configurable_and_invalid_value_rejected(self):
        s=self.state();s.continuous_drag=True;s.drag_step_m=.008;s.top_mode='top_push';s.command=(.565,-.04,.79)
        r=self.update(s,[.565,-.04,.79],load=3.);self.assertAlmostEqual(r['target_xyz'][1],-.032)
        s.drag_step_m=math.nan
        with self.assertRaises(ValueError):self.update(s,[.565,-.04,.79],load=3.)

    def test_fraction_uses_selected_rotated_half_width(self):
        for yaw in [0,math.pi/2]:
            q=[0,0,math.sin(yaw/2),math.cos(yaw/2)]
            p=top_surface_point([.6,0,.77],q,[.14,.09,.045],front_inset_fraction=.8)
            self.assertAlmostEqual(p[0],.6-(.07 if yaw==0 else .045)*.2)
            self.assertAlmostEqual(p[1],0.)
            center=top_surface_point([.6,0,.77],q,[.14,.09,.045],front_inset_fraction=1.)
            self.assertAlmostEqual(center[0],.6)
        for fraction in [0.,1.01,math.nan]:
            with self.assertRaises(ValueError):top_surface_point([.6,0,.77],[0,0,0,1],[.14,.09,.045],front_inset_fraction=fraction)

    def test_corner_is_latched_across_yaw_sign_change(self):
        from simfoundry.data.top_contact_bypass import local_surface_world
        s=self.state();s.corner_contact=True
        self.update(s,[.55,-.1,.8]);local=s.corner_local
        r=s.update([.53,-.06,.82],[.62,-.04,.77],[.43,.15,.7725],.075,.07,
            tip=[.55,-.1,.91],quat=(0,0,math.sin(.03),math.cos(.03)),control_offset_local=(.2,0,0),load_n=0.)
        self.assertEqual(s.corner_local,local)
        self.assertEqual(r['parcel_top_xyz'],local_surface_world([.62,-.04,.77],(0,0,math.sin(.03),math.cos(.03)),local))
        s.continuous_drag=True;s.top_mode='top_push';s.command=(.565,-.04,.79)
        for _ in range(3):self.update(s,[.565,-.04,.79],load=0.)
        self.assertIsNone(s.corner_local);self.assertEqual(s.mode,'top_lift')

    def test_approach_bias_compensates_persistent_lag_before_descent(self):
        from simfoundry.data.top_contact_bypass import top_corner_local,local_surface_world
        s=self.state();s.corner_contact=True;s.approach_compensation=True;s.guarded_descent=True;s.top_mode='top_descend';s.descent_z=.91
        nominal=local_surface_world([.62,-.04,.77],[0,0,0,1],top_corner_local([0,0,0,1],s.size))
        tip=[nominal[0]-.006,nominal[1],.91]
        for _ in range(50):
            before=s.approach_xy_bias.copy();r=self.update(s,tip)
            self.assertLessEqual(max(abs(a-b) for a,b in zip(s.approach_xy_bias,before)),.000500001)
            self.assertLessEqual(max(abs(a) for a in s.approach_xy_bias),.01)
            tip=[r['target_xyz'][0]-.006,r['target_xyz'][1],r['target_xyz'][2]]
        self.assertLess(abs(tip[0]-nominal[0]),.003)
        self.assertGreater(s.approach_xy_bias[0],.004)
        before=s.approach_xy_bias.copy();self.update(s,tip,load=3.);self.assertEqual(s.approach_xy_bias,before)
    def test_compensated_near_contact_misalignment_lifts_for_realign(self):
        s=self.state();s.approach_compensation=True;s.guarded_descent=True;s.top_mode='top_descend';s.descent_z=.794
        surface=top_surface_point([.62,-.04,.77],[0,0,0,1],s.size)
        r=self.update(s,[surface[0]-.004,surface[1],.8])
        self.assertGreater(r['target_xyz'][2],.8)
        self.assertEqual(s.approach_xy_bias,[0.,0.])

    def guarded_state(self):
        s=self.state();s.corner_contact=True;s.forward_margin_m=.025;s.edge_guard_m=.012;s.recovery_clearance_m=.05;s.continuous_drag=True;s.top_mode='top_push';s.command=(.565,-.04,.79)
        return s
    def test_loaded_edge_with_force_still_present_triggers_short_recovery(self):
        s=self.guarded_state();s.load.bias_m=-.003
        r=self.update(s,[.565,-.04,.79],load=3.,loaded_contact=dict(valid=True,normal_load_n=3.,weighted_forward_edge_distance_m=.011))
        self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['last_recontact_reason'],'loaded_edge_margin');self.assertEqual(r['recontacts'],1);self.assertEqual(r['contact_load']['applied_z_bias_m'],0.)
        self.assertAlmostEqual(r['target_xyz'][2],.8525);self.assertIsNone(s.corner_local)
    def test_missing_contact_does_not_invent_edge_trigger(self):
        s=self.guarded_state();r=self.update(s,[.565,-.04,.79],load=3.,loaded_contact=dict(valid=False,normal_load_n=0.,weighted_forward_edge_distance_m=None))
        self.assertEqual(r['mode'],'top_push');self.assertEqual(r['recontacts'],0)
    def test_first_top_transit_and_final_release_keep_original_height(self):
        s=self.guarded_state();s.top_mode='top_lift';s.start=(.55,0,.8)
        r=self.update(s,[.55,0,.8]);self.assertEqual(r['target_xyz'][2],.91)
        s=self.guarded_state();r=self.update(s,[.56,.18,.79],load=3.,target=(.62,.21,.77),loaded_contact=dict(valid=True,normal_load_n=3.,weighted_forward_edge_distance_m=.005))
        self.assertEqual(r['mode'],'top_release');self.assertEqual(r['target_xyz'][2],.91)
    def test_incipient_tilt_triggers_recovery_without_edge_packet(self):
        s=self.guarded_state();angle=.04
        r=s.update([.53,-.06,.82],[.62,-.04,.77],[.43,.15,.7725],.075,.07,tip=[.565,-.04,.79],quat=(math.sin(angle/2),0,0,math.cos(angle/2)),control_offset_local=(.2,0,0),load_n=3.)
        self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['last_recontact_reason'],'incipient_tilt');self.assertGreater(r['travel_height_m'],.84)

    def test_push_x_reference_holds_when_object_drifts(self):
        s=self.guarded_state();s.hold_push_x=True
        r=self.update(s,[.565,-.04,.79],load=3.);anchor=r['push_x_anchor_m'];self.assertIsNotNone(anchor)
        for _ in range(20):
            r=self.update(s,[.565,-.04,.79],load=3.,target=(.65,-.04,.77))
            self.assertEqual(r['push_x_anchor_m'],anchor)
        self.assertAlmostEqual(r['target_xyz'][0],anchor)
        self.assertNotAlmostEqual(r['target_xyz'][0],r['parcel_top_xyz'][0])
    def test_push_x_hold_clears_on_recontact(self):
        s=self.guarded_state();s.hold_push_x=True
        self.update(s,[.565,-.04,.79],load=3.)
        self.assertIsNotNone(s.push_x_anchor)
        r=self.update(s,[.565,-.04,.79],load=3.,loaded_contact=dict(valid=True,normal_load_n=3.,weighted_forward_edge_distance_m=.011))
        self.assertEqual(r['mode'],'top_lift');self.assertIsNone(r['push_x_anchor_m'])

    def test_cross_axis_force_correction_preserves_anchor_and_resets(self):
        s=self.guarded_state();s.hold_push_x=True;s.cross_axis_admittance=True
        loaded=dict(valid=True,normal_load_n=3.,weighted_forward_edge_distance_m=.03,force_on_target_world_n=[1.,2.,-3.])
        r=self.update(s,[.565,-.04,.79],load=3.,loaded_contact=loaded);anchor=r['push_x_anchor_m']
        self.assertLess(r['cross_axis_admittance']['command_bias_x_m'],0.)
        for _ in range(20):r=self.update(s,[.565,-.04,.79],load=3.,loaded_contact=loaded)
        self.assertEqual(r['push_x_anchor_m'],anchor);self.assertLess(r['target_xyz'][0],anchor);self.assertGreaterEqual(r['target_xyz'][0],anchor-.01)
        loaded['weighted_forward_edge_distance_m']=.005
        r=self.update(s,[.565,-.04,.79],load=3.,loaded_contact=loaded)
        self.assertEqual(r['mode'],'top_lift');self.assertEqual(s.cross_axis_control.bias_m,0.);self.assertEqual(s.cross_axis_control.filtered_force_n,0.)
