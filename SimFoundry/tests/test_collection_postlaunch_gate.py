import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_collection_quality import check

class PostLaunchTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.r=Path(self.tmp.name)
  (self.r/'STATUS.json').write_text(json.dumps({'status':'numeric_pass_visual_review_pending'}))
  self.m=[{'episodes':[{'passed':True},{'passed':True}],'pair':{'passed':True}}]
  self.save()
  for i in range(2):
   d=self.r/f'layout_{i}_task';d.mkdir();(d/'quality.json').write_text('{"passed":true}');(d/'raw.npz').write_bytes(b'fixture')
 def save(self):(self.r/'manifest.json').write_text(json.dumps(self.m))
 def test_accept_complete_numeric_only(self):self.assertFalse(check(self.r,2)['training_ready'])
 def test_reject_swallowed_runtime_or_quality_error(self):
  (self.r/'STATUS.json').write_text('{"status":"blocked_quality_or_runtime"}')
  with self.assertRaises(ValueError):check(self.r,2)
 def test_reject_failed_pair_or_episode(self):
  self.m[0]['pair']['passed']=False;self.save()
  with self.assertRaises(ValueError):check(self.r,2)
  self.m[0]['pair']['passed']=True;self.m[0]['episodes'][0]['passed']=False;self.save()
  with self.assertRaises(ValueError):check(self.r,2)
 def test_reject_missing_raw_and_coverage(self):
  with self.assertRaises(ValueError):check(self.r,3)
  (self.r/'layout_0_task/raw.npz').unlink()
  with self.assertRaises(ValueError):check(self.r,2)
if __name__=='__main__':unittest.main()
