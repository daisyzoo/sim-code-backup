import unittest,numpy as np
from phase_sampling_candidate import prepare_strata,draw_queries
class PhaseSamplingTests(unittest.TestCase):
 def fixture(self,length=1200):
  es=[];fs=[];ps=[];records={};eid=0
  for task in ['push_box_to_bin','nudge_mailer_to_bin','wait_no_package']:
   for group in ['g1','g2']:
    for assignment in range(2):
     n=70 if task=='wait_no_package' else length
     es.extend([eid]*n);fs.extend(range(n));ps.extend(['wait']*n if task=='wait_no_package' else ['start']*3+['active']*77+['terminal']*(n-80))
     records[eid]=dict(task_id=task,geometry_group=group,planned_split='train');eid+=1
  return np.array(es),np.array(fs),np.array(ps),records,list(records),[999]
 def quota(self,strata):
  # Synthetic test budgets only, never adopted as training policy.
  return {k:155 if k[1]=='wait' else {'start':99,'active':200,'terminal':77}[k[1]] for k in strata}
 def test_quota_geometry_and_episode_balance(self):
  data=self.fixture();s,n=prepare_strata(*data);q=self.quota(s);idx,report=draw_queries(s,q,seed=42,epoch=0)
  self.assertEqual(len(idx),sum(q.values()));self.assertTrue(((idx>=0)&(idx<n)).all())
  for (task,phase),count in q.items():
   rows=[r for r in report if r['task']==task and r['phase']==phase]
   self.assertEqual(sum(r['queries'] for r in rows),count)
   g=[sum(r['queries'] for r in rows if r['geometry_group']==name) for name in ['g1','g2']];self.assertLessEqual(abs(g[0]-g[1]),1)
   for name in ['g1','g2']:
    values=[r['queries'] for r in rows if r['geometry_group']==name];self.assertLessEqual(max(values)-min(values),1)
 def test_long_release_does_not_dilute_other_exposure(self):
  reports=[]
  for n in [160,1200]:
   s,_=prepare_strata(*self.fixture(n));_,rows=draw_queries(s,self.quota(s),seed=42,epoch=0)
   reports.append([{k:v for k,v in r.items() if k!='available_frames'} for r in rows])
  self.assertEqual(*reports)
 def test_reproducible_seed_epoch_and_epoch_varies(self):
  s,_=prepare_strata(*self.fixture());q=self.quota(s)
  a,_=draw_queries(s,q,seed=42,epoch=0);b,_=draw_queries(s,q,seed=42,epoch=0);c,_=draw_queries(s,q,seed=42,epoch=1)
  np.testing.assert_array_equal(a,b);self.assertFalse(np.array_equal(a,c))
 def test_validation_and_test_rows_rejected(self):
  for split in ['validation','test','development']:
   d=list(self.fixture());d[3][0]['planned_split']=split
   with self.assertRaises(ValueError):prepare_strata(*d)
  d=list(self.fixture());d[5]=[0]
  with self.assertRaises(ValueError):prepare_strata(*d)
 def test_missing_phase_or_frame_rejected(self):
  d=list(self.fixture());d[2][0:3]='active'
  with self.assertRaises(ValueError):prepare_strata(*d)
  d=list(self.fixture());d[1][1]=0
  with self.assertRaises(ValueError):prepare_strata(*d)
 def test_missing_zero_or_noninteger_quota_rejected(self):
  s,_=prepare_strata(*self.fixture());q=self.quota(s)
  for value in [0,-1,1.5,True]:
   bad=dict(q);bad[next(iter(q))]=value
   with self.assertRaises(ValueError):draw_queries(s,bad,seed=42,epoch=0)
  del q[next(iter(q))]
  with self.assertRaises(ValueError):draw_queries(s,q,seed=42,epoch=0)
if __name__=='__main__':unittest.main()
