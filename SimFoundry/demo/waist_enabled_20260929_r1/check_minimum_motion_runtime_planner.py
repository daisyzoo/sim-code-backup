"""All16 original actual recovery inputs through isolated causal runtime planner.
No simulation rollout or training admission. Independent geometry uses separate
URDF hand/elbow models; old default-off function AST must remain identical.
"""
from pathlib import Path
import ast,copy,json,sys,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_minimum_motion_recontact';parent=w/'staged_precise_parent_seed';sys.path[:0]=[str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from recontact_plan import plan
import minimum_motion_recontact as candidate
from audit_recontact_pose_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);audit=EventAudit(repo,stage);records=[];sources={}
old=ast.parse((parent/'recontact_plan.py').read_text());new=ast.parse((stage/'recontact_plan.py').read_text());f=next(n for n in new.body if isinstance(n,ast.FunctionDef));assert f.args.kwonlyargs[-1].arg=='minimum_motion_pose';f.args.kwonlyargs.pop();f.args.kw_defaults.pop();assert len(f.body[1].body)==4;f.body=f.body[2:];assert ast.dump(new)==ast.dump(old)
for name in ['recontact_plan_original.py','recontact_plan_deeper.py','recontact_scene.py','recontact_tracking.py','clearance_runtime.py','articulated_hand_geometry.py','self_clearance.py','recontact_lifecycle.py']:assert sha(stage/name)==sha(parent/name)

def independent_endpoint(x,scene,ctx):
 g,d=audit.geometry(x,ctx);axis=np.linalg.eigh(np.cov(audit.hand.vertices[scene.side].T))[1][:,0];alignment=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis);minimum=float(min(alignment**2-.8**2,*list(d['core'][:2]/2-abs(d['point'][:2])-.020),g['active_above_top_m']-.006,.007-g['active_above_top_m'],audit.hand.minz(x,scene.inactive)-.84,g['elbow_gap_m']-.005));assert minimum>=-2e-7 and min(g['hand_parcel_gaps_m'].values())>=.01-2e-7;assert np.all(x>=audit.lo-2e-7) and np.all(x<=audit.hi+2e-7);return dict(alignment=float(alignment),minimum=minimum)

for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 ep=w/'precise_interior_groups_r1'/f'case_{cid}'/f'layout_{cid}_{task}';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];starts=[e for e in events if e.get('planning') is not None];earliest=(starts[0]['step'],np.array(starts[0]['context']['current']))
 for event in starts:
  ctx=event['context'];q=np.array(ctx['current']);scene=RecontactScene(guard,**ctx['scene']);result=plan(scene,q,step=event['step'],earlier_seed=earliest,prefer_interior=True,minimum_motion_pose=True);meta=result['minimum_motion_pose'];assert meta['parent_plan']==event['planning'],'Original causal parent not exactly reproduced'
  independent=[]
  for a in meta['endpoint_attempts']:
   if not a['accepted']:continue
   x=np.array(a['candidate']);d=independent_endpoint(x,scene,ctx['scene']);assert abs(d['minimum']-a['minimum_constraint_m'])<2e-8;assert abs(np.sum((x-q)**2)-a['objective'])<1e-10;independent.append(d)
  if meta['selected']=='candidate':
   nodes=list(map(np.array,meta['nodes']));assert np.array_equal(nodes[0],q) and np.array_equal(nodes[-1],result['endpoint']);rebuilt=[]
   for a,b in zip(nodes,nodes[1:]):
    n=max(1,int(np.ceil(max(abs(b-a)/(audit.limits*.25)))));rebuilt.extend([np.clip(a+(b-a)*i/n,audit.lo,audit.hi) for i in range(1,n+1)])
   assert np.array_equal(rebuilt,result['waypoints']) and len(rebuilt)==meta['nominal_waypoints']
   for x,stored in zip(rebuilt,meta['selected_path_checks']):
    g,_=audit.geometry(x,ctx['scene']);assert g['accepted'];audit.compare_geometry(stored,g)
   for lift in meta['lift_attempts']:
    for field in ['start_lift','end_lift']:
     a=lift[field]
     if not a['accepted']:continue
     x=np.array(a['candidate']);ref=np.array(a['reference']);g,d=audit.geometry(x,ctx['scene']);_,rd=audit.geometry(ref,ctx['scene']);height=a['height_m'];m=float(min(*list(.002-abs(d['point'][:2]-rd['point'][:2])),g['active_above_top_m']-height,height+.001-g['active_above_top_m'],audit.hand.minz(x,scene.inactive)-.84,g['elbow_gap_m']-.005));assert m>=-2e-7 and abs(m-a['minimum_constraint_m'])<2e-8 and g['accepted']
  records.append(dict(episode=ep.name,step=event['step'],parent_plan_exact=True,selected=meta['selected'],route=meta.get('route'),waypoints=len(result.get('waypoints',[])),independent_endpoint_geometry=independent,plan=result));print(ep.name,event['step'],meta['selected'],meta.get('route'),len(result.get('waypoints',[])),flush=True)
  sources[str(ep/'recontact_pose.json')]=sha(ep/'recontact_pose.json');out=dict(scope=__doc__,complete=False,records=records,default_off_ast_exact=True,source_sha256=sources,physical_validation=False,training_ready=False);(stage/'RUNTIME_PLANNER_CHECK.json').write_text(json.dumps(out,indent=2))
# Failure means explicit parent fallback, not a fabricated candidate success.
class Failed:
 success=False;status=9;nit=220;fun=0.
 def __init__(self,x):self.x=x
saved=candidate.minimize
try:
 candidate.minimize=lambda fun,x,*a,**kw:Failed(x)
 fallback=candidate.plan(scene,q,step=event['step'],parent_plan=event['planning']);assert fallback['minimum_motion_pose']['selected']=='original_fallback' and fallback['minimum_motion_pose']['fallback_reason']=='no_verified_endpoint';stripped=dict(fallback);stripped.pop('minimum_motion_pose');assert stripped==event['planning']
finally:candidate.minimize=saved
rejected=0
for kwargs in [dict(prefer_interior=True,minimum_motion_pose=1),dict(prefer_interior=False,minimum_motion_pose=True)]:
 try:plan(scene,q,step=event['step'],**kwargs)
 except ValueError:rejected+=1
 else:raise AssertionError('bad configuration accepted')
assert len(records)==16
for p in [Path(__file__),stage/'minimum_motion_recontact.py',stage/'recontact_plan.py',w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py']+list(stage.glob('*.json')):
 if p.name.endswith('_CHECK.json'):continue
 sources[str(p)]=sha(p)
for name in ['recontact_plan_original.py','recontact_plan_deeper.py','recontact_scene.py','recontact_tracking.py','clearance_runtime.py','articulated_hand_geometry.py','self_clearance.py','recontact_lifecycle.py']:sources[str(stage/name)]=sha(stage/name)
out.update(complete=True,default_off_ast_exact=True,explicit_failed_solver_fallback_exact=True,invalid_configurations_rejected=rejected,candidate_paths=sum(r['selected']=='candidate' for r in records),source_sha256=sources);(stage/'RUNTIME_PLANNER_CHECK.json').write_text(json.dumps(out,indent=2));print('COMPLETE',out['candidate_paths'],flush=True)
