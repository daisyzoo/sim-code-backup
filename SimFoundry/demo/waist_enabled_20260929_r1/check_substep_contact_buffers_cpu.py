"""CPU-only independent buffer/sequence tests using actual recorded contacts.
Synthetic substep state sequence is not a physical trajectory or GPU graph test.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
import warp as wp
wp.config.enable_cuda=False
wp.config.kernel_cache_dir='/tmp/tilt05_substep_cpu_warp_cache'
wp.init()
from substep_contact_observer_prototype import SubstepBuffers
W=Path(__file__).resolve().parent;EP=W/'tilt05_groups_r1/case_840001/layout_840001_push_box_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
packet=next(x for x in json.loads((EP/'solved_contact_forces.json').read_text())['rows'] if x['after_action_step']==300);contacts=packet['parcel_contacts'];labels=sorted({s for x in contacts for s in x['shapes']});label_index={s:i for i,s in enumerate(labels)};n=len(contacts);capacity=n+4
geom=np.zeros((capacity,2),dtype=np.int32);pos=np.full((capacity,3),999.,dtype=np.float32);force=np.full((capacity,6),999.,dtype=np.float32)
for i,c in enumerate(contacts):
 geom[i]=[label_index[s] for s in c['shapes']];pos[i]=c['position_world'];local=np.asarray(c['force_torque_contact']);frame=np.asarray(c['contact_frame']);assert np.max(abs(local[:3]@frame-c['force_world_N']))<1e-5;force[i]=np.r_[c['force_world_N'],local[3:]@frame]
with np.load(EP/'trace.npz') as tr,np.load(EP/'parcel_orientation.npz') as ori:poses=np.stack([np.r_[tr[k][301],ori[k][301]] for k in ['box','mailer']]).astype(np.float32)
mask=np.array([int('/parcel_box/' in s or '/mailer/' in s) for s in labels],dtype=np.int32)
inputs=dict(state_q=wp.array(poses,dtype=wp.transform,device='cpu'),state_qd=wp.zeros(2,dtype=wp.spatial_vector,device='cpu'),nacon=wp.array([n],dtype=int,device='cpu'),geom=wp.array(geom,dtype=wp.vec2i,device='cpu'),world=wp.zeros(capacity,dtype=int,device='cpu'),mapping=wp.array(np.arange(len(labels),dtype=np.int32)[None],dtype=int,device='cpu'),positions=wp.array(pos,dtype=wp.vec3,device='cpu'),world_forces=wp.array(force,dtype=wp.spatial_vector,device='cpu'))
original={k:v.numpy().copy() for k,v in inputs.items()}
def make(cap=40,ids=(0,1)):return SubstepBuffers(device='cpu',body_ids=ids,shape_is_target=mask,contact_capacity=capacity,capacity=cap)
def capture(b,k):
 before={name:a.numpy().copy() for name,a in inputs.items()};b.capture(k,**inputs)
 for name,a in inputs.items():assert np.array_equal(a.numpy().view(np.uint8),before[name].view(np.uint8)),'input mutation: '+name
checks=[]
for managers,per in [(8,3),(1,24)]:
 b=make();capture(b,0);assert int(b.count.numpy()[0])==0
 for replay in range(2):
  b.begin(replay);states=[];tick=0
  for _ in range(managers):
   for _ in range(per):
    inputs['state_q'].assign(poses+np.array([[tick*.0001,0,0,0,0,0,0]]*2,dtype=np.float32));states.append(inputs['state_q'].numpy().copy());capture(b,0);tick+=1
   inputs['state_q'].assign(poses+np.array([[tick*.0001,0,0,0,0,0,0]]*2,dtype=np.float32));states.append(inputs['state_q'].numpy().copy());capture(b,1)
  out=b.finish(expected_substeps=24,expected_manager_steps=managers)
  assert np.array_equal(out['body_q'],states);assert out['valid'][:,:n].all() and not out['valid'][:,n:].any()
  assert np.array_equal(out['forces_world'][:,:n],np.broadcast_to(force[:n],(len(states),n,6)))
  assert np.array_equal(out['positions'][:,:n],np.broadcast_to(pos[:n],(len(states),n,3)))
  assert np.array_equal(out['shapes'][:,:n],np.broadcast_to(geom[:n],(len(states),n,2)))
  checks.append(dict(kind='recorded_contact_copy_and_exact_sequence',manager_steps=managers,replay=replay,records=len(states),input_arrays_unchanged=True))
 # Empty contacts after real contacts may not leak old valid slots.
 inputs['nacon'].assign(np.array([0],dtype=np.int32));b.begin(2);capture(b,0);capture(b,1);out=b.finish(expected_substeps=1,expected_manager_steps=1);assert not out['valid'].any();inputs['nacon'].assign(np.array([n],dtype=np.int32));checks.append(dict(kind='no_stale_contacts',manager_steps=managers))

def reject(label,fn):
 try:fn()
 except ValueError:checks.append(dict(kind='rejected',case=label))
 else:raise AssertionError('accepted invalid '+label)
b=make();reject('finish_without_begin',lambda:b.finish(expected_substeps=1,expected_manager_steps=1));b.begin(0);reject('nested_begin',lambda:b.begin(1));capture(b,0);capture(b,1);reject('wrong_substep_count',lambda:b.finish(expected_substeps=24,expected_manager_steps=1))
b=make();b.begin(0);capture(b,0);capture(b,0);capture(b,1);capture(b,1);reject('misplaced_post_boundaries',lambda:b.finish(expected_substeps=2,expected_manager_steps=2))
b=make(2);b.begin(0);capture(b,0);capture(b,0);capture(b,1);reject('buffer_overflow',lambda:b.finish(expected_substeps=2,expected_manager_steps=1))
for value in [-1,capacity+1]:
 inputs['nacon'].assign(np.array([value],dtype=np.int32));b=make();b.begin(0);capture(b,0);capture(b,1);reject('invalid_contact_count_'+str(value),lambda:b.finish(expected_substeps=1,expected_manager_steps=1))
inputs['nacon'].assign(np.array([n],dtype=np.int32))
for kind,bad in [('world',-1),('geom',len(labels))]:
 arr=inputs[kind].numpy().copy();arr[0]=bad;inputs[kind].assign(arr);b=make();b.begin(0);capture(b,0);capture(b,1);reject('invalid_'+kind,lambda:b.finish(expected_substeps=1,expected_manager_steps=1));inputs[kind].assign(original[kind])
b=make(ids=(0,99));b.begin(0);reject('body_id_outside_state',lambda:capture(b,0))
b=make();reject('bool_kind',lambda:capture(b,True))
inputs['world_forces'].assign(np.where(np.arange(capacity)[:,None]==0,np.nan,force).astype(np.float32));b=make();b.begin(0);capture(b,0);capture(b,1);reject('nonfinite_selected_force',lambda:b.finish(expected_substeps=1,expected_manager_steps=1));inputs['world_forces'].assign(original['world_forces'])
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,recorded_input_contact_count=n,observed_parcel_bodies=2,device='cpu',cuda_disabled=True,initial_fixture_failure='NaN comparison used array_equal without byte comparison; corrected read-only check to exact bytes, original failure log retained.',initial_fixture_failure_log_sha256=sha('/tmp/substep_buffer_cpu_check.log'),physics_initialized=False,gpu_graph_tested=False,observer_installed=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'substep_contact_observer_prototype.py',EP/'solved_contact_forces.json',EP/'trace.npz',EP/'parcel_orientation.npz']},training_ready=False)
p=W/'SUBSTEP_BUFFER_CPU_CHECK.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print('PASS',len(checks),'checks; CPU only, no physical/GPU replay claim')
