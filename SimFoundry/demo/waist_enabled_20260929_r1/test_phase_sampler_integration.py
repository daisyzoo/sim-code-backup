"""Synthetic metadata/dataloader integration; no real data approval or model."""
from pathlib import Path
import sys,json,hashlib,tempfile,unittest,importlib.util
import numpy as np,torch
root=Path(__file__).resolve().parent;repo=root.parents[1];sys.path.insert(0,str(repo))
from simfoundry.data.query_phases import episode_query_phases
module_path=repo.parent/'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src/lerobot/utils/paired_phase_sampler.py'
spec=importlib.util.spec_from_file_location('actual_phase_sampler',module_path);sampler_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(sampler_module)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Dataset(torch.utils.data.Dataset):
 def __init__(self,root):
  self.root=root;self.hf_dataset=dict(episode_index=np.repeat([0,1,2],[160,160,70]),frame_index=np.r_[np.arange(160),np.arange(160),np.arange(70)])
 def __len__(self):return len(self.hf_dataset['episode_index'])
 def __getitem__(self,index):
  e=int(self.hf_dataset['episode_index'][index]);f=int(self.hf_dataset['frame_index'][index]);length=70 if e==2 else 160
  return dict(index=index,episode=e,frame=f,action_frame_indices=np.minimum(f+np.arange(10),length-1))
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);meta=self.root/'meta';meta.mkdir();records=[];phases=[]
  for i,task in enumerate(['push_box_to_bin','nudge_mailer_to_bin','wait_no_package']*2):
   n=70 if task=='wait_no_package' else 160;q=np.zeros((n,23));a=q.copy();control=[dict(step=j,mode='top_push' if j<70 else 'top_release') for j in range(n)]
   if task!='wait_no_package':q[3:70,12]=np.linspace(0,.1,67);q[70:,12]=.1;a[:]=q
   r=dict(task_id=task,hash=str(i)*64,motion_protocol='waist_yaw_enabled_v1',waist_pilot_contract_sha256='synthetic_fixture',planned_split='train' if i<3 else 'validation')
   r['wait_geometry_group' if task=='wait_no_package' else 'geometry_group']='g1' if i<3 else 'g2';records.append(r)
   phases.append(dict(episode_index=i,task_id=task,raw_sha256=r['hash'],**episode_query_phases(task,q,a,control)))
  data={'paired_provenance.json':dict(records=records),'train_validation_split.json':dict(train=[0,1,2],validation=[3,4,5]),'train_only_stats.json':dict(episode_indices=[0,1,2]),'episode_query_phases.json':dict(records=phases,labeler_source_sha256=sha(repo/'simfoundry/data/query_phases.py'))}
  for n,v in data.items():(meta/n).write_text(json.dumps(v))
  quotas=[dict(task_id=task,phase=phase,queries=count) for task in ['push_box_to_bin','nudge_mailer_to_bin'] for phase,count in [('start',30),('active',90),('terminal',30)]]+[dict(task_id='wait_no_package',phase='wait',queries=60)]
  self.policy=dict(approved_for_training=True,strategy='task_phase_geometry_balanced',dataset_root=str(self.root),seed=42,sampler_source_sha256=sha(module_path),metadata_sha256={n:sha(meta/n) for n in data},phase_labeler_source_sha256=data['episode_query_phases.json']['labeler_source_sha256'],phase_definition=phases[0]['definition'],expected_training_frames=390,quotas=quotas,queries_per_epoch=360)
  self.path=self.root/'policy.json';self.path.write_text(json.dumps(self.policy));self.dataset=Dataset(self.root)
 def build(self):return sampler_module.build_phase_sampler(self.dataset,self.path,42)
 def policy_change(self,**kw):self.policy.update(kw);self.path.write_text(json.dumps(self.policy))
 def test_dataloader_query_counts_and_chunks_stay_with_original_episode(self):
  sampler,report=self.build();self.assertEqual(report['queries_per_epoch'],360);counts={};seen=0
  for batch in torch.utils.data.DataLoader(self.dataset,batch_size=17,sampler=sampler):
   for e,f,chunk in zip(batch['episode'].tolist(),batch['frame'].tolist(),batch['action_frame_indices'].numpy()):
    counts[e]=counts.get(e,0)+1;seen+=1;np.testing.assert_array_equal(chunk,np.minimum(f+np.arange(10),(70 if e==2 else 160)-1))
  self.assertEqual(seen,360);self.assertEqual(counts,{0:150,1:150,2:60});self.assertEqual(report['validation_episodes_sampled'],[])
 def test_epoch_reproducibility_and_variation(self):
  s,_=self.build();first=list(s);second=list(s);self.assertNotEqual(first,second);s.set_epoch(0);self.assertEqual(first,list(s));other,_=self.build();self.assertEqual(first,list(other))
 def test_bound_metadata_change_rejected(self):
  (self.root/'meta/train_only_stats.json').write_text('{}')
  with self.assertRaisesRegex(ValueError,'metadata changed'):self.build()
 def test_source_or_unapproved_policy_rejected(self):
  self.policy_change(approved_for_training=False)
  with self.assertRaises(ValueError):self.build()
  self.policy_change(approved_for_training=True,sampler_source_sha256='0'*64)
  with self.assertRaisesRegex(ValueError,'source changed'):self.build()
 def test_validation_row_or_missing_frame_rejected(self):
  self.dataset.hf_dataset['episode_index'][0]=3
  with self.assertRaisesRegex(ValueError,'train-only'):self.build()
  self.dataset.hf_dataset['episode_index'][0]=0;self.dataset.hf_dataset['frame_index'][0]=1
  with self.assertRaisesRegex(ValueError,'alignment'):self.build()
 def test_duplicate_quota_and_rebound_bad_raw_binding_rejected(self):
  self.policy['quotas'].append(dict(self.policy['quotas'][0]));self.policy_change()
  with self.assertRaisesRegex(ValueError,'Duplicate'):self.build()
  self.policy['quotas'].pop();p=self.root/'meta/episode_query_phases.json';d=json.loads(p.read_text());d['records'][0]['raw_sha256']='f'*64;p.write_text(json.dumps(d));self.policy['metadata_sha256'][p.name]=sha(p);self.policy_change()
  with self.assertRaisesRegex(ValueError,'Phase/raw'):self.build()
if __name__=='__main__':
 # Run original quota/balance tests against this actual production module too.
 sys.modules['phase_sampling_candidate']=sampler_module
 import test_phase_sampling_candidate
 suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(test_phase_sampling_candidate),unittest.defaultTestLoader.loadTestsFromTestCase(IntegrationTests)])
 r=unittest.TextTestRunner().run(suite);raise SystemExit(0 if r.wasSuccessful() else 1)
