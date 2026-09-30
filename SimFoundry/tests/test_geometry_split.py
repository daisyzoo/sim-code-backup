import unittest
from simfoundry.data.diverse_layouts import validate_geometry_split
class SplitTests(unittest.TestCase):
 def rows(self):return [dict(geometry_group='g',assignment=a,layout_id=lid,task_id=t) for a,lid in [('normal',1),('swapped',2)] for t in ['push_box_to_bin','nudge_mailer_to_bin']]
 def test_complete_group(self):self.assertEqual(validate_geometry_split(self.rows(),{1,2}),['g'])
 def test_legacy_unchanged(self):self.assertEqual(validate_geometry_split([dict(layout_id=1)],{1}),[])
 def test_swap_leak_rejected(self):
  with self.assertRaises(ValueError):validate_geometry_split(self.rows(),{1})
 def test_missing_failed_assignment_rejected(self):
  with self.assertRaises(ValueError):validate_geometry_split(self.rows()[:2],set())
 def test_duplicate_task_rejected(self):
  r=self.rows();r[1]['task_id']=r[0]['task_id']
  with self.assertRaises(ValueError):validate_geometry_split(r,set())
if __name__=='__main__':unittest.main()
