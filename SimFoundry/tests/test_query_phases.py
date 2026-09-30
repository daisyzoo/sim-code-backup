import unittest,numpy as np
from simfoundry.data.query_phases import episode_query_phases,expand_query_phases
class QueryPhaseTests(unittest.TestCase):
 def fixture(self):
  q=np.zeros((160,23));a=q.copy();a[30:70,12]=np.linspace(0,.4,40);a[70:,12]=.4;q[30:75,12]=np.linspace(0,.4,45);q[75:,12]=.4
  control=[dict(step=i,mode='top_push' if i<50 else 'top_release') for i in range(160)]
  return q,a,control
 def test_release_withdrawal_is_active_until_settled(self):
  q,a,c=self.fixture();r=episode_query_phases('push_box_to_bin',q,a,c);labels=expand_query_phases(r)
  self.assertEqual(labels[:3],['start']*3);self.assertEqual(labels[50:75],['active']*25);self.assertEqual(r['terminal_start'],75);self.assertEqual(len(labels),160)
 def test_slow_drift_rejected_from_terminal_prefix(self):
  q,a,c=self.fixture();q[:,12]=np.linspace(0,.03,160);a=q.copy();r=episode_query_phases('push_box_to_bin',q,a,c)
  self.assertGreater(r['terminal_start'],100)
 def test_failed_guard_hold_is_not_terminal_release(self):
  q,a,c=self.fixture()
  for row in c:row['mode']='front_guard_lift'
  with self.assertRaises(ValueError):episode_query_phases('nudge_mailer_to_bin',q,a,c)
 def test_wait_remains_wait(self):
  q,a,c=self.fixture();r=episode_query_phases('wait_no_package',q,a,c);self.assertEqual(r['counts'],{'wait':160})
 def test_missing_or_duplicate_control_frame_rejected(self):
  q,a,c=self.fixture()
  with self.assertRaises(ValueError):episode_query_phases('push_box_to_bin',q,a,c[:-1])
  c[30]['step']=29
  with self.assertRaises(ValueError):episode_query_phases('push_box_to_bin',q,a,c)
 def test_bad_runs_and_nan_rejected(self):
  q,a,c=self.fixture();r=episode_query_phases('push_box_to_bin',q,a,c);r['runs'][1]['start']=4
  with self.assertRaises(ValueError):expand_query_phases(r)
  q[2,12]=np.nan
  with self.assertRaises(ValueError):episode_query_phases('push_box_to_bin',q,a,c)
if __name__=='__main__':unittest.main()
