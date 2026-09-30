import unittest
import numpy as np
from test_bounded_servo import controller

class ObjectFeedbackTests(unittest.TestCase):
 def test_stalled_object_limits_goal_and_speed_both_directions(self):
  mod=controller()
  for direction,side in [(1.,'left'),(-1.,'right')]:
   s=mod['CartesianSweepState'](side,.51,0.,object_feedback_lead=.04)
   ys=[]
   for t in range(100):
    s.mode_step=t;ys.append(mod['object_feedback_target_y'](s,0.,direction,-direction*.11))
   self.assertLessEqual(np.abs(np.diff(ys)).max(),.00600001)
   self.assertAlmostEqual(ys[-1],direction*.04)
   self.assertLessEqual(max(direction*y for y in ys),.04000001)
 def test_no_coordinate_write_and_missing_feedback_rejected(self):
  m=controller();s=m['CartesianSweepState']('left',.51,.02,object_feedback_lead=.04)
  for y in [None,float('nan')]:
   with self.assertRaises(ValueError):m['object_feedback_target_y'](s,y,1.,-.09)
  self.assertEqual(s.parcel_y,.02);self.assertEqual(s.parcel_x,.51)
 def test_handover_requires_motion_and_freezes_measured_start(self):
  import torch
  from types import SimpleNamespace
  m=controller();jac=torch.zeros(1,1,6,23)
  for i in range(3):jac[0,0,i,i]=1.
  data=SimpleNamespace(body_pos_w=SimpleNamespace(torch=torch.tensor([[[.30,.02,.832]]])),body_quat_w=SimpleNamespace(torch=torch.tensor([[[1.,0.,0.,0.]]])),body_link_jacobian_w=SimpleNamespace(torch=jac),joint_pos=SimpleNamespace(torch=torch.zeros(1,23)))
  robot=SimpleNamespace(data=data,num_base_dofs=0)
  state=m['CartesianSweepState']('left',.51,0.,mode='sweep',joint_ids=(0,1,2,3,4),jacobian_body_idx=0,contact_palm_z=.84,object_feedback_lead=.04,contact_confirmed_sweep=True)
  action=np.zeros(23)
  def run(y):m['cartesian_sweep_palm'](robot,{'left':0,'right':0},action,state=state,step=80,default_q=np.zeros(23),observed_parcel_y=y)
  run(.01);self.assertEqual(state.mode,'sweep')
  run(.02);self.assertEqual(state.mode,'engaged_sweep');np.testing.assert_allclose(state.engaged_sweep_start,[.5,.02,.839],atol=1e-6)
  run(.24);self.assertEqual(state.mode,'hold');self.assertAlmostEqual(state.feedback_hold_y,.02,places=6)
if __name__=='__main__':unittest.main()
