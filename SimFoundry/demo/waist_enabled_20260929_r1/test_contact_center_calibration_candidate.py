import unittest
import numpy as np
from contact_center_calibration_candidate import ContactCenterCalibration
class ContactCenterTests(unittest.TestCase):
 def setUp(self):
  self.c=ContactCenterCalibration([[-.1,-.1,-.1],[.1,-.1,-.1],[-.1,.1,.1],[.1,.1,.1]])
  self.args=dict(mode='top_press',side='left',actor='mailer',hand_xyz=[0,0,0],hand_rotation=np.eye(3),object_xyz=[0,0,0],object_normal=[0,0,1])
 def packet(self,step):return dict(after_action_step=step-1,post_action_pose={'mailer':[0,0,0]},parcel_contacts=[dict(shapes=['/World/Robot/left_wrist/hand','/World/mailer/mesh'],force_world_N=[0,0,-2],position_world=[.03,.04,0])])
 def test_proposal_requires_three_samples_and_explicit_commit(self):
  for t in range(1,4):
   r=self.c.observe(self.packet(t),step=t,**self.args);self.assertEqual(r['ready'],t==3);self.assertIsNone(self.c.center_local)
  np.testing.assert_allclose(self.c.commit(),[.03,.04,0]);r=self.c.observe(None,step=4,**{**self.args,'mode':'top_release'});self.assertTrue(r['latched'])
 def test_stale_packet_and_pose_mismatch_clear_samples(self):
  self.c.observe(self.packet(1),step=1,**self.args);r=self.c.observe(self.packet(1),step=2,**self.args);self.assertFalse(r['ready']);self.assertEqual(len(self.c.samples),0)
  p=self.packet(3);p['post_action_pose']['mailer']=[.1,0,0];self.assertEqual(self.c.observe(p,step=3,**self.args)['reason'],'post_action_pose_mismatch')
 def test_wrong_hand_and_guard_cannot_commit(self):
  p=self.packet(1);p['parcel_contacts'][0]['shapes'][0]='/World/Robot/right_wrist/hand';self.assertFalse(self.c.observe(p,step=1,**self.args)['ready'])
  for t in (2,3):self.c.observe(self.packet(t),step=t,**self.args)
  self.assertFalse(self.c.observe(self.packet(4),step=4,**{**self.args,'mode':'front_guard_lift'})['ready'])
  with self.assertRaises(ValueError):self.c.commit()
 def test_variable_contact_is_not_stable_and_duplicates_rejected(self):
  for t in range(1,4):
   p=self.packet(t);p['parcel_contacts'][0]['position_world'][0]+=.005*t;r=self.c.observe(p,step=t,**self.args)
  self.assertFalse(r['ready'])
  with self.assertRaises(ValueError):self.c.observe(self.packet(3),step=3,**self.args)
if __name__=='__main__':unittest.main()
