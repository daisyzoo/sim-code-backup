"""Execute all6 actual pre-AppLauncher command validations and compare audit inventory.
No simulator is launched. Inventory parity is not a pass of real task/audits.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,ast
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)];stage=w/'staged_recontact_interior';parent=w/'recontact_pose_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
import recontact_run_contract as old
import interior_run_contract as new
mapping=json.loads((w/'INTERIOR_AUDIT_VERSION_MAP.json').read_text())
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
protocol=json.loads((parent/'PROTOCOL.json').read_text());cli=[];control=[]
for item in protocol['commands']:
 args=item['args']+['--recontact-interior-preference','--out-dir','/tmp/interior_prelaunch_only_no_output']
 code="from pathlib import Path\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nimport types,sys\nm=types.ModuleType('__interior_prelaunch__');sys.modules[m.__name__]=m;ns=m.__dict__;ns['__file__']=str(p)\nexec(compile(s,str(p),'exec'),ns)\na=ns['args']\nassert a.recontact_interior_preference and a.unloaded_recontact_pose and not hasattr(a,'push_assist') and not a.push_force_n and not a.wait_force_n and a.horizon==10\nprint('PRELAUNCH_OK')\n"
 p=subprocess.run([sys.executable,'-c',code,*args],capture_output=True,text=True);assert p.returncode==0 and 'PRELAUNCH_OK' in p.stdout,(item['layout_id'],p.stdout[-1200:],p.stderr[-2500:]);cli.append(dict(layout_id=item['layout_id'],wait=item['wait'],passed=True));print(item['layout_id'],'actual CLI passed',flush=True)
 for task in item['tasks']:
  if item['wait']:continue
  ep=parent/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];expected=[rename(n) for n in old.controls(plan)];assert new.controls(plan)==expected;control+=expected
assert len(cli)==6 and len(control)==80 and len(new.ADDITIONAL)*8==56
assert new.ADDITIONAL==[rename(n) for n in old.ADDITIONAL]
for wait in [True,False]:assert new.primary(wait)==[rename(n) for n in old.primary(wait)]
assert new.REPORTS=={rename(k):(rename(v[0]),v[1]) for k,v in old.REPORTS.items()}
for script in set(control)|set(new.ADDITIONAL)|set(new.primary(True))|set(new.primary(False)):assert (w/script).is_file()
drivers={'recontact_run_contract.py':'interior_run_contract.py','run_recontact_pose_groups.py':'run_recontact_interior_groups.py','watch_recontact_pose_audits.py':'watch_recontact_interior_audits.py','close_recontact_pose_groups.py':'close_recontact_interior_groups.py'}
for a,b in drivers.items():
 expected=rename((w/a).read_text()).replace('recontact_run_contract','interior_run_contract')
 if a.startswith(('run_','close_')):expected=expected.replace("assert prov['args']['unloaded_recontact_pose'] is True", "assert prov['args']['recontact_interior_preference'] is True and prov['args']['unloaded_recontact_pose'] is True")
 assert ast.dump(ast.parse(expected),include_attributes=False)==ast.dump(ast.parse((w/b).read_text()),include_attributes=False),b
sources=[Path(__file__),stage/'collect_paired_sorting.py',parent/'PROTOCOL.json',w/'INTERIOR_AUDIT_VERSION_MAP.json',w/'prepare_recontact_interior_groups.py',*[w/n for n in drivers],*[w/n for n in drivers.values()],*[w/n for n in new.REPORTS]]
out=dict(passed=True,scope=__doc__,actual_prelaunch_commands=cli,original_control_count=len(control),additional_count=56,complete_condition_count=10,unchanged_driver_control_flow=True,source_sha256={str(p):sha(p) for p in sources},physical_validation=False,training_ready=False);(stage/'RUN_PROTOCOL_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS6CLI80controls56extra10conditions',flush=True)
