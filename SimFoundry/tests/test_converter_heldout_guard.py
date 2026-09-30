"""Regression: heldout geometry cannot become training data via generic pilot path."""
import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('paired_converter',Path(__file__).resolve().parents[1]/'scripts/prepare_paired_sorting_lerobot.py');converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)

class HeldoutAdmissionTests(unittest.TestCase):
 def source(self,root):
  episodes={}
  for name in ['layout_900000_push_box_to_bin','layout_900000_nudge_mailer_to_bin']:
   p=root/name;p.mkdir();(p/'raw.npz').write_bytes(b'unit-test-stub-not-physical-data');episodes[f'{name}/raw.npz']=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest()
  (root/'STATUS.json').write_text(json.dumps({'status':'numeric_pass_visual_review_pending'}))
  (root/'review.json').write_text(json.dumps({'approved':True,'method':'unit-test-stub','episodes':episodes}))
  (root/'provenance.json').write_text(json.dumps({'args':{'layouts':1,'wait_episodes':0}}))
 def test_generic_pilot_test_layout_rejected_before_numeric_audit(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.source(root)
   ep=SimpleNamespace(collect_meta={'collection_role':'pilot','assist_frames':0,'layout':{'planned_split':'test'}})
   with patch.object(converter,'load_episode',return_value=ep),patch.object(converter,'audit_rollout',side_effect=AssertionError('must reject before audit')):
    with self.assertRaisesRegex(ValueError,'preassigned test geometry'):converter.checked_sources([root])
 def test_train_marker_does_not_admit_diagnostic(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.source(root)
   ep=SimpleNamespace(collect_meta={'collection_role':'diagnostic','assist_frames':0,'layout':{'planned_split':'train'}})
   with patch.object(converter,'load_episode',return_value=ep):
    with self.assertRaisesRegex(ValueError,'diagnostic or assisted'):converter.checked_sources([root])
 def test_preassigned_train_cannot_move_to_validation(self):
  records=[dict(layout_id=i,task_id=t,planned_split='train') for i in [1,2] for t in converter.PAIRED_SORTING_PROMPTS]
  with self.assertRaisesRegex(ValueError,'preassigned pilot split'):converter.make_split(records,{2})

if __name__=='__main__':unittest.main()
