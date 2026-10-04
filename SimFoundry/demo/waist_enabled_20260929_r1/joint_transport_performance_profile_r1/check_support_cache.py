"""Unwired all-vertex cache comparison on all eight saved bilateral contexts.
Compare endpoints and fixed interpolants; replay16 original complete adaptive
paths and retain tiny floating-point differences explicitly. Not production
approval: a conservative error bound and boundary behavior remain required.
"""
from pathlib import Path
import sys,json,hashlib,datetime,time
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from support_cache_probe import CachedSupportAudit
from joint_transport_paths import JointTransportPaths
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();original=JointTransportPaths(ROOT,S);cached=JointTransportPaths(ROOT,S);cached.audit=CachedSupportAudit(ROOT,S);source={};records=[];maxerror=0.;old_seconds=0.;new_seconds=0.;paths_exact_structure=0
ref=json.loads((W/'joint_transport_runtime_preparation_r1/RUNTIME_CONTEXT_CHECK.json').read_text());source[str(W/'joint_transport_runtime_preparation_r1/RUNTIME_CONTEXT_CHECK.json')]=sha(W/'joint_transport_runtime_preparation_r1/RUNTIME_CONTEXT_CHECK.json')
for ctx in ref['contexts']:
 file=Path(ctx['record']);assert sha(file)==ctx['record_sha256'];record=json.loads(file.read_text());source[str(file)]=sha(file);p=record['proposal'];q=np.array(p['current']);scene=p['scene'];row=dict(side=ctx['side'],step=ctx['step'],paths=[])
 for kind,end in [('nominal',np.array(record['output_command'])),('predicted',np.array(p['predicted_q']))]:
  errs=[]
  for alpha in [0.,.125,.25,.5,.75,.875,1.]:
   state=q+alpha*(end-q);start=time.perf_counter();a=original.margins(state,scene);old_seconds+=time.perf_counter()-start;start=time.perf_counter();b=cached.margins(state,scene);new_seconds+=time.perf_counter()-start;err=float(np.max(abs(a-b)));errs.append(err);maxerror=max(maxerror,err);assert err<1e-11
  start=time.perf_counter();path=cached.certify(q,end,scene);elapsed=time.perf_counter()-start;old=record['paths'][kind];assert path['passed']==old['passed']==True and path['nodes']==old['nodes'] and path['max_depth']==old['max_depth'] and len(path['leaves'])==len(old['leaves'])
  errors=[]
  for x,y in zip(path['leaves'],old['leaves']):
   assert x['interval']==y['interval'];errors.extend(abs(np.array(x['lower_bounds_m'])-np.array(y['lower_bounds_m'])))
  assert max(errors)<1e-11;paths_exact_structure+=1;row['paths'].append(dict(kind=kind,nodes=path['nodes'],leaves=len(path['leaves']),cached_elapsed_s=elapsed,maximum_leaf_bound_difference_m=float(max(errors)),maximum_sample_margin_difference_m=max(errs),same_acceptance_and_subdivision=True))
 records.append(row);print(json.dumps(row),flush=True)
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):source[str(p)]=sha(p)
for p in [Path(__file__),D/'support_cache_probe.py',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:source[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,contexts=len(records),sampled_states=112,paths=paths_exact_structure,maximum_margin_difference_m=maxerror,original_sampled_margin_time_s=old_seconds,cached_sampled_margin_time_s=new_seconds,sampled_margin_speedup=old_seconds/new_seconds,records=records,source_sha256=source,production_ready=False,physical_execution=False,training_ready=False)
with (D/'SUPPORT_CACHE_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['records','source_sha256','scope']}),flush=True)
