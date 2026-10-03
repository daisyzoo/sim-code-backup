"""Prepare full paired1mm comparison drivers; no launch or admission.
Retain all cases and audit gates. Parent full204 closure is required at preflight.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'front_drive_1mm_preparation_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
family=json.loads((W/'FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json').read_text());check=json.loads((P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json').read_text());assert check['passed'] and check['expected_audits']==204
replacements=family['global_replacements']+[
 ('front_corridor_midpoint_physical_preparation_r1','front_drive_1mm_preparation_r2'),
 ('front_corridor_midpoint_physical_r1','front_drive_1mm_physical_r1'),
 ('front_corridor_midpoint_physical','front_drive_1mm_physical'),
 ('watch_front_corridor_midpoint_numeric_reviews','watch_front_drive_1mm_numeric_reviews'),
 ('review_front_corridor_midpoint_incomplete_episode','review_front_drive_1mm_incomplete_episode'),
 ('FRONT_CORRIDOR_MIDPOINT_INCOMPLETE','FRONT_DRIVE_1MM_INCOMPLETE'),
 ('FRONT_CORRIDOR_MIDPOINT_REVIEW','FRONT_DRIVE_1MM_REVIEW')]
def rename(s):
 for a,b in replacements:s=s.replace(a,b)
 return s
def write(parent,text):
 dest=W/rename(parent.name);assert dest!=parent and not dest.exists();ast.parse(text);dest.write_text(text);records.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest)))
for n in ['review_front_corridor_midpoint_stage_episode.py','review_front_corridor_midpoint_incomplete_episode.py','watch_front_corridor_midpoint_numeric_reviews.py','watch_front_corridor_midpoint_physical_audits.py','close_front_corridor_midpoint_physical.py','queue_front_corridor_midpoint_physical_closure.py']:
 p=W/n;s=rename(p.read_text())
 if n=='close_front_corridor_midpoint_physical.py':s=s.replace('front_z_priority_physical_r1','front_corridor_midpoint_physical_r1').replace('RESULT_WITH_ROTATION_SUPPLEMENT.json','RESULT.json').replace('midpoint_route_against_matched_loaded_z_parent','existing_front_drive1mm_against_midpoint2mm_parent')
 write(p,s)
p=W/'run_front_corridor_midpoint_physical.py';s=rename(p.read_text());s=s.replace("PREVIOUS=W/'front_z_priority_physical_r1'","PREVIOUS=W/'front_corridor_midpoint_physical_r1'")
start=s.index('CHECKS=');end=s.index('_cache={}',start)
s=s[:start]+"""CHECKS=['staged_front_drive_1mm/CLI_PARAMETER_CHECK.json','front_drive_1mm_preparation_r2/CONFIGURATION_SOURCE_AUDIT_CHECK.json']
MANIFESTS=['FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json','FRONT_CORRIDOR_MIDPOINT_SOURCE_CONTRACT_PREPARATION.json','FRONT_DRIVE_1MM_PHYSICAL_PREPARATION.json']
"""+s[end:]
s=s.replace("expected+=['--front-corridor-midpoint-replan']","expected[expected.index('--front-cop-drive-step-m')+1]='.001'")
s=s.replace("W/'staged_closed_peak_trial/TRIAL_PROFILE.json'","P/'TRIAL_PROFILE.json'")
s=s.replace("W/'FRONT_CORRIDOR_MIDPOINT_AUDIT_DEPENDENCIES_CHECK.json'","P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json'")
s=s.replace("assert not deps['missing'] and deps['conditions']==10 and deps['expected_audit_invocations']==204","assert deps['passed'] and deps['condition_count']==10 and deps['expected_audits']==204")
start=s.index('def preflight():');end=s.index('def main(out,check_only=False):',start)
s=s[:start]+"""def preflight():
 plan=configuration();closed_path=PREVIOUS/'RESULT.json';parent=json.loads(closed_path.read_text())
 assert parent['status']=='diagnostic_complete_failures_retained' and parent['conditions']==10 and parent['audit_invocations']==204
 assert parent['failed_audit_invocations']==[] and parent['training_ready'] is False and parent['model_goal_achieved'] is False
 bound(parent['source_sha256']);assert parent['closer_sha256']==sha(W/'close_front_corridor_midpoint_physical.py')
 protocol=json.loads((PREVIOUS/'PROTOCOL.json').read_text());audit=json.loads((PREVIOUS/'AUDIT_STATUS.json').read_text());bound(protocol['frozen_files_sha256'])
 assert audit['status']=='complete' and len(audit['rows'])==204
 for pid in [protocol['producer_pid'],audit['pid']]:
  path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z',('previous process live',pid)
 records=json.loads((PREVIOUS/'COLLECTION_EXECUTION.json').read_text());assert len(records)==10
 for row in records:bound(row['source_sha256'])
 visual=json.loads((PREVIOUS/'NUMERIC_VISUAL_SUMMARY.json').read_text());assert visual['actual_reviews']==10 and len(visual['rows'])==10;bound(visual['source_sha256'])
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),configuration_check_sha256=sha(P/'CONFIGURATION_CHECK.json'),matched_parent_closure_sha256=sha(closed_path),storage=storage,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan

"""+s[end:]
s=s.replace("PREVIOUS/'RESULT_WITH_ROTATION_SUPPLEMENT.json'","PREVIOUS/'RESULT.json'")
s=s.replace('Matched midpoint-route physical diagnostic','Matched declared1mm-front-drive physical diagnostic')
write(p,s)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=records,replacements=replacements,plan_sha256=sha(P/'PLAN.json'),generator_sha256=sha(__file__),source_sha256={str(p):sha(p) for p in [P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json',W/'FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json',W/'FRONT_DRIVE_1MM_HISTORICAL_PROPOSAL_BUDGET.json']},physics_started=False,training_ready=False)
with (W/'FRONT_DRIVE_1MM_PHYSICAL_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(files=len(records),conditions=10,physics_started=False)))
