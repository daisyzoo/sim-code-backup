import unittest
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin

class LoadedMarginTests(unittest.TestCase):
 def packet(self,swap=False):
  rows=[]
  for y,f in ((.03,1.),(.04,3.)):
   shapes=['/World/left_wrist_roll_rubber_hand','/World/mailer/geometry/mesh'];force=[0,0,-f]
   if swap:shapes.reverse();force=[0,0,f]
   rows.append(dict(shapes=shapes,position_world=[.6,y,.79],force_world_N=force))
  return dict(parcel_contacts=rows)
 def read(self,p):return loaded_forward_margin(p,'left','mailer',(.6,0,.77),(0,0,0,1),(.135,.1276,.04),1)
 def test_actual_force_weighted_contact_and_slot_sign(self):
  a=self.read(self.packet());b=self.read(self.packet(True));self.assertEqual(a,b);self.assertTrue(a['valid']);self.assertAlmostEqual(a['normal_load_n'],4.);self.assertAlmostEqual(a['weighted_forward_edge_distance_m'],.0638-.0375);self.assertAlmostEqual(a['min_sample_forward_edge_distance_m'],.0638-.04)
 def test_absent_or_other_hand_contacts_do_not_invent_load(self):
  self.assertFalse(self.read(None)['valid']);p=self.packet()
  for r in p['parcel_contacts']:r['shapes'][0]='/World/right_wrist_roll_rubber_hand'
  self.assertFalse(self.read(p)['valid'])
 def test_net_force_is_force_on_target_in_world_axes(self):
  p=self.packet();p['parcel_contacts'][0]['force_world_N']=[1.,2.,-1.];p['parcel_contacts'][1]['force_world_N']=[-.25,-.5,-3.]
  self.assertEqual(self.read(p)['force_on_target_world_n'],[.75,1.5,-4.])
 def test_invalid_force_rejected(self):
  p=self.packet();p['parcel_contacts'][0]['force_world_N'][2]=float('nan')
  with self.assertRaises(ValueError):self.read(p)
 def test_zero_and_wrong_force_sign_filtered(self):
  p=self.packet()
  for r in p['parcel_contacts']:r['force_world_N']=[0,0,1.]
  self.assertFalse(self.read(p)['valid'])

if __name__=='__main__':unittest.main()
