import importlib.util,unittest,tempfile,json,hashlib
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('converter_query_test',Path(__file__).resolve().parents[1]/'scripts/prepare_paired_sorting_lerobot.py');converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)
class ConverterPhaseTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);q=np.zeros((120,23));a=q.copy();q[10:50,12]=np.linspace(0,.1,40);q[50:,12]=.1;a[:]=q
  self.raw=self.root/'raw.npz';np.savez(self.raw,q=q,action=a);self.control=self.root/'expert_control.json';self.control.write_text(json.dumps([dict(step=i,mode='top_push' if i<50 else 'top_release') for i in range(120)]))
  self.record=dict(path=self.raw,hash=hashlib.sha256(self.raw.read_bytes()).hexdigest(),task_id='push_box_to_bin',motion_protocol='waist_yaw_enabled_v1',waist_pilot_contract_sha256='fixture_not_real_admission')
 def test_binding_and_raw_unchanged(self):
  before=self.raw.read_bytes();r=converter.build_query_phase_records([self.record]);row=r['records'][0];self.assertEqual(row['episode_index'],0);self.assertEqual(sum(row['counts'].values()),120);self.assertEqual(row['raw_sha256'],self.record['hash']);self.assertEqual(row['expert_control_sha256'],hashlib.sha256(self.control.read_bytes()).hexdigest());self.assertEqual(self.raw.read_bytes(),before)
 def test_diagnostic_or_unbound_records_rejected(self):
  for change in [dict(motion_protocol='waist_locked_v1'),dict(waist_pilot_contract_sha256=None)]:
   with self.assertRaises(ValueError):converter.build_query_phase_records([dict(self.record,**change)])
 def test_changed_raw_or_missing_log_rejected(self):
  with self.assertRaises(ValueError):converter.build_query_phase_records([dict(self.record,hash='0'*64)])
  self.control.unlink()
  with self.assertRaises(OSError):converter.build_query_phase_records([self.record])
if __name__=='__main__':unittest.main()
