"""Boundary/domain/rejected-state validation of unwired interval support paths.
No live controller edit and no new physical trajectory or training admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,time
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from bounded_support_paths_v1 import BoundedSupportPaths,BoundedSupportAudit,ERROR_M,TOL
from joint_transport_paths import JointTransportPaths
from audit_front_recontact_center_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[];bounds=[];rejections=[];domains=[];max_difference=0.;start=time.perf_counter()
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
ref=read(W/'joint_transport_runtime_preparation_r1/RUNTIME_CONTEXT_CHECK.json');fast=BoundedSupportPaths(ROOT,S);original=JointTransportPaths(ROOT,S)
for ctx in ref['contexts']:
 file=Path(ctx['record']);assert sha(file)==ctx['record_sha256'];record=read(file);q=np.array(record['proposal']['current']);scene=record['proposal']['scene']
 for kind,end in [('nominal',np.array(record['output_command'])),('predicted',np.array(record['proposal']['predicted_q']))]:
  began=time.perf_counter();path=fast.certify(q,end,scene);old=record['paths'][kind];assert path['passed']==old['passed']==True and path['nodes']==old['nodes'] and path['max_depth']==old['max_depth'] and len(path['leaves'])==len(old['leaves']);differences=[]
  for x,y in zip(path['leaves'],old['leaves']):
   assert x['interval']==y['interval'];delta=np.array(x['lower_bounds_m'])-np.array(y['lower_bounds_m']);assert max(delta)<=2e-15 and min(delta)>=-ERROR_M-2e-15;differences.extend(abs(delta))
  max_difference=max(max_difference,max(differences));rows.append(dict(side=ctx['side'],step=ctx['step'],kind=kind,nodes=path['nodes'],same_decisions_and_subdivision=True,boundary_fallbacks=path['boundary_fallbacks'],elapsed_s=time.perf_counter()-began,maximum_leaf_difference_m=float(max(differences))));print(json.dumps(rows[-1]),flush=True)
 m=fast.margins(q,scene);exact=original.margins(q,scene)
 for margin in [1,2,3]:
  for delta in [-2*ERROR_M,-.5*ERROR_M,0.,.5*ERROR_M,2*ERROR_M]:
   offset=np.zeros(6);offset[margin]=m[margin]+TOL+delta;passed,reported,bound,fallback=fast.decide(q,scene,offset);expected=bool(min(exact-offset)>=-TOL);assert passed==expected
   if abs(delta)<=.5*ERROR_M:assert fallback and np.array_equal(reported,exact)
   if passed:assert min(bound)>=-TOL
   bounds.append(dict(side=ctx['side'],step=ctx['step'],margin=fast.labels[margin],offset_from_threshold_m=delta,passed=passed,reference_passed=expected,original_projection_fallback=fallback))
for cid,task,step in [(840023,'nudge_mailer_to_bin',374),(840020,'push_box_to_bin',816)]:
 ep=W/'inactive_transport_physical_r1'/f'case_{cid}'/f'layout_{cid}_{task}';r=read(ep/'inactive_transport_clearance.json')['rows'][step];c=r['collector_context'];q=np.array(c['current']);end=np.array(r['output_command']);scene=c['scene']
 with np.load(ep/'raw.npz',allow_pickle=False) as z:np.testing.assert_array_equal(q,z['q'][step,12:23]);np.testing.assert_array_equal(end,z['action'][step,12:23])
 sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');a=original.certify(q,end,scene);b=fast.certify(q,end,scene);assert a['passed']==b['passed']==False and a['reason']==b['reason']=='endpoint_geometry';rejections.append(dict(episode=ep.name,step=step,original=a,cached=b))
# Domain fallbacks are tested on intentionally altered direct-gap inputs only.
ctx=ref['contexts'][0];record=read(Path(ctx['record']));scene=record['proposal']['scene'];q=np.array(record['proposal']['current']);side=scene['side'];pose=fast.audit.hand.fk(q,side)
for label,transform,pos in [('nonorthogonal_pose',pose.copy(),np.array(scene['target_xyz'])),('large_translation',pose.copy(),np.array(scene['target_xyz'])),('large_box_position',pose.copy(),np.array([11.,0.,0.]))]:
 if label=='nonorthogonal_pose':transform[0,0]+=.01
 if label=='large_translation':transform[0,3]=11.
 before=fast.audit.full_projection_calls;b=fast.audit.gap(side,transform,pos,scene['target_quat'],scene['core_size']);a=RecoveryEventAudit.gap(fast.audit,side,transform,pos,scene['target_quat'],scene['core_size']);assert a==b and fast.audit.full_projection_calls==before+1;domains.append(dict(case=label,original_full_projection_exact=True))
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),D/'SUPPORT_ERROR_BOUND.md',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
assert len(rows)==16 and len(bounds)==120 and len(rejections)==2 and len(domains)==3
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,paths=rows,boundary_cases=bounds,rejected_actual_states=rejections,domain_fallbacks=domains,maximum_leaf_bound_difference_m=float(max_difference),elapsed_s=time.perf_counter()-start,source_sha256=sources,production_ready=False,physical_execution=False,training_ready=False)
with (D/'BOUNDED_SUPPORT_PATH_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,paths=len(rows),boundary_cases=len(bounds),boundary_fallbacks=sum(x['original_projection_fallback'] for x in bounds),actual_state_rejections=len(rejections),domain_fallbacks=len(domains),elapsed_s=out['elapsed_s'])),flush=True)
