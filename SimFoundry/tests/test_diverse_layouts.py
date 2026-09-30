import json,tempfile,unittest
from pathlib import Path
from simfoundry.data.diverse_layouts import load_diagnostic_layout
class LayoutTests(unittest.TestCase):
 def check(self,d):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'layout.json';p.write_text(json.dumps(d));return load_diagnostic_layout(p,50000)
 def valid(self):return dict(layout_id=50000,seed=1,geometry_group='g',assignment='swapped',box_xyz=[.4,.14,.7725],mailer_xyz=[.58,-.14,.77])
 def test_swapped_preserved(self):self.assertEqual(self.check(self.valid()),self.valid())
 def test_overlap_rejected(self):
  d=self.valid();d['mailer_xyz']=[.4,.14,.77]
  with self.assertRaises(ValueError):self.check(d)
 def test_invalid_height_and_id(self):
  for key,value in [('layout_id',50001),('box_xyz',[.4,.14,.9]),('box_xyz',[float('nan'),.14,.7725]),('geometry_group',None)]:
   d=self.valid();d[key]=value
   with self.assertRaises(ValueError):self.check(d)
 def test_rotated_footprint_clearance(self):
  import math
  d=self.valid();d.update(box_xyz=[.36,0,.7725],mailer_xyz=[.505,0,.77])
  with self.assertRaises(ValueError):self.check(d)
  d['box_yaw']=math.pi/2
  self.assertEqual(self.check(d),d)
  d['mailer_xyz'][0]=.49
  with self.assertRaises(ValueError):self.check(d)
 def test_nonfinite_yaw_and_overhang(self):
  for yaw in [float('nan'),float('inf'),4.]:
   d=self.valid();d['box_yaw']=yaw
   with self.assertRaises(ValueError):self.check(d)
  d=self.valid();d.update(box_xyz=[.36,.14,.7725],box_yaw=.7)
  with self.assertRaises(ValueError):self.check(d)
 def test_distance_rule_preserves_near_and_is_category_independent(self):
  from simfoundry.data.diverse_layouts import contact_offset_for_distance as f
  for x in [.36,.362,.44,.479]:self.assertEqual(f(x,-.13,-.11),-.13)
  for x in [.48,.505,.51]:self.assertEqual(f(x,-.13,-.11),-.11)
  for x in [.36,.51,.62]:self.assertEqual(f(x,-.13),-.13)
if __name__=='__main__':unittest.main()
