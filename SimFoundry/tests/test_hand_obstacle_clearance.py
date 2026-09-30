import itertools,math,unittest
import numpy as np
from simfoundry.data.hand_obstacle_clearance import ConvexFaceSeparation

class HandObstacleClearanceTests(unittest.TestCase):
 def setUp(self):self.cube=ConvexFaceSeparation(np.array(list(itertools.product([-1,1],repeat=3)))*.05)
 def test_known_separation_touch_and_overlap(self):
  for x,gap in [(.12,.02),(.1,0.),(.09,-.01)]:
   self.assertAlmostEqual(self.cube.gap([0,0,0],[0,0,0,1],[x,0,0],[0,0,0,1],[.1]*3),gap)
 def test_rigid_rotation_and_translation_invariance(self):
  q=[0,0,math.sin(.4),math.cos(.4)];d=[.12*math.cos(.8),.12*math.sin(.8),0]
  self.assertAlmostEqual(self.cube.gap([1,2,3],q,[1+d[0],2+d[1],3],q,[.1]*3),.02)
 def test_invalid_geometry_rejected(self):
  for size in [[.1,-.1,.1],[math.nan,.1,.1]]:
   with self.assertRaises(ValueError):self.cube.gap([0,0,0],[0,0,0,1],[.2,0,0],[0,0,0,1],size)

if __name__=='__main__':unittest.main()
