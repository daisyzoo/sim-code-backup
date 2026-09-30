import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'scripts/prepare_paired_sorting_lerobot.py'
spec=importlib.util.spec_from_file_location('converter_wait_geometry_test',p);converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)
class ConverterWaitGeometryTests(unittest.TestCase):
 def records(self):
  rows=[]
  for i,split in ((81000,'train'),(81001,'train'),(81002,'validation'),(81003,'validation')):
   layout=dict(geometry_group='train_group' if split=='train' else 'val_group',assignment='normal' if i%2==0 else 'swapped')
   for task in ('push_box_to_bin','nudge_mailer_to_bin'):
    rows.append(dict(layout_id=i,task_id=task,planned_split=split,**converter.record_geometry_metadata(task,layout)))
  for i,split in ((82000,'train'),(82001,'validation')):
   rows.append(dict(layout_id=i,task_id='wait_no_package',planned_split=split,**converter.record_geometry_metadata('wait_no_package',dict(geometry_group='wait_'+split,assignment='normal'))))
  return rows
 def test_wait_metadata_is_preserved_separately(self):
  self.assertEqual(converter.record_geometry_metadata('wait_no_package',dict(geometry_group='wait_g',assignment='normal')),dict(wait_geometry_group='wait_g',wait_assignment='normal'))
  self.assertEqual(converter.record_geometry_metadata('wait_no_package',{}),{})
 def test_push_metadata_is_unchanged(self):
  layout=dict(geometry_group='g',assignment='swapped')
  self.assertEqual(converter.record_geometry_metadata('push_box_to_bin',layout),layout)
 def test_complete_swaps_and_waits_can_be_split(self):
  rows=self.records();split=converter.make_split(rows,{81002,81003,82001})
  for key in ('train','validation'):
   self.assertEqual({rows[i]['task_id'] for i in split[key]}, {'push_box_to_bin','nudge_mailer_to_bin','wait_no_package'})
  self.assertEqual(split['geometry_groups'],['train_group','val_group'])
 def test_partial_push_swap_still_rejected(self):
  rows=[r for r in self.records() if r['layout_id']!=81001]
  with self.assertRaisesRegex(ValueError,'both category assignments'):converter.make_split(rows,{81002,81003,82001})
 def test_cross_split_category_swap_still_rejected(self):
  with self.assertRaisesRegex(ValueError,'leaked across'):converter.make_split(self.records(),{81001,81002,81003,82001})
 def test_wait_preassigned_split_still_enforced(self):
  with self.assertRaisesRegex(ValueError,'preassigned'):converter.make_split(self.records(),{81002,81003,82000,82001})
if __name__=='__main__':unittest.main()
