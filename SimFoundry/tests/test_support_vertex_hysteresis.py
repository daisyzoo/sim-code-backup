import math,unittest
from unittest.mock import patch
from simfoundry.data.support_vertex_hysteresis import support_vertex_with_hysteresis
from simfoundry.data.top_contact_bypass import support_vertex,support_mesh,rotation_xyzw

class SupportVertexHysteresisTests(unittest.TestCase):
 def test_nearly_coplanar_far_vertices_do_not_chatter(self):
  vertices=((-0.02,0.,0.),(.02,0.,0.))
  with patch('simfoundry.data.support_vertex_hysteresis.support_mesh',return_value={'left':vertices}):
   point=None
   for a in (.001,-.001,.001,-.001):
    q=(0.,math.sin(a/2),0.,math.cos(a/2))
    point,meta=support_vertex_with_hysteresis('left',q,(0,0,0,1),point)
    self.assertEqual(point,vertices[1]);self.assertLessEqual(meta['support_plane_excess_m'],.0002)
   point,meta=support_vertex_with_hysteresis('left',(0,math.sin(-.1/2),0,math.cos(-.1/2)),(0,0,0,1),point)
   self.assertEqual(point,vertices[0]);self.assertTrue(meta['vertex_changed'])
 def test_real_hull_rotation_path_respects_height_bound(self):
  for side in ('left','right'):
   point=None
   for i in range(200):
    a=i*.031;q=(math.sin(a/2),0.,0.,math.cos(a/2));pq=(0.,math.sin(.12),0.,math.cos(.12))
    point,meta=support_vertex_with_hysteresis(side,q,pq,point)
    self.assertIn(point,support_mesh()[side]);self.assertGreaterEqual(meta['support_plane_excess_m'],-1e-12);self.assertLessEqual(meta['support_plane_excess_m'],.0002+1e-12)
 def test_zero_tolerance_exact_selector_parity(self):
  for side in ('left','right'):
   previous=None
   for a in (0.,.1,-.1,1.5,-2.):
    q=(0.,math.sin(a/2),0.,math.cos(a/2));p,meta=support_vertex_with_hysteresis(side,q,(0,0,0,1),previous,0.)
    self.assertEqual(p,support_vertex(side,q,(0,0,0,1)));previous=p
 def test_invalid_tolerance_and_non_mesh_point_rejected(self):
  for tol in (-.1,float('nan'),.001):
   with self.assertRaises(ValueError):support_vertex_with_hysteresis('left',(0,0,0,1),(0,0,0,1),max_excess_m=tol)
  with self.assertRaises(ValueError):support_vertex_with_hysteresis('left',(0,0,0,1),(0,0,0,1),(999.,0,0))

if __name__=='__main__':unittest.main()
