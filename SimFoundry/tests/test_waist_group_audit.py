import unittest
from copy import deepcopy
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts


class CompleteSwapTests(unittest.TestCase):
    def setUp(self):
        self.layouts = [dict(layout_id=1, geometry_group='g', assignment='normal',
            planned_split='train', seed=17, box_xyz=[.43,.15,.7725],
            mailer_xyz=[.46,-.15,.77], box_yaw=.12, mailer_yaw=-.08),
            dict(layout_id=2, geometry_group='g', assignment='swapped',
            planned_split='train', seed=17, box_xyz=[.46,-.15,.7725],
            mailer_xyz=[.43,.15,.77], box_yaw=-.08, mailer_yaw=.12)]

    def test_complete_counterfactual_preserves_slots_not_category_height(self):
        self.assertEqual(validate_complete_swap_layouts(self.layouts), {'g':[1,2]})

    def test_missing_duplicate_or_changed_slot_rejected(self):
        variants = [self.layouts[:1], self.layouts+[self.layouts[0]]]
        for key,value in [('box_xyz',[.49,-.15,.7725]), ('box_yaw',.12),
                          ('seed',18), ('planned_split','validation')]:
            rows=deepcopy(self.layouts);rows[1][key]=value;variants.append(rows)
        for rows in variants:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                validate_complete_swap_layouts(rows)

    def test_heldout_and_nonfinite_geometry_rejected(self):
        for key,value in [('planned_split','test'),('box_yaw',float('nan')),
                          ('mailer_xyz',[float('inf'),0.,.77])]:
            rows=deepcopy(self.layouts);rows[0][key]=value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_complete_swap_layouts(rows)
