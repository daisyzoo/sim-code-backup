import unittest,math,struct
from pathlib import Path
from simfoundry.data.fingertip_bypass import contact_pad_mesh_vertex,distal_mesh_vertex,side_surface_point,FingertipBypassState
from simfoundry.data.frontal_bypass import frontal_bypass_plan,FrontalBypassState

class FingertipTests(unittest.TestCase):
    def state(self):
        p=frontal_bypass_plan([.46,-.15,.77],[.43,.15,.7725],[.15,.145],[.14,.09],0.,0.,1)
        return FingertipBypassState(FrontalBypassState(p,mode='rear_push',push_command_x=.5),'left',(.15,.145,.04))
    def update(self,s,tip,target=(.62,-.04,.77)):
        return s.update([.53,-.06,.82],target,[.43,.15,.7725],.075,.07,tip=tip,quat=(0,0,0,1))
    def test_vertex_exists_in_actual_mesh_and_is_distal(self):
        root=Path(__file__).resolve().parents[1]/'third_party/unitree_ros/robots/g1_description/meshes'
        for side in ['left','right']:
            b=(root/f'{side}_wrist_roll_rubber_hand.STL').read_bytes();count=struct.unpack_from('<I',b,80)[0]
            self.assertEqual(len(b),84+50*count)
            verts=[]
            for row in struct.iter_unpack('<12fH',b[84:]):verts.extend([row[3:6],row[6:9],row[9:12]])
            self.assertIn(contact_pad_mesh_vertex(side),verts)
            v=distal_mesh_vertex(side);self.assertIn(v,verts);self.assertEqual(v[0],max(x[0] for x in verts))
    def test_surface_uses_actual_rotation(self):
        p=side_surface_point([.6,0,.77],[0,0,0,1],[.14,.09,.045],-1)
        self.assertAlmostEqual(p[0],.545);self.assertAlmostEqual(p[1],.045);self.assertAlmostEqual(p[2],.7895)
        p=side_surface_point([.6,0,.77],[0,0,math.sin(math.pi/4),math.cos(math.pi/4)],[.14,.09,.045],-1)
        self.assertAlmostEqual(p[0],.57);self.assertAlmostEqual(p[1],.07)
    def test_no_early_switch_without_rear_clearance(self):
        s=self.state();r=self.update(s,[.58,-.1,.8],target=(.5,-.04,.77))
        self.assertEqual(r['mode'],'rear_push');self.assertIsNone(r['control_offset_local'])
    def test_lift_before_side_approach_and_actual_position_before_push(self):
        s=self.state();r=self.update(s,[.58,-.1,.8]);self.assertEqual(r['mode'],'tip_lift');self.assertEqual(r['target_xyz'],(.58,-.1,.92))
        for _ in range(80):self.assertEqual(self.update(s,[.58,-.1,.8])['mode'],'tip_lift')
        r=self.update(s,[.58,-.1,.92]);self.assertEqual(r['mode'],'tip_cross');xy=r['target_xyz'][:2]
        r=self.update(s,[*xy,.92]);self.assertEqual(r['mode'],'tip_press');press=r['target_xyz']
        for _ in range(3):r=self.update(s,press)
        self.assertEqual(r['mode'],'tip_sweep');self.assertEqual(r['control_offset_local'],distal_mesh_vertex('left'))
        self.assertLessEqual(abs(r['target_xyz'][1]-press[1]),.00400001)
    def test_release_depends_on_original_goal(self):
        s=self.state();s.tip_mode='tip_sweep';s.command=(.56,.18,.79)
        r=self.update(s,[.56,.18,.79],target=(.62,.21,.77));self.assertEqual(r['mode'],'tip_release');self.assertEqual(r['target_xyz'],(.56,.18,.92))
    def test_invalid_quat_rejected(self):
        with self.assertRaises(ValueError):side_surface_point([.6,0,.77],[0,0,0,0],[.14,.09,.045],-1)

    def test_rotated_contact_face_stays_on_approach_side(self):
        for direction in [-1,1]:
            for yaw in [0,math.pi/2,math.pi,3*math.pi/2]:
                p=side_surface_point([.6,0,.77],[0,0,math.sin(yaw/2),math.cos(yaw/2)],[.14,.09,.045],direction)
                self.assertGreater(-direction*p[1],.04)
                self.assertLess(p[0],.6)

    def test_pad_offset_matches_selected_control_point_and_release(self):
        s=self.state();s.use_contact_pad=True
        r=self.update(s,[.58,-.1,.8])
        self.assertEqual(s.control_vertex(),contact_pad_mesh_vertex('left'))
        self.assertEqual(r['control_offset_local'],s.control_vertex())
        self.assertEqual(r['target_xyz'],(.58,-.1,.92))
        s.tip_mode='tip_sweep';s.command=(.56,.18,.79)
        r=self.update(s,[.56,.18,.79],target=(.62,.21,.77))
        self.assertEqual(r['mode'],'tip_release')
        self.assertEqual(r['control_offset_local'],s.control_vertex())

    def test_strict_descent_rejects_old_18mm_undershoot(self):
        s=self.state();s.strict_descent=True
        self.update(s,[.58,-.1,.8])
        r=self.update(s,[.58,-.1,.92]);xy=r['target_xyz'][:2]
        for _ in range(30):
            r=self.update(s,[xy[0]-.018,xy[1],.92])
            self.assertEqual(r['mode'],'tip_cross')
            self.assertEqual(r['target_xyz'][2],.92)
        r=self.update(s,[xy[0]-.004,xy[1]+.004,.92])
        self.assertEqual(r['mode'],'tip_press')
