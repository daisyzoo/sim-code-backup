import hashlib,json,tempfile,unittest
from pathlib import Path
from simfoundry.data.spatial_protocol import validate_spatial_contract

class SpatialContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.r=Path(self.tmp.name);proof=self.r/'proof';(proof/'visual_evidence').mkdir(parents=True)
  rows=[]
  for i in range(4):
   p=proof/f'episode_{i}';p.mkdir();raw=p/'raw.npz';raw.write_bytes(f'reviewed-fixture-{i}'.encode());h=hashlib.sha256(raw.read_bytes()).hexdigest();rows.append({'path':str(p),'passed':True,'raw_sha256':h})
  (proof/'visual_evidence/inventory.json').write_text(json.dumps(rows));review=proof/'visual_review.json';review.write_text(json.dumps({'reviewed':True,'raw_sha256':[r['raw_sha256'] for r in rows]}))
  a={'layout_id':60000,'geometry_group':'g','assignment':'normal','seed':1,'box_xyz':[.36,0,.7725],'mailer_xyz':[.505,0,.77]}
  b={**a,'layout_id':60001,'assignment':'swapped','box_xyz':[.505,0,.7725],'mailer_xyz':[.36,0,.77]}
  self.c={'version':1,'approved_for_pilot':True,'expert':{'steps':160,'staging_z':.92,'contact_offset':-.13},'layouts':[a,b],'feasibility':[{'root':str(proof),'visual_review_sha256':hashlib.sha256(review.read_bytes()).hexdigest()}]};self.p=self.r/'contract.json'
 def call(self,**kwargs):
  self.p.write_text(json.dumps(self.c));args=dict(layout_id=60000,steps=160,staging_z=.92,contact_offset=-.13);args.update(kwargs);return validate_spatial_contract(self.p,**args)
 def test_registered_complete_group(self):self.assertEqual(self.call()[0]['layout_id'],60000)
 def test_unreviewed_rejected(self):
  self.c['approved_for_pilot']=False
  with self.assertRaises(ValueError):self.call()
 def test_settings_and_id_mismatch(self):
  for k,v in [('steps',180),('staging_z',1.),('layout_id',60002)]:
   with self.assertRaises(ValueError):self.call(**{k:v})
 def test_partial_or_false_swap_rejected(self):
  b=self.c['layouts'].pop()
  with self.assertRaises(ValueError):self.call()
  self.c['layouts'].append(b);b['mailer_xyz'][0]=.37
  with self.assertRaises(ValueError):self.call()
 def test_modified_evidence_rejected(self):
  (self.r/'proof/episode_1/raw.npz').write_bytes(b'changed')
  with self.assertRaises(ValueError):self.call()
 def test_reused_diagnostic_id_rejected(self):
  (self.r/'proof/layout_60000.json').write_text('{"layout_id":60000}')
  with self.assertRaises(ValueError):self.call()
 def test_distance_setting_must_match_exact_contract(self):
  self.c['expert']['far_contact_offset']=-.11
  with self.assertRaises(ValueError):self.call()
  self.assertEqual(self.call(far_contact_offset=-.11)[0]['layout_id'],60000)
  with self.assertRaises(ValueError):self.call(far_contact_offset=-.12)
if __name__=='__main__':unittest.main()
