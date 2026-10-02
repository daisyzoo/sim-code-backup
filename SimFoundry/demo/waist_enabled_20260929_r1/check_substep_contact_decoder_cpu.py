"""Validate the installed contact decoder with analytic fixtures on CPU.
No physics scene, CUDA graph, or runtime callback installation is exercised.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import json, hashlib, datetime
import numpy as np
import warp as wp
wp.config.kernel_cache_dir='/tmp/tilt05_substep_cpu_warp_cache'
wp.init()
assert not wp.get_cuda_devices(), 'Run with CUDA_VISIBLE_DEVICES empty'
from mujoco_warp._src import support
from mujoco_warp._src.types import ConeType, vec5
from substep_contact_observer_prototype import SubstepBuffers
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=lambda x,dtype:wp.array(np.asarray(x),dtype=dtype,device='cpu')
capacity=4
rot=np.array([[0,1,0],[-1,0,0],[0,0,1]],dtype=np.float32)
frames=np.stack([np.eye(3),rot,np.eye(3),rot]).astype(np.float32)
contact=NS(frame=a(frames,wp.mat33),friction=a(np.tile([.5,.4,.3,.2,.1],(capacity,1)),vec5),dim=a([3,3,1,6],int),efc_address=a([[0,1,2,3,4,5]]*capacity,int),worldid=a([0,1,0,1],int),geom=a([[0,2],[1,2],[2,2],[0,1]],wp.vec2i),pos=a([[0,0,0],[1,2,3],[4,5,6],[7,8,9]],wp.vec3))
data=NS(contact=contact,efc=NS(force=a([[1,2,3,4,5,6,7,8,9,10],[10,20,30,40,50,60,70,80,90,100]],float)),njmax=10,nacon=a([4],int))
ids=a(np.arange(capacity,dtype=np.int32),int)
output=a(np.full((capacity,6),999,dtype=np.float32),wp.spatial_vector)
model=NS(opt=NS(cone=ConeType.PYRAMIDAL))
q=a([[0,0,0,0,0,0,1],[1,0,0,0,0,0,1]],wp.transform)
qd=wp.zeros(2,dtype=wp.spatial_vector,device='cpu')
mapping=a([[0,1,2],[0,1,2]],int)
arrays={**vars(contact),'force':data.efc.force,'nacon':data.nacon,'ids':ids,'q':q,'qd':qd,'mapping':mapping}
def snapshot():return {k:v.numpy().tobytes() for k,v in arrays.items()}
def unchanged(before):assert before==snapshot(), 'Read-only decoder changed input arrays'
checks=[]
# Expected local values computed independently from constraint pyramid pairs.
pyramid=np.array([[10,-.5,-.4,0,0,0],[100,-5,-4,0,0,0],[1,0,0,0,0,0],[550,-5,-4,-3,-2,-1]],dtype=np.float32)
elliptic=np.array([[1,2,3,0,0,0],[10,20,30,0,0,0],[1,0,0,0,0,0],[10,20,30,40,50,60]],dtype=np.float32)
for cone,expected in [(ConeType.PYRAMIDAL,pyramid),(ConeType.ELLIPTIC,elliptic)]:
 model.opt.cone=cone
 for world in [False,True]:
  before=snapshot();support.contact_force(model,data,ids,world,output);actual=output.numpy();unchanged(before)
  reference=expected.copy()
  if world:
   for i in range(capacity):
    reference[i,:3]=expected[i,:3]@frames[i];reference[i,3:]=expected[i,3:]@frames[i]
  np.testing.assert_allclose(actual,reference,atol=1e-5,rtol=1e-6)
  checks.append(dict(cone=int(cone),world_frame=world,all_six_components_match=True,inputs_byte_unchanged=True))
# Glue the installed decoder output into independent buffers for both schedules.
model.opt.cone=ConeType.PYRAMIDAL
for managers,per in [(8,3),(1,24)]:
 b=SubstepBuffers(device='cpu',body_ids=(0,1),shape_is_target=[1,1,0],contact_capacity=capacity)
 before=snapshot();b.begin(0)
 def capture(kind):
  support.contact_force(model,data,ids,True,output)
  b.capture(kind,state_q=q,state_qd=qd,nacon=data.nacon,geom=contact.geom,world=contact.worldid,mapping=mapping,positions=contact.pos,world_forces=output)
 for _ in range(managers):
  for _ in range(per):capture(0)
  capture(1)
 packet=b.finish(expected_substeps=24,expected_manager_steps=managers);unchanged(before)
 assert packet['valid'][:,[0,1,3]].all() and not packet['valid'][:,2].any()
 world_expected=pyramid.copy()
 for i in range(capacity):
  world_expected[i,:3]=pyramid[i,:3]@frames[i];world_expected[i,3:]=pyramid[i,3:]@frames[i]
 np.testing.assert_allclose(packet['forces_world'][:,[0,1,3]],np.broadcast_to(world_expected[[0,1,3]],(24+managers,3,6)),atol=1e-5,rtol=1e-6)
 checks.append(dict(kind='decoder_plus_buffer',manager_steps=managers,records=24+managers,inputs_byte_unchanged=True,nonparcel_contact_filtered=True))
 # The installed kernel intentionally leaves invalid output slots untouched.
 # They must never be exposed as current contacts by the buffer's valid mask.
 stale=output.numpy().copy();data.nacon.assign(np.array([0],dtype=np.int32));before=snapshot();b.begin(1);capture(0);capture(1)
 packet=b.finish(expected_substeps=1,expected_manager_steps=1);unchanged(before)
 assert np.array_equal(output.numpy(),stale) and not packet['valid'].any()
 checks.append(dict(kind='stale_decoder_slots_masked',manager_steps=managers))
 data.nacon.assign(np.array([capacity],dtype=np.int32))
# A valid contact without a constraint address must decode to zero force.
adr=contact.efc_address.numpy().copy();adr[0]=-1;contact.efc_address.assign(adr);before=snapshot();support.contact_force(model,data,ids,True,output);unchanged(before);assert np.array_equal(output.numpy()[0],np.zeros(6))
checks.append(dict(kind='inactive_constraint_zero_force',inputs_byte_unchanged=True))
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,cuda_devices=[],device='cpu',physics_initialized=False,gpu_graph_tested=False,observer_installed=False,training_ready=False,limitations=['Synthetic analytic fixture, not a physical substep trajectory.','World-force sign relative to each actual body requires geometry-side convention binding.','State at end of solve is not assumed to be the pose where contact force was evaluated.','GPU graph replay and actual callback integration remain untested.'],source_sha256={str(p):sha(p) for p in [Path(__file__),W/'substep_contact_observer_prototype.py',Path(support.__file__)]})
p=W/'SUBSTEP_CONTACT_DECODER_CPU_CHECK.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print('PASS',len(checks),'analytic decoder and buffer checks; no GPU or physics claim')
