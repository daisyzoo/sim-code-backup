import math,unittest
from simfoundry.data.top_contact_bypass import rotation_xyzw,top_corner_local
from simfoundry.data.top_push_contact_geometry import top_trailing_corner_local,forward_edge_distance,top_front_contact_local

class TopPushContactGeometryTests(unittest.TestCase):
 def test_both_directions_choose_trailing_side(self):
  size=(.1344,.0864,.045)
  for direction in (-1,1):
   p=top_trailing_corner_local((0,0,0,1),size,direction)
   self.assertAlmostEqual(p[0],-.0572);self.assertAlmostEqual(p[1],-direction*.0332)
   self.assertAlmostEqual(forward_edge_distance(p,(0,0,0,1),size,direction),.0764)
 def test_rotated_front_face_and_trailing_choice(self):
  size=(.135,.1276,.04)
  for yaw in (-2.7,-1.6,-.16,.11,1.4,2.8):
   q=(0,0,math.sin(yaw/2),math.cos(yaw/2));r=rotation_xyzw(q);front=max((0,1),key=lambda i:abs(r[0][i]));other=1-front
   for direction in (-1,1):
    p=top_trailing_corner_local(q,size,direction);op=list(p);op[other]*=-1
    self.assertLessEqual(direction*sum(r[1][i]*p[i] for i in (0,1)),direction*sum(r[1][i]*op[i] for i in (0,1)))
    self.assertLess(r[0][front]*p[front],0)
    for i in (0,1):self.assertAlmostEqual(size[i]/2-abs(p[i]),.01)
 def test_observed_leading_corner_has_shorter_margin(self):
  q=(0,0,math.sin(-.161/2),math.cos(-.161/2));size=(.1344,.0864,.045)
  leading=top_corner_local(q,size);trailing=top_trailing_corner_local(q,size,-1)
  self.assertLess(forward_edge_distance(leading,q,size,-1),.011)
  self.assertGreater(forward_edge_distance(trailing,q,size,-1),.07)
 def test_front_point_preserves_edge_and_forward_margins_across_yaw(self):
  for yaw in (-2.7,-1.6,-.16,0.,.11,1.4,2.8):
   q=(0,0,math.sin(yaw/2),math.cos(yaw/2));size=(.1344,.0864,.045)
   for direction in (-1,1):
    p=top_front_contact_local(q,size,direction)
    self.assertGreaterEqual(forward_edge_distance(p,q,size,direction),.025-1e-12)
    for i in (0,1):self.assertGreaterEqual(size[i]/2-abs(p[i]),.01-1e-12)
 def test_forward_point_avoids_full_trailing_reach_penalty(self):
  yaw=-.161;q=(0,0,math.sin(yaw/2),math.cos(yaw/2));size=(.1344,.0864,.045);r=rotation_xyzw(q)
  a=top_corner_local(q,size);b=top_front_contact_local(q,size,-1);c=top_trailing_corner_local(q,size,-1)
  x=lambda p:sum(r[0][i]*p[i] for i in (0,1))
  self.assertGreater(x(b),x(a));self.assertLess(x(b)-x(a),.003);self.assertGreater(x(c)-x(a),.01)
  with self.assertRaises(ValueError):top_front_contact_local(q,size,-1,1.)
 def test_rear_shift_preserves_real_edge_and_forward_margins(self):
  from simfoundry.data.top_push_contact_geometry import shift_top_contact_rearward
  for yaw in [-2.8,-1.6,-.4,0.,.4,1.6,2.8]:
   q=(0,0,math.sin(yaw/2),math.cos(yaw/2));r=rotation_xyzw(q)
   for size in [(.135,.1276,.04),(.1344,.0864,.045)]:
    for direction in [-1,1]:
     start=top_front_contact_local(q,size,direction,.04)
     for shift in [0.,.01,.02,.03]:
      end=shift_top_contact_rearward(start,q,size,direction,.04,shift)
      dx=sum(r[0][j]*(end[j]-start[j]) for j in (0,1))
      self.assertGreaterEqual(dx,-1e-10);self.assertLessEqual(dx,shift+1e-10)
      self.assertGreaterEqual(forward_edge_distance(end,q,size,direction),.04-1e-10)
      for j in (0,1):self.assertGreaterEqual(size[j]/2-abs(end[j]),.01-1e-10)
 def test_invalid_arguments_and_outside_edge(self):
  for d in (0,2,float('nan')):
   with self.assertRaises(ValueError):top_trailing_corner_local((0,0,0,1),(.1,.1,.04),d)
  self.assertLess(forward_edge_distance((0,.06,0),(0,0,0,1),(.1,.1,.04),1),0)
  with self.assertRaises(ValueError):top_trailing_corner_local((0,0,0,1),(.01,.1,.04),1)

if __name__=='__main__':unittest.main()
