"""Prepare unchanged full eight-push/two-wait comparison, adding midpoint flag only.
No physics launch, no automatic data admission, no failed-condition retry.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;S=W/'staged_front_corridor_midpoint_integrated';P=W/'front_corridor_midpoint_physical_preparation_r1';assert not P.exists();P.mkdir();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
parent=W/'front_z_priority_physical_r1/PROTOCOL.json';old=json.loads(parent.read_text())['plan'];commands=[]
for item in old['commands']:
 args=list(item['args']);args[args.index('--out-dir')+1]=str(P/f"case_{item['layout_id']}");args.append('--front-corridor-midpoint-replan');commands.append(dict(item,args=args))
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),groups=old['groups'],commands=commands,parent_protocol=str(parent),parent_protocol_sha256=sha(parent),parent_run=str(parent.parent),comparison='midpoint_route_against_same_loaded_z_parent',scope=__doc__,simulation_started=False,training_ready=False)
(P/'PLAN.json').write_text(json.dumps(plan,indent=2))
def rename(s):return s.replace('staged_front_loaded_z_priority','staged_front_corridor_midpoint_integrated').replace('front_z_priority','front_corridor_midpoint').replace('FRONT_Z_PRIORITY','FRONT_CORRIDOR_MIDPOINT')
def write(parent,name,s):
 dest=W/name;assert not dest.exists();ast.parse(s);dest.write_text(s);records.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest)))
for name in ['review_front_z_priority_stage_episode.py','review_front_z_priority_incomplete_episode.py','watch_front_z_priority_numeric_reviews.py','watch_front_z_priority_physical_audits.py','close_front_z_priority_physical.py','queue_front_z_priority_physical_closure.py']:
 p=W/name;s=rename(p.read_text())
 if name=='close_front_z_priority_physical.py':s=s.replace('front_initial_physical_r1','front_z_priority_physical_r1').replace('RESULT_WITH_REGION_SUPPLEMENT.json','RESULT_WITH_ROTATION_SUPPLEMENT.json').replace('loaded_z_priority_against_matched_uncapped_first_center_parent','midpoint_route_against_matched_loaded_z_parent')
 write(p,rename(name),s)
p=W/'run_front_z_priority_physical.py';s=rename(p.read_text());s=s.replace("PREVIOUS=W/'front_initial_physical_r1'","PREVIOUS=W/'front_z_priority_physical_r1'")
start=s.index('CHECKS=');end=s.index('_cache={}',start)
s=s[:start]+'''CHECKS=['staged_front_corridor_midpoint_integrated/COLLECTOR_WIRING_CHECK.json','staged_front_corridor_midpoint_integrated/INDEPENDENT_RECORD_CHECK.json','staged_front_corridor_midpoint_integrated/CONTINUOUS_OBSERVATION_CHECK.json','staged_front_corridor_midpoint_integrated/CONTINUOUS_COP_CHECK.json','staged_front_corridor_midpoint_integrated/UPSTREAM_JOINT_CHAIN_CHECK.json','FRONT_CORRIDOR_MIDPOINT_SOURCE_CONTRACT_CHECK.json','FRONT_CORRIDOR_MIDPOINT_AUDIT_DEPENDENCIES_CHECK.json','FRONT_CORRIDOR_MIDPOINT_COMMAND_BRIDGE_CHECK.json','FRONT_CORRIDOR_MIDPOINT_INTEGRATION_PROGRESS.json']
MANIFESTS=['FRONT_CORRIDOR_MIDPOINT_AUDIT_FAMILY_PREPARATION.json','FRONT_CORRIDOR_MIDPOINT_SOURCE_CONTRACT_PREPARATION.json','FRONT_CORRIDOR_MIDPOINT_PHYSICAL_PREPARATION.json']
'''+s[end:]
s=s.replace("expected+=['--front-loaded-z-priority']","expected+=['--front-corridor-midpoint-replan']")
s=s.replace("for flag in ['--front-loaded-z-priority'","for flag in ['--front-corridor-midpoint-replan','--front-loaded-z-priority'")
s=s.replace("for key in ['front_loaded_z_priority'","for key in ['front_corridor_midpoint_replan','front_loaded_z_priority'")
s=s.replace("prep=json.loads((S/'VALIDATED_PREPARATION.json').read_text());bound(prep['source_sha256'])","prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());bound(prep['source_sha256']);bound({str(S/n):h for n,h in prep['stage_sha256'].items()})")
start=s.index('def preflight():');end=s.index('def main(out,check_only=False):',start)
s=s[:start]+'''def preflight():
 plan=configuration()
 from close_front_z_priority_rotation_supplements import inspect as verify_closed_parent
 checked=verify_closed_parent();closed_path=PREVIOUS/'RESULT_WITH_ROTATION_SUPPLEMENT.json';parent=json.loads(closed_path.read_text())
 assert {k:v for k,v in parent.items() if k!='created_at_utc'}=={k:v for k,v in checked.items() if k!='created_at_utc'}
 bound(parent['source_sha256']);assert not parent['unresolved_audits'] and not parent['training_ready']
 protocol=json.loads((PREVIOUS/'PROTOCOL.json').read_text());audit=json.loads((PREVIOUS/'AUDIT_STATUS.json').read_text());bound(protocol['frozen_files_sha256'])
 for pid in [protocol['producer_pid'],audit['pid']]:
  path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z',('previous process live',pid)
 records=json.loads((PREVIOUS/'COLLECTION_EXECUTION.json').read_text());assert len(records)==10
 for r in records:bound(r['source_sha256'])
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),configuration_check_sha256=sha(P/'CONFIGURATION_CHECK.json'),matched_parent_closure_sha256=sha(closed_path),storage=storage,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan

'''+s[end:]
s=s.replace("PREVIOUS/'RESULT_WITH_REGION_SUPPLEMENT.json'","PREVIOUS/'RESULT_WITH_ROTATION_SUPPLEMENT.json'")
s=s.replace('Matched uncapped loaded-Z physical diagnostic','Matched midpoint-route physical diagnostic')
write(p,'run_front_corridor_midpoint_physical.py',s)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,plan_sha256=sha(P/'PLAN.json'),files=records,generator_sha256=sha(__file__),source_sha256={str(parent):sha(parent),str(W/'close_front_z_priority_rotation_supplements.py'):sha(W/'close_front_z_priority_rotation_supplements.py')},physics_started=False,training_ready=False)
with (W/'FRONT_CORRIDOR_MIDPOINT_PHYSICAL_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(conditions=sum(len(c['tasks']) for c in commands),files=len(records),physics_started=False)))
