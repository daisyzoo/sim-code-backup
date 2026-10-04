"""Profile one saved current-parent front-bag context; no physics or running-source changes."""
from pathlib import Path
import sys,json,hashlib,datetime,cProfile,pstats,time,io
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_runtime import JointTransportRuntime
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
ep=W/'front_loaded_z_quarter_physical_r2/case_840023/layout_840023_nudge_mailer_to_bin';t=190;ref=next(r for r in read(ep/'joint_transport_clearance.json')['rows'] if r['step']==t);ctx=ref['collector_context'];coordinate=next(r for r in read(ep/'coordination.json') if r['step']==t);front=next(r for r in read(ep/'frontal_bypass.json')['rows'] if r['step']==t)
with np.load(ep/'raw.npz',allow_pickle=False) as z:
 np.testing.assert_array_equal(z['q'][t,12:23],ctx['current']);np.testing.assert_array_equal(z['q'][t-1,12:23],ctx['previous_q']);np.testing.assert_array_equal(z['action'][t-1,12:23],ctx['previous_command'])
sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');guard=ClearanceGuard(ROOT,S);runtime=JointTransportRuntime(guard,ROOT,S,enabled=True);scene=RecontactScene(guard,**ctx['scene']);args=dict(step=t,selected=ref['selected'],side=ctx['side'],row=front,coordinate=coordinate,scene=scene,parent_command=ref['parent_command'],**{k:ctx[k] for k in ['current','previous_q','previous_command','decay']})
prof=cProfile.Profile();start=time.perf_counter();prof.enable();command,result=runtime.refine(**args);prof.disable();elapsed=time.perf_counter()-start
prof.dump_stats(str(D/'context.prof'));stream=io.StringIO();pstats.Stats(prof,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(35);(D/'PROFILE.txt').write_text(stream.getvalue())
np.testing.assert_array_equal(command,ref['output_command']);assert result=={k:v for k,v in ref.items() if k!='collector_context'}
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,step=t,elapsed_profiled_wall_s=elapsed,command_bit_identical=True,entire_runtime_record_exact=True,result_reason=result['reason'],solver_status=result['proposal']['solver_status'],solver_iterations=result['proposal']['iterations'],applied=result['applied'],source_sha256=sources,physical_execution=False,training_ready=False)
with (D/'RESULT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']}));print(stream.getvalue())
