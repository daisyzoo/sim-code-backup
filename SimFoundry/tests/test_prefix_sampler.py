import importlib.util
from pathlib import Path
import unittest
from collections import Counter
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
MODULE=ROOT/'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src/lerobot/utils/paired_prefix_sampler.py'
spec=importlib.util.spec_from_file_location('paired_prefix_sampler_test_module',MODULE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PrefixSamplerTest(unittest.TestCase):
    def setUp(self):
        self.eps=np.array([0]*6+[2]*4);self.frames=np.array(list(range(6))+list(range(4)))
        self.records=[{'task_id':'push_box_to_bin'},{'task_id':'nudge_mailer_to_bin'},{'task_id':'wait_no_package'}]
    def weights(self):return m.prefix_weights(self.eps,self.frames,self.records,[0,2],[1],2,4)[0]
    def test_preserves_episode_mass_and_wait_weights(self):
        w=self.weights();self.assertAlmostEqual(w[:6].sum(),6);np.testing.assert_array_equal(w[6:],np.ones(4));self.assertGreater(w[0],w[2])
    def test_exact_episode_counts_wait_coverage_and_reproducibility(self):
        a=list(m.EpisodePrefixSampler(self.eps,self.weights(),42));b=list(m.EpisodePrefixSampler(self.eps,self.weights(),42));self.assertEqual(a,b)
        self.assertEqual(Counter(self.eps[a]),Counter({0:6,2:4}));self.assertEqual(sorted(i for i in a if i>=6),list(range(6,10)))
    def test_weighting_changes_prefix_exposure_without_changing_task_counts(self):
        sampler=m.EpisodePrefixSampler(self.eps,self.weights(),42);prefix=0
        for _ in range(100):
            values=list(sampler);self.assertEqual(Counter(self.eps[values]),Counter({0:6,2:4}));prefix+=sum(i<2 for i in values)
        self.assertGreater(prefix,300)
    def test_uniform_control_retains_all_frames_once(self):
        values=list(m.EpisodePrefixSampler(self.eps,np.ones(10),42));self.assertEqual(sorted(values),list(range(10)))
    def test_rejects_fractional_prefix_and_empty_sampler(self):
        for invalid in [2.5,True,0,21]:
            with self.assertRaises(ValueError):m.prefix_weights(self.eps,self.frames,self.records,[0,2],[1],invalid,4)
        with self.assertRaises(ValueError):m.EpisodePrefixSampler([],[],42)
    def test_rejects_validation_leak_and_incomplete_frame_table(self):
        with self.assertRaises(ValueError):m.prefix_weights(self.eps,self.frames,self.records,[0,2],[2],2,4)
        broken=self.frames.copy();broken[1]=0
        with self.assertRaises(ValueError):m.prefix_weights(self.eps,broken,self.records,[0,2],[1],2,4)

if __name__=='__main__':unittest.main()
