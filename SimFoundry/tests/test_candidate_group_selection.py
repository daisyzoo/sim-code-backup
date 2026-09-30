import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from select_spatial_candidate_groups import choose_groups

class SelectionTests(unittest.TestCase):
 def rows(self):
  r=[]
  for i,s in enumerate(['negative','center','positive']*4):
   r.append({'group':f'g{i}','partition':'train','stratum':s,'status':'approved_group'})
  r += [{'group':'v0','partition':'validation','stratum':'center','status':'approved_group'}, {'group':'v1','partition':'validation','stratum':'center','status':'approved_group'}]
  return r
 def test_registered_order_and_whole_group_quotas(self):
  picked=choose_groups(self.rows());self.assertEqual([r['group'] for r in picked],['g0','g3','g1','g4','g2','g5','v0'])
 def test_failed_or_unreviewed_group_never_selected(self):
  rows=self.rows();rows[0]['status']='rejected_numeric';rows[1]['status']='numeric_pass_visual_pending';names=[r['group'] for r in choose_groups(rows)]
  self.assertNotIn('g0',names);self.assertNotIn('g1',names);self.assertIn('g6',names);self.assertIn('g7',names)
 def test_shortfall_does_not_borrow_from_other_stratum(self):
  rows=self.rows()
  for r in rows:
   if r['stratum']=='negative':r['status']='rejected_numeric'
  with self.assertRaises(ValueError):choose_groups(rows)
 def test_validation_never_replaced_with_training(self):
  rows=[r for r in self.rows() if r['partition']=='train']
  with self.assertRaises(ValueError):choose_groups(rows)
if __name__=='__main__':unittest.main()
