"""Prepare full8push2wait post-commit comparison, original2mm parent and214 audits.
Matched parent original failure remains, with its separate verified supplement.
New physics requires original storage/GPU gates; no launch in this generator.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'rear_waypoint_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
checks=[P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json',P/'LOADED_AUDIT_V3_CHECK.json']
for p in checks:
 d=json.loads(p.read_text());assert d['passed']
 for name,h in d['source_sha256'].items():assert sha(name)==h,name
replacements=[('front_drive_1mm_v2_stage_run_contract','rear_waypoint_v3_stage_run_contract'),('front_drive_1mm_v2','rear_waypoint_v2'),('FRONT_DRIVE_1MM_V2','REAR_WAYPOINT_V2'),('staged_front_drive_1mm','staged_rear_waypoint_reconciliation'),('front_drive_1mm_preparation_r2','rear_waypoint_preparation_r1'),('front_drive_1mm_physical_r1','rear_waypoint_physical_r1'),('run_front_drive_1mm_rigid_parent_v2','run_rear_waypoint_physical'),('front_drive_1mm_physical','rear_waypoint_physical'),('watch_front_drive_1mm_numeric_reviews','watch_rear_waypoint_numeric_reviews'),('review_front_drive_1mm_incomplete_episode','review_rear_waypoint_incomplete_episode'),('FRONT_DRIVE_1MM_INCOMPLETE','REAR_WAYPOINT_INCOMPLETE'),('FRONT_DRIVE_1MM_REVIEW','REAR_WAYPOINT_REVIEW')]
def rename(s):
 for a,b in replacements:s=s.replace(a,b)
 return s
def write(p,s):
 dst=W/rename(p.name);assert not dst.exists();ast.parse(s)
 with dst.open('x') as f:f.write(s)
 records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(dst),sha256=sha(dst)))
for name in ['review_front_drive_1mm_v2_stage_episode.py','review_front_drive_1mm_incomplete_episode.py','watch_front_drive_1mm_numeric_reviews.py','watch_front_drive_1mm_physical_audits.py','close_front_drive_1mm_physical.py','queue_front_drive_1mm_physical_closure.py']:
 p=W/name;s=rename(p.read_text())
 if name=='watch_front_drive_1mm_physical_audits.py':s=s.replace('len(all_rows)==204','len(all_rows)==214')
 if name=='queue_front_drive_1mm_physical_closure.py':s=s.replace("len(audit['rows'])==204","len(audit['rows'])==214").replace('audit_rows=204','audit_rows=214')
 if name=='close_front_drive_1mm_physical.py':s=s.replace('len(all_rows)==204','len(all_rows)==214').replace('existing_front_drive1mm_against_midpoint2mm_parent','post_commit_rear_cursor_against_midpoint2mm_parent')
 write(p,s)
p=W/'run_front_drive_1mm_rigid_parent_v2.py';s=rename(p.read_text());start=s.index('CHECKS=');end=s.index('_cache={}',start)
s=s[:start]+"""CHECKS=['staged_rear_waypoint_reconciliation/COLLECTOR_WIRING_CHECK_V2.json','rear_waypoint_preparation_r1/CONFIGURATION_SOURCE_AUDIT_CHECK.json','rear_waypoint_preparation_r1/LOADED_AUDIT_V3_CHECK.json']
MANIFESTS=['REAR_WAYPOINT_V2_AUDIT_FAMILY_PREPARATION.json','REAR_WAYPOINT_LOADED_AUDIT_V3_PREPARATION.json','REAR_WAYPOINT_PHYSICAL_PREPARATION.json']
"""+s[end:]
s=s.replace("expected[expected.index('--front-cop-drive-step-m')+1]='.001'","expected+=['--rear-waypoint-reconciliation']")
s=s.replace("for flag in ['--front-corridor-midpoint-replan'","for flag in ['--rear-waypoint-reconciliation','--front-corridor-midpoint-replan'")
s=s.replace("for key in ['front_corridor_midpoint_replan'","for key in ['rear_waypoint_reconciliation','front_corridor_midpoint_replan'")
s=s.replace("P/'TRIAL_PROFILE.json'","W/'staged_closed_peak_trial/TRIAL_PROFILE.json'")
s=s.replace("bound(family['dependency_sha256'])","bound(family['source_sha256']);bound(json.loads((P/'AUDIT_DEPENDENCIES.json').read_text())['source_sha256'])\n supplement=json.loads((W/MANIFESTS[1]).read_text());bound(supplement['source_sha256'])\n for row in supplement['adapters']:assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256']")
s=s.replace("deps['expected_audits']==204","deps['expected_audits']==214")
s=s.replace('original_audits=194,new_execution_audits=10,total_audits=204','original_audits=204,new_commit_audits=10,total_audits=214')
s=s.replace('RIGID_PARENT_V2_CONFIGURATION_CHECK.json','CONFIGURATION_CHECK.json').replace('RIGID_PARENT_V2_LAUNCH_PREFLIGHT.json','LAUNCH_PREFLIGHT.json')
s=s.replace('Matched declared1mm-front-drive physical diagnostic','Matched post-commit rear-cursor physical diagnostic').replace('All194 original audits plus10 actual-command audits','All204 original audits plus10 complete commit-log audits')
write(p,s)
queue=[Path(r['path']) for r in records]+[Path(r['path']) for r in json.loads((W/MANIFEST if False else W/'REAR_WAYPOINT_V2_AUDIT_FAMILY_PREPARATION.json').read_text())['adapters']]+[W/'rear_waypoint_v3_stage_run_contract.py',W/'audit_rear_waypoint_v3_stage_pose_loaded_execution.py',W/'audit_rear_waypoint_v2_commit.py'];seen=set();missing=[]
while queue:
 p=queue.pop()
 if p in seen:continue
 seen.add(p)
 for n in ast.walk(ast.parse(p.read_text())):
  names=[]
  if isinstance(n,ast.ImportFrom) and n.module and '.' not in n.module:names=[n.module+'.py']
  elif isinstance(n,ast.Import):names=[a.name+'.py' for a in n.names if '.' not in a.name]
  elif isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.endswith('.py') and '/' not in n.value:names=[n.value]
  for name in names:
   candidates=[W/name,W/'staged_rear_waypoint_reconciliation'/name,W/'rear_waypoint_reconciliation_draft_r1'/name]
   found=next((q for q in candidates if q.is_file()),None)
   if found:queue.append(found)
   elif 'rear_waypoint' in name:missing.append(name)
assert not missing,missing
with (P/'AUDIT_DEPENDENCIES.json').open('x') as f:json.dump(dict(source_sha256={str(p):sha(p) for p in sorted(seen)},missing=missing,training_ready=False),f,indent=2)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=records,replacements=replacements,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'AUDIT_DEPENDENCIES.json',*checks]},physics_started=False,training_ready=False)
with (W/'REAR_WAYPOINT_PHYSICAL_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(dict(files=len(records),dependencies=len(seen),missing=missing,physics_started=False))
