"""Nominal withdrawal/relanding geometry from actual loaded configurations.
Straight withdrawal must never deepen the original measured plane penetration;
all nominal hand-other, independent elbow, table and joint checks stay enforced.
Unloaded segment uses original4mm plane/10mm hand-other check. This is a CPU
path screen, not measured unloading, real motion, physical COP or force proof.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from minimum_motion_recontact import lift_endpoint,interpolate
from audit_minimum_motion_plan_reentrant import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();src=W/'FRONT_WRENCH_RELANDING_ENDPOINT_PROBE.json';data=json.loads(src.read_text());assert data['status']=='complete';g=ClearanceGuard(ROOT,S);ind=PlanAudit(ROOT,S);rows=[];out=W/'FRONT_WRENCH_RELANDING_PATH_PROBE.json';assert not out.exists()
sources={str(p):sha(p) for p in [Path(__file__),src,S/'minimum_motion_recontact.py',S/'recontact_scene.py',S/'clearance_runtime.py',W/'audit_minimum_motion_plan_reentrant.py']};sources.update(g.model.source_sha256)
def save(status,**kw):
 tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,simulation_started=False,collector_integrated=False,training_ready=False,**kw),indent=2));tmp.replace(out)
try:
 save('running')
 for record in data['records']:
  if not record['selected']:continue
  scene=RecontactScene(g,**record['observed_scene']);q=np.array(record['actual_current_q']);_,start=ind.geometry(q,scene.record());startheight=float(start['point'][2]-scene.core[2]/2);r=dict(episode=record['episode'],step=record['step'],actual_initial_plane_height_m=startheight,lift_options=[]);rows.append(r)
  for height in [.06,.08]:
   save('running',current_episode=record['episode'],height=height);lift=lift_endpoint(scene,q,height);entry=dict(height_m=height,lift_endpoint=lift,withdrawal=None,relocation=[]);r['lift_options'].append(entry)
   if not lift['accepted']:save('running');continue
   end=np.array(lift['candidate']);points,ignored=ind.path([q,end],scene.record());checks=[];prior=startheight
   for value in points:
    v=np.array(value);gg,d=ind.geometry(v,scene.record());h=float(d['point'][2]-scene.core[2]/2);table=float(min(ind.hand.minz(v,'left'),ind.hand.minz(v,'right'))-.75);accepted=bool(h>=startheight-2e-7 and h>=prior-2e-7 and min(gg['hand_parcel_gaps_m'].values())>=.01-2e-7 and gg['elbow_gap_m']>=.005-2e-7 and table>=.005-2e-7 and np.all(v>=g.lower-2e-7) and np.all(v<=g.upper+2e-7));checks.append(dict(accepted=accepted,plane_height_m=h,table_clearance_m=table,independent_geometry=gg));prior=h
   withdrawal=bool(checks and all(c['accepted'] for c in checks));entry['withdrawal']=dict(accepted=withdrawal,nominal_waypoints=points,checks=checks)
   if withdrawal:
    for condition in record['conditions']:
     candidates=[]
     for attempt in condition['attempts']:
      if not attempt['accepted']:continue
      endpoint=np.array(attempt['candidate_q']);path=interpolate(scene,[end,endpoint]);indpoints,ichecks=ind.path([end,endpoint],scene.record());assert np.max(abs(np.array(indpoints)-np.array(path['waypoints'])))<1e-12
      valid=bool(path['accepted'] and all(c['accepted'] and c['elbow_gap_m']>=.005-2e-7 for c in ichecks));candidates.append(dict(endpoint_seed=attempt['seed'],accepted=valid,unloaded_waypoints=len(indpoints),nominal_total_with_withdrawal=len(points)+len(indpoints),unloaded_path=path,independent_checks=ichecks,endpoint_q=endpoint.tolist()))
     entry['relocation'].append(dict(condition=condition['name'],candidates=candidates,accepted_paths=sum(c['accepted'] for c in candidates)))
   save('running');print(record['episode'],'height',height,'withdrawal',withdrawal,'paths',[(x['condition'],x['accepted_paths']) for x in entry['relocation']],flush=True)
 save('complete')
except Exception as e:save('failed',error=repr(e));raise
