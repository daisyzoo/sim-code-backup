"""Distinguish endpoint feasibility from full nominal-path feasibility.
No candidate can be admitted by its best objective alone. This is offline
geometry only; measured tracking,240tick budget and contact remain unverified.
"""
from pathlib import Path
import json,sys,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_precise_parent_seed';sys.path[:0]=[str(w),str(repo)]
from audit_recontact_pose_events import EventAudit
src=w/'FLAT_FACE_RECONTACT_SCREEN.json';d=json.loads(src.read_text());assert d['complete'],'Wait for whole16 screen completion, do not treat partial as final';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert all(sha(Path(p))==h for p,h in d['source_sha256'].items());audit=EventAudit(repo,stage);rows=[]
for row in d['records']:
 name=row['episode'];layout=name.split('_')[1];ep=w/'precise_interior_groups_r1'/('case_'+layout)/name;events=json.loads((ep/'recontact_pose.json').read_text())['rows'];event=next(e for e in events if e['step']==row['step']);ctx=event['context'];q=np.array(ctx['current']);feasible=[x for x in row['attempts'] if x['accepted']];usable=[x for x in feasible if x['independent_path_geometry_passed']]
 out=dict(episode=name,step=row['step'],endpoint_feasible_attempts=len(feasible),path_feasible_attempts=len(usable),original_alignment_abs=row['original_alignment_abs'],best_path_feasible=min(usable,key=lambda a:a['objective']) if usable else None)
 if feasible and not usable:
  best=min(feasible,key=lambda a:a['objective']);end=np.array(best['candidate']);count=best['path_samples'];assert count==max(1,int(np.ceil(max(abs(end-q)/(audit.limits*.25)))));checks=[]
  for i in range(1,count+1):
   x=np.clip(q+(end-q)*i/count,audit.lo,audit.hi);g,_=audit.geometry(x,ctx['scene']);checks.append(g)
  bad=[(i+1,g) for i,g in enumerate(checks) if not g['accepted']];assert bad
  out.update(best_endpoint_only=best,path_failure_samples=len(bad),first_failure_waypoint=bad[0][0],first_failure=bad[0][1],min_active_above_top_mm=min(g['active_above_top_m'] for g in checks)*1000,min_hand_parcel_gap_mm=min(min(g['hand_parcel_gaps_m'].values()) for g in checks)*1000,min_elbow_gap_mm=min(g['elbow_gap_m'] for g in checks)*1000)
 rows.append(out);print(name,row['step'],'endpoint',len(feasible),'path',len(usable),out.get('min_active_above_top_mm'),flush=True)
report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=len(rows),endpoint_feasible_cases=sum(x['endpoint_feasible_attempts']>0 for x in rows),path_feasible_cases=sum(x['path_feasible_attempts']>0 for x in rows),rows=rows,source_sha256={str(p):sha(p) for p in [src,Path(__file__),w/'audit_recontact_pose_events.py']},physical_validation=False,training_ready=False);(w/'FLAT_FACE_PATH_FINDINGS.json').write_text(json.dumps(report,indent=2))
