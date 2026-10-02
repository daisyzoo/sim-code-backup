"""Recompute original measured-ready predicate along saved hypothetical paths.
Ideal nominal path-index timing is a screen, not live tracking or impossibility proof.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=W/'FRONT_ALTERNATIVE_REAR_LANDING_PROBE_V2.json';old=W/'FRONT_ALTERNATIVE_REAR_LANDING_FINDINGS.json';data=json.loads(source.read_text());assert data['status']=='complete'
guard=ClearanceGuard(ROOT,S);rows=[]
for item in data['rows']:
 p=item['planner'];r=dict(episode=item['episode'],point=item['point'],static_landing_verified=item['verified_static_landing_and_nominal_path'],physical_transport_verified=False)
 if p['accepted']:
  scene=RecontactScene(guard,**p['scene']);end=np.asarray(p['endpoint']);points=[np.asarray(p['start'])]+[np.asarray(x) for x in p['waypoints']];checks=[]
  for i,q in enumerate(points):
   g=scene.details(q);gap=float(np.max(abs(q-end)));height=float(g['point'][2]-scene.core[2]/2);inset=float(np.min(scene.core[:2]/2-abs(g['point'][:2])))
   ready=bool(gap<=.003 and inset>=.01 and .004<=height<=.01 and np.all(q>=guard.lower-2e-7) and np.all(q<=guard.upper+2e-7) and scene.check(q)['accepted'])
   checks.append(dict(path_index=i,endpoint_max_joint_distance_rad=gap,inset_m=inset,above_top_m=height,original_physical_ready=ready))
  # Ideal measured state at tick t is points[t-1]. At the endpoint it holds.
  count=0;first=None
  for tick in range(1,1001):
   count=count+1 if checks[min(tick-1,len(points)-1)]['original_physical_ready'] else 0
   if count>=3:first=tick;break
  r.update(nominal_waypoints=len(p['waypoints']),first_nominal_ready_path_index=next((x['path_index'] for x in checks if x['original_physical_ready']),None),ideal_one_waypoint_per_tick_handover_tick=first,original_maximum_ticks=240,ideal_nominal_schedule_within_budget=first is not None and first<=240,live_budget_feasibility='unproven',checks=checks)
 rows.append(r)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,supersedes_interpretation=str(old),correction='Waypoint count alone is not a runtime lower bound. Original handover requires measured endpoint tolerance plus geometry for three frames, not final waypoint index. Ideal timing assumes exact one-waypoint-per-tick tracking; real dynamics can differ.',rows=rows,source_sha256={str(p):sha(p) for p in [source,old,Path(__file__),S/'minimum_motion_lifecycle.py',S/'recontact_scene.py',S/'clearance_runtime.py']},training_ready=False,collector_integrated=False)
dest=W/'FRONT_ALTERNATIVE_REAR_LANDING_BUDGET_V2.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='checks'} for r in rows],indent=2))
