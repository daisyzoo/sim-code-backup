"""Real CUDA graph/replay on analytic fixture arrays, no physical scene.
Checks graph replay against changed live input buffers and exact callback order.
The fixture Manager is not NewtonManager; scene integration remains untested.
"""
from pathlib import Path
import ast,copy,json,hashlib,datetime
from types import SimpleNamespace as NS
import numpy as np
import warp as wp
wp.config.kernel_cache_dir='/tmp/tilt05_substep_gpu_warp_cache';wp.init()
assert wp.get_cuda_devices(), 'GPU required'
from mujoco_warp._src.types import vec5,ConeType
from substep_contact_runtime_bridge import SubstepContactBridge
W=Path(__file__).resolve().parent
arr=lambda x,t:wp.array(np.asarray(x),dtype=t,device='cuda:0')
# Reuse the previously checked fixture class, changing allocation device only.
fixture_path=W/'check_substep_runtime_bridge_cpu.py'
tree=ast.parse(fixture_path.read_text());node=copy.deepcopy(next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Manager'))
class DeviceOnly(ast.NodeTransformer):
 def visit_Constant(self,n):
  return ast.copy_location(ast.Constant('cuda:0'),n) if n.value=='cpu' else n
node=DeviceOnly().visit(node);exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(fixture_path),'exec'))
checks=[]
for graphable in [False,True]:
 m=Manager(graphable);b=SubstepContactBridge(m,control_decimation=8);b.install()
 def one_manager_step():
  for _ in range(24 if graphable else 3):
   for cb in m.pre:cb(m.state)
  for cb in m.post:cb()
 arrays=[m.state.body_q,m.state.body_qd,m.model.body_mass,m.model.body_com,m.model.body_inertia,m._solver.mjw_data.efc.force,m._solver.mjw_data.nacon,*vars(m._solver.mjw_data.contact).values()]
 def snapshot():return [a.numpy().tobytes() for a in arrays]
 def launch_control():
  for _ in range(1 if graphable else 8):wp.capture_launch(graph)
 # Compile kernels with recording disabled, before capture. No simulation step.
 before=snapshot();one_manager_step();wp.synchronize();assert snapshot()==before
 assert b.buffers.count.numpy()[0]==0
 with wp.ScopedCapture(device='cuda:0') as cap:one_manager_step()
 graph=cap.graph;m._graph=graph
 launch_control();wp.synchronize();assert b.buffers.count.numpy()[0]==0 and snapshot()==before
 checks.append(dict(kind='capture_and_disabled_replay',all_graphable=graphable,count=0,inputs_byte_unchanged=True))
 for interval,value in enumerate([5.,7.,11.]):
  m._solver.mjw_data.efc.force.assign(np.array([[value]],dtype=np.float32))
  q=m.state.body_q.numpy();q[:,0]=np.array([interval*.01,1+interval*.01],dtype=np.float32);m.state.body_q.assign(q)
  before=snapshot();b.begin(interval);launch_control();r=b.finish();assert snapshot()==before
  assert len(r['kinds'])==(25 if graphable else 32)
  np.testing.assert_array_equal(r['body_q'],np.broadcast_to(q,r['body_q'].shape))
  assert np.all(r['valid']) and np.all(r['forces_world'][:,:,0]==value) and np.all(r['forces_world'][:,:,1:]==0)
  checks.append(dict(kind='changed_live_inputs_observed_after_graph_capture',all_graphable=graphable,interval=interval,force_n=value,records=len(r['kinds']),inputs_byte_unchanged=True))
  count=int(b.buffers.count.numpy()[0]);launch_control();wp.synchronize();assert int(b.buffers.count.numpy()[0])==count
  checks.append(dict(kind='disabled_replay_does_not_append',all_graphable=graphable,interval=interval))
 # Contact kernel leaves empty slots stale. They must remain invalid on replay.
 m._solver.mjw_data.nacon.assign(np.array([0],dtype=np.int32));before=snapshot();b.begin(3);launch_control();r=b.finish();assert snapshot()==before and not r['valid'].any()
 checks.append(dict(kind='empty_contacts_no_stale_valid_rows',all_graphable=graphable))
 # Two controls inside one interval must fail, not silently clip records.
 b.begin(4);launch_control();launch_control()
 try:b.finish()
 except ValueError:checks.append(dict(kind='overflow_rejected_after_graph_replay',all_graphable=graphable))
 else:raise AssertionError('overflow accepted')
 # Existing graph may not be silently recaptured by a new bridge.
 try:SubstepContactBridge(m,control_decimation=8)
 except ValueError:checks.append(dict(kind='install_after_capture_rejected',all_graphable=graphable))
 else:raise AssertionError('preexisting graph accepted')
 wp.synchronize()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
from mujoco_warp._src import support
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,device=str(wp.get_device('cuda:0')),gpu_name=wp.get_device('cuda:0').name,warp_version=wp.__version__,gpu_graph_tested=True,physics_initialized=False,actual_runtime_installed=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),fixture_path,W/'substep_contact_runtime_bridge.py',W/'substep_contact_observer_prototype.py',Path(support.__file__)]})
p=W/'SUBSTEP_RUNTIME_BRIDGE_GPU_CHECK.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print('PASS',len(checks),'CUDA graph/replay checks; not an actual Newton scene')
