"""Current-observation-only20mm trailing landing feasibility for failed front box.
Separate from running rear-only and queued lateral experiments. No new actions,
no copied future response, no physical task success or data admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,importlib.util
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_plan import plan as original_plan,checked_scene
spec=importlib.util.spec_from_file_location('front_trailing_offset',D/'offset_plan.py');candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=W/'joint_transport_reserve_physical_r1/case_840020/layout_840020_push_box_to_bin';src=ep/'front_recontact_center.json';data=json.loads(src.read_text());allrows=[r for r in data['rows'] if r.get('planning')];assert len(allrows)==13;selected=[allrows[i] for i in [0,6,12]];guard=ClearanceGuard(ROOT,S);results=[];sources={str(p):sha(p) for p in [Path(__file__),D/'offset_plan.py',D/'PREPARATION.json',src,ep/'raw.npz',ep/'coordination.json',ep/'trace.npz',ep/'parcel_orientation.npz']}
for idx,row in enumerate(selected):
 z=row['context']['scene'];scene=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);q=np.asarray(row['context']['current']);assert np.array_equal(q,np.asarray(row['planning']['start']));offset=(scene.rotation.T@np.array([0.,.020,0.]))[:2]
 if idx==0:
  old=original_plan(scene,q,step=row['step']);off=candidate.plan(scene,q,step=row['step']);off.pop('landing_preference_local_xy');assert old==off,'zero-offset must reproduce full planner'
  for bad in [(0.,.021),(float('nan'),0.),(0.,)]:
   try:candidate.plan(scene,q,step=row['step'],offset_local_xy=bad)
   except ValueError:pass
   else:raise AssertionError('Invalid offset accepted')
 out=candidate.plan(scene,q,step=row['step'],offset_local_xy=offset);assert out['scene']==scene.record();result=dict(step=row['step'],recontact_index=row['real_recontact_index'],offset_local_xy=offset.tolist(),planning=out)
 if out['accepted']:
  x=np.asarray(out['endpoint']);details=scene.details(x);point=np.asarray(details['point']);assert np.max(abs(point[:2]-offset))<=.002+2e-7;assert scene.core[2]/2+.006-2e-7<=point[2]<=scene.core[2]/2+.007+2e-7;assert checked_scene(scene,x)['accepted']
  for waypoint in out['waypoints']:assert checked_scene(scene,waypoint)['accepted']
  result.update(actual_geometry_rechecked=True,endpoint_local_point=point.tolist(),nominal_waypoints=len(out['waypoints']),reference_center_nominal_waypoints=row['planning']['nominal_path_nodes'])
 results.append(result);(D/'LIVE_PROGRESS.json').write_text(json.dumps(dict(completed_contexts=len(results),total_contexts=3,rows=results,training_ready=False),indent=2));print(json.dumps({k:v for k,v in result.items() if k!='planning'}),flush=True)
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,completed=True,zero_offset_full_planner_identical=True,invalid_offset_rejections=3,contexts=results,source_sha256=sources,limitations=['New20mm landing location is a deliberate expert design change; not a relaxation of task/other-object gates.','Nominal sampled geometry cannot establish actual240tick tracking, dynamic margins, COP location or sustained transport.','No current collector/lifecycle/auditor was changed.'],physical_started=False,training_ready=False)
with (D/'RESULT.json').open('x') as f:json.dump(out,f,indent=2)
print('COMPLETE',flush=True)
