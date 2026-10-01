"""Offline first-command guard check at all16 actual recovery starts.
Original proposal must exactly reproduce actual recorded command. Candidate
waypoints are a geometry screen only; no subsequent physics/tracking assumed.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_precise_parent_seed';sys.path[:0]=[str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from recontact_tracking import propose
from audit_recontact_pose_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();paths=json.loads((w/'MINIMUM_MOTION_PATH_FINDINGS.json').read_text());lifts=json.loads((w/'MINIMUM_MOTION_LIFT_PATH_SCREEN.json').read_text());assert lifts['complete'];sources={}
for report in [paths,lifts]:
 for p,h in report['source_sha256'].items():assert sha(p)==h;sources[p]=h
for n in ['MINIMUM_MOTION_PATH_FINDINGS.json','MINIMUM_MOTION_LIFT_PATH_SCREEN.json']:sources[str(w/n)]=sha(w/n)
guard=ClearanceGuard(repo,stage);audit=EventAudit(repo,stage);rows=[]
for row in paths['rows']:
 name=row['episode'];ep=w/'precise_interior_groups_r1'/('case_'+name.split('_')[1])/name;events=json.loads((ep/'recontact_pose.json').read_text())['rows'];e=next(e for e in events if e['step']==row['step']);ctx=e['context'];q=np.array(ctx['current']);scene=RecontactScene(guard,**ctx['scene'])
 if row['best_path_feasible']:
  nodes=[q,np.array(row['best_path_feasible']['candidate'])];kind='straight'
 else:
  options=next(r['attempts'] for r in lifts['records'] if r['episode']==name and r['step']==row['step']);valid=[a for a in options if a['path_geometry_passed']];assert valid;best=min(valid,key=lambda a:a['total_waypoints']);nodes=[q,np.array(best['start_lift']['candidate']),np.array(best['end_lift']['candidate']),np.array(row['best_endpoint_only']['candidate'])];kind='raised'
 waypoints=[]
 for a,b in zip(nodes,nodes[1:]):
  count=max(1,int(np.ceil(max(abs(b-a)/(guard.limits*.25)))));waypoints.extend([np.clip(a+(b-a)*i/count,guard.lower,guard.upper) for i in range(1,count+1)])
 assert all(audit.geometry(x,ctx['scene'])[0]['accepted'] for x in waypoints)
 def call(waypoint):return propose(enabled=True,selected=ctx['selected'],mode='top_cross',recontacts=ctx['recontacts'],observed_load_n=ctx['observed_load_n'],filtered_load_n=ctx['filtered_load_n'],current=q,previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],waypoint=waypoint,decay=e['proposal']['decay'],guard=guard,scene_check=scene.check)
 old,record=call(e['proposal']['waypoint']);assert old is not None and np.array_equal(old,np.array(e['command'],dtype=np.float32));assert record==e['proposal']
 index=1 if max(abs(q-waypoints[0]))<=.003 and len(waypoints)>1 else 0
 command,new=call(waypoints[index]);out=dict(episode=name,step=row['step'],path_kind=kind,nominal_waypoints=len(waypoints),original_proposal_exact=True,first_command_accepted=command is not None,first_proposal=new,real_tracking_verified=False,physical_validation=False);rows.append(out);print(name,row['step'],kind,len(waypoints),'first',command is not None,new['reason'],flush=True)
for p in [Path(__file__),stage/'recontact_tracking.py',stage/'recontact_scene.py',stage/'clearance_runtime.py']:sources[str(p)]=sha(p)
out=dict(scope=__doc__,cases=len(rows),original_exact=sum(r['original_proposal_exact'] for r in rows),first_command_passed=sum(r['first_command_accepted'] for r in rows),rows=rows,source_sha256=sources,training_ready=False);(w/'MINIMUM_MOTION_FIRST_COMMAND_CHECK.json').write_text(json.dumps(out,indent=2))
