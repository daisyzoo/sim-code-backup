"""20mm interior landing vs frozen 12mm on ALL18 recorded recovery starts.
Only planner inset changes. Original joint limits, wrist objective, height,
clearance and seeds retained. Raw q/object states independently bind context.
Independent geometry checks endpoints and interpolated path waypoints; this is
not physics, actual COP stability, handover or training admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_pose';probe=w/'staged_recontact_deeper_probe';sys.path[:0]=[str(probe),str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from recontact_plan_deeper import plan
from audit_recontact_pose_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);audit=EventAudit(repo,stage);records=[];sources={}
for cid,task,side,key,other in [(840001,'push_box_to_bin','right','box','mailer'),(840004,'nudge_mailer_to_bin','left','mailer','box')]:
 ep=w/'recontact_pose_groups_r1'/f'case_{cid}'/f'layout_{cid}_{task}';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];starts=[r for r in events if r.get('planning')];assert len(starts)==9
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);oxyz=z[other].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float);oquat=z[other].astype(float)
 first=starts[0]['step'];seed=(first,qs[first].copy());core=json.loads((ep/'frontal_bypass.json').read_text())['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']
 for event in starts:
  t=event['step'];ctx=event['context'];assert np.max(abs(np.array(ctx['current'])-qs[t]))<1e-7;scene=RecontactScene(guard,side,xyz[t],quat[t],core,oxyz[t],oquat[t],[.15,.145,.04] if other=='mailer' else [.14,.09,.045]);scene_record=scene.record()
  for k,v in scene_record.items():
   if isinstance(v,list):assert np.max(abs(np.array(v)-ctx['scene'][k]))<1e-7,(t,k)
   else:assert ctx['scene'][k]==v
  assert ctx['observed_load_n']==0 and 0<=ctx['filtered_load_n']<=.05
  variants=[]
  new=plan(scene,qs[t],step=t,earlier_seed=seed)
  for label,result,inset in [('parent_recorded_12mm',event['planning'],.012),('deeper_20mm',new,.020)]:
   entry=dict(label=label,planner_accepted=result['accepted'],plan=result)
   if result['accepted']:
    x=np.array(result['endpoint']);g,detail=audit.geometry(x,scene_record);margins=detail['core'][:2]/2-abs(detail['point'][:2]);inactive='left' if side=='right' else 'right';height=g['active_above_top_m'];bounds=bool(np.all(x>=audit.lo-2e-7) and np.all(x<=audit.hi+2e-7));endpoint=bool(min(margins)>=inset-2e-7 and .006-2e-7<=height<=.007+2e-7 and min(g['hand_parcel_gaps_m'].values())>=.01-2e-7 and g['elbow_gap_m']>=.005-2e-7 and audit.hand.minz(x,inactive)>=.84-2e-7 and bounds)
    assert endpoint,(ep.name,t,label)
    path=[audit.geometry(np.array(y),scene_record)[0] for y in result['waypoints']];bad=[i for i,p in enumerate(path) if not p['accepted']]
    entry.update(independent_endpoint_passed=endpoint,independent_margins_mm=(margins*1000).tolist(),path_waypoints=len(path),path_rejected_indices=bad,all_interpolated_waypoints_passed=not bad,waist_yaw=float(x[0]),wrist=float(x[5 if side=='left' else 10]),max_joint_shift_rad=float(max(abs(x-qs[t]))))
   variants.append(entry)
  records.append(dict(episode=ep.name,step=t,variants=variants));print(ep.name,t,[(v['label'],v['planner_accepted'],v.get('path_waypoints'),len(v.get('path_rejected_indices',[]))) for v in variants],flush=True)
 for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','recontact_pose.json']:sources[str(ep/name)]=sha(ep/name)
for p in [Path(__file__),probe/'recontact_plan_deeper.py',stage/'recontact_plan.py',stage/'recontact_scene.py',stage/'clearance_runtime.py',w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
assert len(records)==18
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,physical_validation=False,collector_connected=False,training_ready=False);(probe/'DEEPER_ENDPOINT_SCREEN.json').write_text(json.dumps(out,indent=2));print('DONE18starts',flush=True)
