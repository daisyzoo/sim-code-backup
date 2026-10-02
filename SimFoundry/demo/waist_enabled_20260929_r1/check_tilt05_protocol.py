"""Same complete8push2wait and audit inventory; internal0.03->0.05 only.
No simulator initialized. New full experiment remains forbidden until parent
is fully closed and its frozen sources/independent checks still match.
"""
from pathlib import Path
import ast,json,sys,subprocess,hashlib,os,copy,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)];stage=w/'staged_box_inward_correction';parent=w/'box_inward_groups_r1';run=w/'tilt05_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
import box_inward_run_contract as old
import tilt05_run_contract as new
renames={'box_inward_run_contract':'tilt05_run_contract','audit_micro_clearance_live.py':'audit_tilt05_micro_clearance_live.py','audit_box_inward_pose_height.py':'audit_tilt05_box_inward_pose_height.py'}
def rename(s):
 for a,b in renames.items():s=s.replace(a,b)
 return s
protocol=json.loads((parent/'PROTOCOL.json').read_text());commands=copy.deepcopy(protocol['commands'])
for before,c in zip(protocol['commands'],commands):
 c['args']=[v.replace(str(parent),str(run)) for v in c['args']];i=c['args'].index('--expert-top-tilt-recontact-rad')+1;assert float(c['args'][i])==.03;c['args'][i]='.05'
 restored=[v.replace(str(run),str(parent)) for v in c['args']];restored[i]=before['args'][i];assert restored==before['args']
assert len(commands)==6 and sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
control=[]
# Same declared layouts; complete parent plans from preceding identical inventory.
for c in commands:
 if c['wait']:continue
 for task in c['tasks']:
  ep=w/'box_entry_lift_groups_r1'/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];assert new.controls(plan)==[rename(n) for n in old.controls(plan)];control.extend(new.controls(plan))
assert len(control)==80 and len(new.ADDITIONAL)*8==56
assert new.ADDITIONAL==[rename(n) for n in old.ADDITIONAL]
for wait in [True,False]:assert new.primary(wait)==[rename(n) for n in old.primary(wait)]
assert new.REPORTS=={rename(k):(v[0],v[1]) for k,v in old.REPORTS.items()}
files=[Path(__file__),parent/'PROTOCOL.json',stage/'collect_paired_sorting.py',w/'tilt05_diagnostic_contract.py',w/'TILT05_DIAGNOSTIC_CONTRACT_CHECK.json',w/'audit_contact_stability_control.py'];drivers=[('box_inward_run_contract.py','tilt05_run_contract.py'),('run_box_inward_groups.py','run_tilt05_groups.py'),('watch_box_inward_audits.py','watch_tilt05_audits.py'),('close_box_inward_groups.py','close_tilt05_groups.py')]
for a,b in drivers:
 s=rename((w/a).read_text())
 if a in ['run_box_inward_groups.py','close_box_inward_groups.py']:s=s.replace("assert prov['args']['rear_box_inward_correction'] is True","assert prov['args']['expert_top_tilt_recontact_rad']==.05 and prov['args']['rear_box_inward_correction'] is True")
 assert ast.dump(ast.parse(s))==ast.dump(ast.parse((w/b).read_text())),b;files.extend([w/a,w/b])
checked=json.loads((w/'TILT05_DIAGNOSTIC_CONTRACT_CHECK.json').read_text());assert checked['passed']
for path,digest in checked['source_sha256'].items():assert sha(path)==digest
files.extend(w/n for n in new.REPORTS)
env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
code="from pathlib import Path\nimport sys,types\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nm=types.ModuleType('__tilt05_cli__');sys.modules[m.__name__]=m;m.__dict__['__file__']=str(p)\nexec(compile(s,str(p),'exec'),m.__dict__)\na=m.args\nassert a.expert_top_tilt_recontact_rad==.05 and a.rear_box_inward_correction and a.rear_box_entry_lift and a.expert_frontal_top_load_n==5. and a.horizon==10 and a.waist_limit_rad==1. and a.role=='diagnostic' and not a.push_force_n and not a.wait_force_n\nprint('TILT05_CLI_OK')\n"
cli=[]
for c in commands:
 test_args=[v.replace(str(run),str(parent)) for v in c['args']]
 result=subprocess.run([sys.executable,'-c',code,*test_args,'--out-dir','/tmp/tilt05_cli_no_simulator'],env=env,cwd=repo,capture_output=True,text=True);assert result.returncode==0 and 'TILT05_CLI_OK' in result.stdout,(result.stdout[-1000:],result.stderr[-1500:]);cli.append(dict(layout_id=c['layout_id'],wait=c['wait'],passed=True,parsed_args=test_args,layout_path_uses_identical_parent_source=True));print(cli[-1],flush=True)
args=[v.replace(str(run),str(parent)) for v in commands[0]['args']];args[args.index('--expert-top-tilt-recontact-rad')+1]='.20';bad=subprocess.run([sys.executable,'-c',code,*args,'--out-dir','/tmp/tilt05_cli_no_simulator'],env=env,cwd=repo,capture_output=True,text=True);assert bad.returncode==2 and 'error:' in bad.stderr
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,commands=commands,actual_cli_checks=cli,illegal_control_threshold_point20_rejected=True,original_control_count=80,additional_count=56,primary_count=36,formal_upright_gate_rad=.20,original_micro_return_guard_rad=.03,only_runtime_change_internal_withdrawal_rad=.05,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False)
(w/'TILT05_RUN_PROTOCOL_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS6 actual CLIs,illegal0.20CLI rejected,original8+2 and36/80/56')
