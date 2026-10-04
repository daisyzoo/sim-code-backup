"""Benchmark exact cached versus native effective solver on saved immutable contexts.
Require command and fullruntime record equality, including original failures.
No candidate rollout, dynamic successor state or new admission is inferred.
"""
from pathlib import Path
import copy,datetime,functools,hashlib,inspect,json,sys,time
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'effective_height_exact_cache_probe_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_effective_height_runtime_v1 import JointTransportRuntime
import joint_transport_effective_height_cached_solver_v1 as cached
assert Path(inspect.getfile(JointTransportRuntime)).resolve()==S/'joint_transport_effective_height_runtime_v1.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());sources={};rows=[];cache_handles=[]
def tracked_cache(*args,**kwargs):
 decorate=functools.lru_cache(*args,**kwargs)
 def wrap(fn):
  value=decorate(fn);cache_handles.append(value);return value
 return wrap
cached.lru_cache=tracked_cache
for case,task,step in [(840023,'nudge_mailer_to_bin',190),(840020,'push_box_to_bin',181)]:
 ep=W/f'front_loaded_z_quarter_physical_r2/case_{case}/layout_{case}_{task}';ref=next(r for r in read(ep/'joint_transport_clearance.json')['rows'] if r['step']==step);ctx=ref['collector_context'];coordinate=next(r for r in read(ep/'coordination.json') if r['step']==step);front=next(r for r in read(ep/'frontal_bypass.json')['rows'] if r['step']==step)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:
  np.testing.assert_array_equal(z['q'][step,12:23],ctx['current']);np.testing.assert_array_equal(z['q'][step-1,12:23],ctx['previous_q']);np.testing.assert_array_equal(z['action'][step-1,12:23],ctx['previous_command'])
 input_snapshot=json.dumps([ctx,coordinate,front],sort_keys=True);outputs=[]
 for use_cache in [False,True]:
  guard=ClearanceGuard(ROOT,S);runtime=JointTransportRuntime(guard,ROOT,S,enabled=True,effective_quarter_height=True)
  if use_cache:runtime._propose=functools.partial(cached.propose,quarter_enabled=True)
  scene=RecontactScene(guard,**ctx['scene']);args=dict(step=step,selected=ref['selected'],side=ctx['side'],row=front,coordinate=coordinate,scene=scene,parent_command=ref['parent_command'],**{k:ctx[k] for k in ['current','previous_q','previous_command','decay']})
  start=time.perf_counter();cmd,result=runtime.refine(**args);elapsed=time.perf_counter()-start;outputs.append((cmd,result,elapsed));assert json.dumps([ctx,coordinate,front],sort_keys=True)==input_snapshot
  print(json.dumps(dict(episode=ep.name,step=step,cache=use_cache,elapsed_s=elapsed,reason=result['reason'],applied=result['applied'],status=result.get('proposal',{}).get('solver_status'))),flush=True)
 np.testing.assert_array_equal(outputs[0][0],outputs[1][0]);assert outputs[0][1]==outputs[1][1],'Fullruntime record changed'
 assert len(cache_handles)==len(rows)+1;info=cache_handles[-1].cache_info();assert info.maxsize==256 and info.currsize<=256
 rows.append(dict(episode=ep.name,step=step,native_elapsed_s=outputs[0][2],cached_elapsed_s=outputs[1][2],observed_speedup=outputs[0][2]/outputs[1][2],command_bit_identical=True,entire_runtime_record_exact=True,cache_info=info._asdict(),result=outputs[1][1]))
 for p in [ep/'raw.npz',ep/'coordination.json',ep/'frontal_bypass.json',ep/'joint_transport_clearance.json']:sources[str(p)]=sha(p)
# Each call must allocate a separate cache even when keys happen to overlap.
assert len(cache_handles)==2 and cache_handles[0] is not cache_handles[1]
for p in [Path(__file__),Path(cached.__file__),D/'DERIVATION.json',*[p for p in S.iterdir() if p.is_file()]]:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,separate_per_call_caches=True,source_sha256=sources,installed=False,physical_execution=False,training_ready=False,limitation='Two fixed saved-context measurements, not a general speedup or newphysics success. Original status9 stays rejected.')
with (D/'NATIVE_PARITY_AND_TIMING_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,cases=len(rows),speedups=[r['observed_speedup'] for r in rows],installed=False)),flush=True)
