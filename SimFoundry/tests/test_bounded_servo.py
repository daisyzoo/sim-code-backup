"""Exercise controller lead bounds against a deliberately stalled mock plant."""
import ast,dataclasses,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch

def controller():
 p=Path(__file__).resolve().parents[1]/'simfoundry/data/sorting_cartesian_expert.py'
 tree=ast.parse(p.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.Assign,ast.ClassDef,ast.FunctionDef))]
 env={'dataclass':dataclasses.dataclass,'np':np,'torch':torch,'TABLE_TOP_Z':.75,'PALM_OFFSET':(.2,0,.007),'quat_apply':lambda q,v:v,'G1_23DOF_JOINT_NAMES':[str(i) if i!=12 else 'torso_joint' for i in range(23)]}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),env);return env
class ServoTests(unittest.TestCase):
 def simulate(self,memory):
  mod=controller();jac=torch.zeros(1,1,6,23);jac[0,0,0,0]=1;jac[0,0,1,1]=1;jac[0,0,2,2]=1
  data=SimpleNamespace(body_pos_w=SimpleNamespace(torch=torch.tensor([[[.30,.10,.88]]])),body_quat_w=SimpleNamespace(torch=torch.tensor([[[1.,0.,0.,0.]]])),body_link_jacobian_w=SimpleNamespace(torch=jac),joint_pos=SimpleNamespace(torch=torch.zeros(1,23)))
  robot=SimpleNamespace(data=data,num_base_dofs=0)
  state=mod['CartesianSweepState']('left',.52,.17,mode='cross',joint_ids=(0,1,2,3,4),jacobian_body_idx=0,staging_palm_z=.92,contact_side_offset=-.07,bounded_servo_memory=memory)
  values=[]
  for step in range(20):
   action=np.zeros(23);mod['cartesian_sweep_palm'](robot,{'left':0,'right':0},action,state=state,step=step,default_q=np.zeros(23));values.append(action.copy())
   self.assertEqual(action[12],0)
  return np.array(values)
 def test_accumulation_bounded_under_stall(self):
  a=self.simulate(True);self.assertLessEqual(abs(a[:,13:18]).max(),.100001);self.assertGreater(np.linalg.norm(a[-1,13:18]),np.linalg.norm(a[0,13:18]));self.assertLessEqual(np.abs(np.diff(a[:,13:18],axis=0)).max(),.055001)
 def test_default_has_no_accumulation(self):
  a=self.simulate(False);np.testing.assert_array_equal(a[0],a[-1])
if __name__=='__main__':unittest.main()
