"""Full original80+56 audit inventory and new10 native coverage prerequisites.
Actual CLI/defaultoff/action/stop checks must be current. No simulation/run mkdir.
"""
from pathlib import Path
import sys,ast,json,hashlib,datetime
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w))
import recontact_run_contract as old
import loaded_edge_run_contract as new
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();stage=w/'staged_loaded_edge_coverage';sources={};checks=['ADAPTER_ACTUAL_CHECK.json','COLLECTOR_CONTRACT_CHECK.json','COLLECTOR_EXECUTION_CHECK.json','INDEPENDENT_RECORD_CHECK.json','DECISION_COVERAGE_CHECK.json','NATIVE_FILES_CHECK.json','SOURCE_CONTRACT_CHECK.json','ORIGINAL_MATH_CHECK.json','LEGACY_EXECUTION_CHECK.json','COMMAND_CHAIN_CHECK.json','DEPENDENCY_VERSION_CHECK.json']
for name in checks:
 path=stage/name;d=json.loads(path.read_text());assert d.get('passed',d.get('adapter_checks_passed')) is True,name
 for p,h in d['source_sha256'].items():assert sha(p)==h,(name,p)
 sources[str(path)]=sha(path)
v=json.loads((w/'LOADED_EDGE_AUDIT_VERSION_MAP.json').read_text());mapping=dict(v['modules']);mapping.update(audit_recontact_pose_self_clearance='audit_loaded_edge_self_clearance',audit_recontact_pose_task_optimality='audit_loaded_edge_task_optimality',audit_recontact_pose_loaded_execution='audit_loaded_edge_loaded_execution')
rename=lambda name:mapping.get(name.removesuffix('.py'),name.removesuffix('.py'))+'.py'
records=[]
for ep in sorted((w/'recontact_pose_groups_r1').glob('case_*/layout_*/frontal_bypass.json')):
 plan=json.loads(ep.read_text())['plan'];before=old.controls(plan);after=new.controls(plan);assert after==[rename(n) for n in before];records.append(dict(episode=ep.parent.name,original=before,versioned=after));sources[str(ep)]=sha(ep)
assert sum(len(x['original']) for x in records)==80 and len(new.ADDITIONAL)*8==56
assert new.ADDITIONAL==[rename(n) for n in old.ADDITIONAL]
for wait in [False,True]:assert new.primary(wait)==['audit_loaded_edge_coverage_live.py']+[rename(n) for n in old.primary(wait)]
used=set(new.ADDITIONAL+new.primary(True)+new.primary(False)+[n for r in records for n in r['versioned']]);assert used<=new.REPORTS.keys()
for script in used:
 path=w/script;tree=ast.parse(path.read_text());report,keys=new.REPORTS[script];assert any(isinstance(n,ast.Constant) and n.value==report for n in ast.walk(tree)),(script,report)
 sources[str(path)]=sha(path)
# Full same tasks/layouts/seed/budget/order; feature flag is sole CLI change.
p=json.loads((w/'recontact_pose_groups_r1/PROTOCOL.json').read_text());commands=[]
for item in p['commands']:
 args=item['args']+['--loaded-edge-coverage'];assert args[:-1]==item['args'];commands.append(dict(layout_id=item['layout_id'],tasks=item['tasks'],wait=item['wait']))
assert len(commands)==6 and sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
# Original runner/watch/closer control flow retained apart from declared names/flag.
replacements=dict(mapping, recontact_run_contract='loaded_edge_run_contract');reports=dict(v['reports']);reports.update({'RECONTACT_POSE_SELF_CLEARANCE_AUDIT.json':'LOADED_EDGE_SELF_CLEARANCE_AUDIT.json','RECONTACT_POSE_TASK_OPTIMALITY_AUDIT.json':'LOADED_EDGE_TASK_OPTIMALITY_AUDIT.json','RECONTACT_POSE_LOADED_EXECUTION_AUDIT.json':'LOADED_EDGE_LOADED_EXECUTION_AUDIT.json'})
for parent,child in [('run_recontact_pose_groups.py','run_loaded_edge_coverage_groups.py'),('watch_recontact_pose_audits.py','watch_loaded_edge_coverage_audits.py'),('close_recontact_pose_groups.py','close_loaded_edge_coverage_groups.py')]:
 text=(w/child).read_text()
 for a,b in replacements.items():text=text.replace(b,a)
 for a,b in reports.items():text=text.replace(b,a)
 text=text.replace(" and prov['args']['loaded_edge_coverage'] is True",'').replace(" and meta['loaded_edge_coverage'] is True",'').replace('当前有载边缘覆盖完整诊断','无载重接触完整诊断').replace('default-off loaded-edge flag enabled','default-off pose flag enabled')
 assert ast.dump(ast.parse(text),include_attributes=False)==ast.dump(ast.parse((w/parent).read_text()),include_attributes=False),child
 for path in [w/child,w/parent]:sources[str(path)]=sha(path)
for path in [Path(__file__),w/'loaded_edge_run_contract.py',w/'recontact_run_contract.py',w/'LOADED_EDGE_AUDIT_VERSION_MAP.json',w/'recontact_pose_groups_r1/PROTOCOL.json',w/'prepare_loaded_edge_coverage_groups.py']:sources[str(path)]=sha(path)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,current_preflight_checks=checks,commands=commands,original_control_invocations=80,additional_invocations=56,new_native_coverage_invocations=10,control_mapping=records,original_runner_watch_closer_ast_preserved=True,source_sha256=sources,physical_validation=False,training_ready=False)
(stage/'RUN_PROTOCOL_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS complete protocol',80,56,10)
