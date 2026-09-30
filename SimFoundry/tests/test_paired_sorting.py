from types import SimpleNamespace
import unittest
import importlib.util
import json
from pathlib import Path
import tempfile
import numpy as np
from simfoundry.data.paired_sorting import audit_rollout, audit_pair, sample_layout
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS

class PairedQualityTests(unittest.TestCase):
    def baseline(self):
        q = np.zeros((70, 23), dtype=np.float32)
        trace = {k: np.tile(p, (70, 1)) for k, p in {
            'box': (.45, -.14, .7725), 'mailer': (.45, .14, .77),
            'palm_left': (.10, .20, .60), 'palm_right': (.10, -.20, .60),
        }.items()}
        return q, q.copy(), trace

    def test_hanging_zero_pose_is_not_table_penetration(self):
        q, a, t = self.baseline()
        self.assertTrue(audit_rollout('push_box_to_bin', q, a, t, idle=True)['passed'])

    def test_idle_self_drift_is_rejected(self):
        q, a, t = self.baseline()
        t['mailer'][:, 0] += np.linspace(0, .04, 70)
        self.assertFalse(audit_rollout('push_box_to_bin', q, a, t, idle=True)['passed'])

    def test_wait_checks_workspace_not_only_y(self):
        q, a, t = self.baseline()
        t['box'][:] = (15., .1, .02)
        t['mailer'][:] = (8., .2, .02)
        self.assertTrue(audit_rollout('wait_no_package', q, a, t)['passed'])
        t['box'][20] = (.45, -.14, .7725)
        self.assertFalse(audit_rollout('wait_no_package', q, a, t)['passed'])

    def test_fake_zero_and_abrupt_actions_rejected(self):
        q, a, t = self.baseline()
        q[0, 13] = .1
        a[10:, 14] = .3
        reasons = audit_rollout('push_box_to_bin', q, a, t, idle=True)['reasons']
        self.assertTrue(any('state is not zero' in x for x in reasons))
        self.assertTrue(any('abrupt' in x for x in reasons))

    def test_pair_requires_same_state_and_correct_text(self):
        eps = [SimpleNamespace(collect_meta={'box_xyz': [0.,0.,0.], 'mailer_xyz': [1.,1.,1.]},
                rgb=np.zeros((1,3,4,4), dtype=np.uint8), q=np.zeros((1,23)),
                task_id=task, instruction=PAIRED_SORTING_PROMPTS[task])
               for task in ('push_box_to_bin', 'nudge_mailer_to_bin')]
        self.assertTrue(audit_pair(*eps)['passed'])
        eps[1].collect_meta['mailer_xyz'][0] += .02
        eps[1].instruction = eps[0].instruction
        self.assertFalse(audit_pair(*eps)['passed'])

    def test_pair_orientation_and_quaternion_sign(self):
        eps = [SimpleNamespace(collect_meta={'box_xyz':[0,0,0], 'mailer_xyz':[1,1,1], 'box_quat_xyzw':[0,0,0,1]},
                rgb=np.zeros((1,3,4,4), dtype=np.uint8), q=np.zeros((1,23)),
                task_id=t, instruction=PAIRED_SORTING_PROMPTS[t]) for t in ('push_box_to_bin','nudge_mailer_to_bin')]
        eps[1].collect_meta['box_quat_xyzw']=[0,0,0,-1]
        self.assertTrue(audit_pair(*eps)['passed'])
        eps[1].collect_meta['box_quat_xyzw']=[0,0,1,0]
        self.assertFalse(audit_pair(*eps)['passed'])
        del eps[1].collect_meta['box_quat_xyzw']
        self.assertFalse(audit_pair(*eps)['passed'])

    def test_layout_is_deterministic_and_objects_are_separate(self):
        for i in range(20):
            a = sample_layout(i)
            self.assertEqual(a, sample_layout(i))
            self.assertGreater(a['mailer_xyz'][1] - a['box_xyz'][1], .24)
        self.assertNotEqual(sample_layout(0), sample_layout(1))


class ConversionGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'scripts/prepare_paired_sorting_lerobot.py'
        spec = importlib.util.spec_from_file_location('paired_converter', path)
        cls.converter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.converter)

    def test_failed_collection_cannot_be_converted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'STATUS.json').write_text(json.dumps({'status': 'blocked_quality_or_runtime'}))
            with self.assertRaisesRegex(ValueError, 'numeric gates'):
                self.converter.checked_sources([root])

    def test_validation_keeps_layout_pairs_together(self):
        records = [{'layout_id': k, 'task_id': t}
                   for k in (0, 1)
                   for t in ('push_box_to_bin', 'nudge_mailer_to_bin')]
        records += [{'layout_id': k, 'task_id': 'wait_no_package'} for k in (10000, 10001)]
        split = self.converter.make_split(records, {1, 10001})
        self.assertEqual(split['train'], [0, 1, 4])
        self.assertEqual(split['validation'], [2, 3, 5])
        with self.assertRaisesRegex(ValueError, 'wait'):
            self.converter.make_split(records, {1})

    def test_preassigned_pilot_split_cannot_be_changed(self):
        records = []
        for group, split in ((0, 'train'), (1, 'validation')):
            for assignment, lid in (('normal', 2*group), ('swapped', 2*group+1)):
                records += [dict(layout_id=lid, task_id=task, geometry_group=f'g{group}',
                                 assignment=assignment, planned_split=split)
                            for task in ('push_box_to_bin', 'nudge_mailer_to_bin')]
        records += [dict(layout_id=10000, task_id='wait_no_package'),
                    dict(layout_id=10001, task_id='wait_no_package')]
        split = self.converter.make_split(records, {2, 3, 10001})
        self.assertEqual(len(split['train']), 5)
        with self.assertRaisesRegex(ValueError, 'preassigned pilot split'):
            self.converter.make_split(records, {0, 1, 10001})
        # Even moving a complete test group together must fail.
        for row in records[:4]:
            row['planned_split'] = 'test'
        with self.assertRaisesRegex(ValueError, 'preassigned pilot split'):
            self.converter.make_split(records, {2, 3, 10001})

if __name__ == '__main__':
    unittest.main()
