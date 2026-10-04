"""All actual new rejection/loss contexts plus two historical right contexts.
Two predeclared reserve settings; stricter solver stopping, original objective,
contact and1e-6 certificate. No physical command or old-future continuation.
"""
from pathlib import Path
import sys,json,hashlib,datetime,time,copy
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';F=W/'joint_transport_performance_profile_r1';sys.path[:0]=[str(D),str(F),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from reserve_solver import propose
from reserve_certificate import verify
from bounded_support_paths_v1 import BoundedSupportPaths
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};out=D/'RESULT.json';assert not out.exists();rows=[];guard=ClearanceGuard(ROOT,S);paths=BoundedSupportPaths(ROOT,S)
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
plan=read(D/'PLAN.json')
for name,bind in plan['changed_sources'].items():assert sha(D/name)==bind['output_sha256'] and sha(bind['parent'])==bind['parent_sha256']
def save(complete):
 for mod in list(sys.modules.values()):
  f=getattr(mod,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
 for p in [Path(__file__),F/'SUPPORT_ERROR_BOUND.md',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
 obj=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=complete,contexts=len(contexts),expected_variants=2*len(contexts),rows=rows,source_sha256=sources,physical_execution=False,training_ready=False)
 tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2));tmp.replace(out)
new=W/'joint_transport_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';jr=read(new/'joint_transport_clearance.json')['rows'];selected=sorted({157,233,368}|{x['step'] for x in jr if x['reason']=='independent_constraints_rejected'});assert len(selected)==15
contexts=[(new,'joint_transport_clearance.json',t) for t in selected]+[(W/'inactive_transport_physical_r1/case_840020/layout_840020_push_box_to_bin','inactive_transport_clearance.json',t) for t in [808,813]]
cache={}
for ep,record_file,t in contexts:
 if str(ep) not in cache:
  rec=read(ep/record_file)['rows'];coord={r['step']:r for r in read(ep/'coordination.json')};front={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']}
  with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');cache[str(ep)]=(rec,coord,front,q,u)
 recs,coords,front,q,u=cache[str(ep)];rec=recs[t];ctx=rec['collector_context'];coordinate=coords[t];scene=RecontactScene(guard,**ctx['scene']);assert rec['selected']
 for key,actual in [('current',q[t]),('previous_q',q[t-1]),('previous_command',u[t-1])]:np.testing.assert_array_equal(ctx[key],actual)
 np.testing.assert_array_equal(rec['output_command'],u[t]);np.testing.assert_array_equal(coordinate['front_loaded_z_priority']['output_command'],rec['parent_command'])
 for reserve in [0.,.0015]:
  start=time.perf_counter();command,proposal=propose(step=t,side=ctx['side'],scene=scene,**{k:ctx[k] for k in ['current','previous_q','previous_command','decay']},parent_command=rec['parent_command'],coordinate=coordinate,elbow_reserve_m=reserve)
  certificate=verify(proposal,coordinate['task_inputs'],coordinate,guard=guard,elbow_reserve_m=reserve);path_results={}
  if command is not None and certificate['passed']:
   path_results={k:paths.certify(q[t],end,ctx['scene']) for k,end in [('nominal',command),('predicted',np.array(proposal['predicted_q']))]}
  negatives=[]
  for key,val in [('elbow_reserve_m',.0015 if reserve==0 else 0.),('nominal_predicted_elbow_floor_m',.004)]:
   bad=copy.deepcopy(proposal);bad[key]=val
   try:verify(bad,coordinate['task_inputs'],coordinate,guard=guard,elbow_reserve_m=reserve)
   except ValueError:negatives.append(key)
   else:raise AssertionError('Changed policy accepted')
  good=bool(command is not None and certificate['passed'] and len(path_results)==2 and all(x['passed'] for x in path_results.values()))
  row=dict(episode=ep.name,source_run=ep.parent.parent.name,step=t,mode=front[t]['mode'],historical_reason=rec['reason'],reserve_m=reserve,solver_success=proposal['solver_success'],solver_status=proposal['solver_status'],iterations=proposal['iterations'],preliminary_passed=proposal['preliminary_passed'],certificate_passed=certificate['passed'],stationarity=certificate.get('certificate',{}).get('stationarity_residual'),fully_verified_unissued=good,elapsed_s=time.perf_counter()-start,nominal_elbow_gaps_mm=(guard.geometry.constraints(np.array(proposal['command']))*1000).tolist(),predicted_elbow_gaps_mm=proposal['predicted_elbow_gaps_mm'],negative_policy_rejections=negatives,proposal=proposal,certificate=certificate,paths=path_results);rows.append(row);save(False);print(json.dumps({k:v for k,v in row.items() if k not in ['proposal','certificate','paths']}),flush=True)
assert len(rows)==34;save(True);print('COMPLETE34',sum(x['fully_verified_unissued'] for x in rows),flush=True)
