"""Offline causal first-blocked-frame lift geometry, not controller integration.
Reuse unchanged existing lift optimizer and path checks to reach the original
0.84m measured entry guard with 5mm nominal allowance. No threshold relaxation.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_center_preference';sys.path[:0]=[str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from box_center_preference_plan import lift_endpoint,interpolate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);rows=[];sources={}
def save(complete):
 for p in [Path(__file__),*stage.glob('*.py'),stage/'elbow_torso_hulls.json',repo/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
 (w/'BOX_RECOVERY_LIFT_SCREEN.json').write_text(json.dumps(dict(scope=__doc__,complete=complete,rows=rows,source_sha256=sources,physical_validation=False,training_ready=False),indent=2))
for run in ['box_center_groups_r1','rear_slow_drag_groups_r1','rear_box_rate_groups_r1']:
 ep=w/run/'case_840001/layout_840001_push_box_to_bin';p=ep/'recontact_pose.json';events=json.loads(p.read_text())['rows'];sources[str(p)]=sha(p);seen=set()
 for e in events:
  if e.get('reason')!='initial_hand_below_unloaded_planning_height':continue
  ctx=e['context'];n=ctx['recontacts']
  if n in seen:continue
  seen.add(n);assert ctx['observed_load_n']==0 and 0<=ctx['filtered_load_n']<=.05
  q=np.array(ctx['current']);scene=RecontactScene(guard,**ctx['scene']);start=scene.check(q);desired_height=.845-scene.target[2]-scene.core[2]/2
  result=lift_endpoint(scene,q,desired_height) if start['accepted'] else None
  path=interpolate(scene,[q,np.array(result['candidate'])]) if result and result['accepted'] else None
  endpoint_z=None
  if path and path['accepted']:
   T=guard.model.fk(scene.side,result['candidate'])[0];endpoint_z=float(np.min((guard.model.vertices[scene.side]@T[:3,:3].T+T[:3,3])[:,2]))
  ok=bool(path and path['accepted'] and endpoint_z>=.84)
  row=dict(run=run,recontacts=n,step=e['step'],selection='first causally recorded rejected-height frame, not best future frame',start_scene=start,lift=result,path=path,nominal_endpoint_lowest_world_z_m=endpoint_z,geometry_accepted=ok)
  rows.append(row);save(False);print(run,n,e['step'],'accepted',ok,'waypoints',len(path['waypoints']) if path else None,'z',endpoint_z,flush=True)
save(True);print('COMPLETE',len(rows),'accepted',sum(x['geometry_accepted'] for x in rows),flush=True)
