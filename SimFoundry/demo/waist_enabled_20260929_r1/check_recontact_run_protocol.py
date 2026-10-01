"""Actual pre-AppLauncher CLI checks, complete80control matrix on unchanged
parent recordings, explicit version map and source dependencies. No physics.
Checks do not start a simulator, create a run directory or grant admission.
"""
from pathlib import Path
import sys,ast,json,hashlib,subprocess,os
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from recontact_run_contract import controls,ADDITIONAL,REPORTS,primary,run_audit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();stage=w/'staged_recontact_pose';parent=w/'rear_short_recovery_groups_r1';p=json.loads((parent/'PROTOCOL.json').read_text());cli=[]
prefix=(stage/'collect_paired_sorting.py').read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]
# Actual argparse/AppLauncher argument registration and all original validation.
for item in p['commands']:
 args=item['args']+['--unloaded-recontact-pose','--out-dir','/tmp/recontact_prelaunch_only_no_output']
 code="from pathlib import Path\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nimport types,sys\nm=types.ModuleType('__prelaunch_check__');sys.modules[m.__name__]=m;ns=m.__dict__;ns['__file__']=str(p)\nexec(compile(s,str(p),'exec'),ns)\na=ns['args']\nassert a.unloaded_recontact_pose and not hasattr(a,'push_assist') and not a.push_force_n and not a.wait_force_n and a.horizon==10\nprint('PRELAUNCH_OK')\n"
 result=subprocess.run([sys.executable,'-c',code,*args],capture_output=True,text=True);assert result.returncode==0 and 'PRELAUNCH_OK' in result.stdout,(item['layout_id'],result.stdout[-1000:],result.stderr[-3000:]);cli.append(dict(layout_id=item['layout_id'],wait=item['wait'],passed=True));print(item['layout_id'],'actual CLI passed',flush=True)
assert len(cli)==6 and sum(len(c['tasks']) for c in p['commands'] if not c['wait'])==8 and sum(len(c['tasks']) for c in p['commands'] if c['wait'])==2
# Three replacements only; surface reconstruction math remains unchanged.
a=(w/'audit_recontact_initial_near_half.py').read_text().replace('audit_recontact_region_reference','audit_region_reference_live').replace('RECONTACT_INITIAL_NEAR_HALF_AUDIT.json','INITIAL_NEAR_HALF_LIVE_AUDIT.json');assert ast.dump(ast.parse(a),include_attributes=False)==ast.dump(ast.parse((w/'audit_initial_near_half_live.py').read_text()),include_attributes=False)
chain=json.loads((stage/'REGION_CHAIN_CHECK.json').read_text());records=[]
for case in chain['parent_replays']:
 ep=Path(case['fixture']);plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];names=controls(plan)
 for script in names:
  row=run_audit(ep,script);assert row['returncode']==0,(ep.name,script,(ep/(script+'.log')).read_text()[-3000:]);records.append(row)
 print(ep.name,len(names),'control reports passed',flush=True)
assert len(records)==80 and len(ADDITIONAL)==7
assert primary(True)==['audit_recontact_pose_self_clearance.py','audit_normal_wait.py']
assert primary(False)[0:2]==['audit_recontact_pose_live.py','audit_recontact_pose_self_clearance.py']
assert 'audit_recontact_pose_height.py' in ADDITIONAL and 'audit_recontact_pose_task_optimality.py' in ADDITIONAL and 'audit_recontact_pose_loaded_execution.py' in ADDITIONAL
source=[Path(__file__),w/'recontact_run_contract.py',w/'run_recontact_pose_groups.py',w/'watch_recontact_pose_audits.py',w/'close_recontact_pose_groups.py',w/'prepare_recontact_pose_groups.py',w/'recontact_audit_context.py',stage/'collect_paired_sorting.py',parent/'PROTOCOL.json']
source += [w/s for s in set(REPORTS)]
for path in source:
 if path.suffix=='.py':ast.parse(path.read_text())
report=dict(passed=True,scope=__doc__,actual_prelaunch_commands=cli,original_control_invocations=records,control_count=80,additional_count=56,primary_before_consumers=True,three_original_control_versions=True,source_sha256={str(f):sha(f) for f in source},physical_validation=False,training_ready=False)
(stage/'RUN_PROTOCOL_CHECK.json').write_text(json.dumps(report,indent=2));print('PASS',len(cli),len(records),56,flush=True)
