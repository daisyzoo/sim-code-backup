"""CPU fixture callback wiring only; no actual Newton scene or CUDA graph."""
from pathlib import Path
from types import SimpleNamespace as NS
import json,hashlib,datetime
import numpy as np
import warp as wp
wp.config.kernel_cache_dir='/tmp/tilt05_substep_cpu_warp_cache';wp.init();assert not wp.get_cuda_devices()
from mujoco_warp._src.types import vec5,ConeType
from substep_contact_runtime_bridge import SubstepContactBridge
W=Path(__file__).resolve().parent
arr=lambda x,t:wp.array(np.asarray(x),dtype=t,device='cpu')
class Manager:
 def __init__(self,graphable):
  self._graph=None;self._use_single_state=True;self._num_substeps=3;self._decimation=8;self._solver_dt=1/360;self.graphable=graphable;self.pre=[];self.post=[]
  self.state=NS(body_q=arr([[0,0,0,0,0,0,1],[1,0,0,0,0,0,1]],wp.transform),body_qd=wp.zeros(2,dtype=wp.spatial_vector,device='cpu'))
  self.model=NS(shape_body=arr([0,1,-1],int),shape_label=['/env/parcel_box/collision','/env/mailer/collision','/table/collision'],body_label=['box','mailer'],body_mass=arr([.2,.1],float),body_com=arr([[.01,0,0],[0,.01,0]],wp.vec3),body_inertia=arr(np.tile(np.eye(3)*.001,(2,1,1)),wp.mat33))
  contact=NS(frame=arr([np.eye(3)],wp.mat33),friction=arr([[.5,.4,.3,.2,.1]],vec5),dim=arr([1],int),efc_address=arr([[0]],int),worldid=arr([0],int),geom=arr([[0,2]],wp.vec2i),pos=arr([[1,2,3]],wp.vec3))
  data=NS(contact=contact,efc=NS(force=arr([[5.]],float)),njmax=1,nacon=arr([1],int),naconmax=1)
  self._solver=NS(use_mujoco_cpu=False,update_data_interval=1,mjw_data=data,mjw_model=NS(opt=NS(cone=ConeType.PYRAMIDAL)),mjc_geom_to_newton_shape=arr([[0,1,2]],int))
 def get_model(self):return self.model
 def get_state_0(self):return self.state
 def _is_all_graphable(self):return self.graphable
 def register_state_force_callback(self,cb):self.pre.append(cb)
 def register_post_step_callback(self,cb):self.post.append(cb)
 def simulate(self):
  for _ in range(1 if self.graphable else 8):
   for _ in range(24 if self.graphable else 3):
    for cb in self.pre:cb(self.state)
   for cb in self.post:cb()
checks=[]
def reject(name,call):
 try:call()
 except ValueError:checks.append(dict(rejected=name))
 else:raise AssertionError('accepted '+name)
for graphable in [False,True]:
 m=Manager(graphable);b=SubstepContactBridge(m,control_decimation=8,fixture_cpu=True)
 reject('begin_before_install',lambda:b.begin(0));b.install();reject('double_install',b.install)
 arrays=[m.state.body_q,m.state.body_qd,m.model.body_mass,m.model.body_com,m.model.body_inertia,m._solver.mjw_data.efc.force,*vars(m._solver.mjw_data.contact).values()]
 before=[a.numpy().tobytes() for a in arrays]
 m.simulate();assert b.buffers.count.numpy()[0]==0
 for repeat in range(2):
  b.begin(repeat);m.simulate();r=b.finish();assert len(r['kinds'])==(25 if graphable else 32)
  assert np.all(r['valid']) and np.all(r['forces_world'][:,:,0]==5) and np.all(r['forces_world'][:,:,1:]==0)
  assert before==[a.numpy().tobytes() for a in arrays]
  checks.append(dict(kind='callback_schedule',all_graphable=graphable,repeat=repeat,records=len(r['kinds']),solver_state_and_model_byte_unchanged=True))
 assert b.metadata['body_labels']==['box','mailer'];np.testing.assert_allclose(b.metadata['body_com_local'],[[.01,0,0],[0,.01,0]])
 m._num_substeps=4;reject('schedule_changed',lambda:b.begin(3))
for name,mutate in [('captured_graph',lambda m:setattr(m,'_graph',object())),('double_state',lambda m:setattr(m,'_use_single_state',False)),('cpu_mujoco',lambda m:setattr(m._solver,'use_mujoco_cpu',True)),('sparse_update',lambda m:setattr(m._solver,'update_data_interval',2)),('manager_decimation',lambda m:setattr(m,'_decimation',1)),('invalid_mass',lambda m:m.model.body_mass.assign(np.array([0,.1],dtype=np.float32))),('missing_parcel',lambda m:setattr(m.model,'shape_label',['/other/a','/other/b','table']))]:
 m=Manager(True);mutate(m);reject(name,lambda:SubstepContactBridge(m,control_decimation=8,fixture_cpu=True));assert not m.pre and not m.post
m=Manager(True);reject('cpu_without_explicit_fixture',lambda:SubstepContactBridge(m,control_decimation=8));reject('unsupported_control_schedule',lambda:SubstepContactBridge(m,control_decimation=7,fixture_cpu=True))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,cuda_devices=[],physics_initialized=False,gpu_graph_tested=False,actual_runtime_installed=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'substep_contact_runtime_bridge.py',W/'substep_contact_observer_prototype.py']})
p=W/'SUBSTEP_RUNTIME_BRIDGE_CPU_CHECK.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print('PASS',len(checks),'CPU fixture checks; actual runtime and CUDA graph remain untested')
