"""Validate complete minimum-motion trial against frozen parent-seed5N baseline.
Same full8push2wait, order, budgets, pressure/camera and80+56 numerical gates.
New causal pose/path flag, independent audit extension and explicit source names.
"""
from pathlib import Path
import ast,json,sys,subprocess,hashlib,os,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)];stage=w/'staged_minimum_motion_recontact';parent=w/'parent_seed_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
from prepare_minimum_motion_groups import commands,run
import parent_seed_run_contract as old
import minimum_motion_run_contract as new
mapping=json.loads((w/'MINIMUM_MOTION_AUDIT_VERSION_MAP.json').read_text())
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
p,items=commands();assert len(items)==6 and sum(len(c['tasks']) for c in items if not c['wait'])==8 and sum(len(c['tasks']) for c in items if c['wait'])==2
for c in items:
 assert c['args'][-1]=='--minimum-motion-recontact'
 assert float(c['args'][c['args'].index('--expert-frontal-top-load-n')+1])==5.
control=[]
for c in items:
 for task in c['tasks']:
  if c['wait']:continue
  plan=json.loads((parent/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"/'frontal_bypass.json').read_text())['plan'];expected=[rename(n) for n in old.controls(plan)];assert new.controls(plan)==expected;control+=expected
assert len(control)==80 and len(new.ADDITIONAL)*8==56
assert new.ADDITIONAL==[rename(n) for n in old.ADDITIONAL]
for wait in [True,False]:assert new.primary(wait)==[rename(n) for n in old.primary(wait)]
assert new.REPORTS=={rename(k):(rename(v[0]),v[1]) for k,v in old.REPORTS.items()}
drivers={'parent_seed_run_contract.py':'minimum_motion_run_contract.py','run_parent_seed_groups.py':'run_minimum_motion_groups.py','watch_parent_seed_audits.py':'watch_minimum_motion_audits.py','close_parent_seed_groups.py':'close_minimum_motion_groups.py'}
for a,b in drivers.items():
 s=rename((w/a).read_text()).replace('parent_seed_run_contract','minimum_motion_run_contract')
 if a.startswith(('run_','close_')):s=s.replace("assert prov['args']['rear_joint_edge_parent_seed_retry'] is True","assert prov['args']['minimum_motion_recontact'] is True and prov['args']['rear_joint_edge_parent_seed_retry'] is True")
 if a.startswith('close_'):s=s.replace("assert meta['rear_joint_edge_parent_seed_retry'] is True","assert meta['minimum_motion_recontact'] is True and meta['rear_joint_edge_parent_seed_retry'] is True")
 assert ast.dump(ast.parse(s),include_attributes=False)==ast.dump(ast.parse((w/b).read_text()),include_attributes=False),b
for script in set(control)|set(new.ADDITIONAL)|set(new.primary(True))|set(new.primary(False)):assert (w/script).is_file()
env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1');cli=[]
for c in items:
 args=[x.replace(str(run/'layouts'),str(parent/'layouts')) for x in c['args']]+['--out-dir','/tmp/precise_interior_protocol_prelaunch_only']
 code="from pathlib import Path\nimport sys,types\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nm=types.ModuleType('__precise_protocol__');sys.modules[m.__name__]=m;m.__dict__['__file__']=str(p)\nexec(compile(s,str(p),'exec'),m.__dict__)\na=m.args\nassert a.minimum_motion_recontact and a.rear_joint_edge_parent_seed_retry and a.rear_joint_edge_analytic_retry and a.precise_clearance_task_ik and a.recontact_interior_preference and a.unloaded_recontact_pose and a.self_clearance_task_ik and a.expert_frontal_top_load_n==5. and a.horizon==10 and not hasattr(a,'push_assist') and not a.push_force_n and not a.wait_force_n\nprint('PRECISE_PROTOCOL_PRELAUNCH_OK')\n"
 child=subprocess.run([sys.executable,'-c',code,*args],env=env,cwd=repo,capture_output=True,text=True);assert child.returncode==0 and 'PRECISE_PROTOCOL_PRELAUNCH_OK' in child.stdout,(c['layout_id'],child.stdout[-1000:],child.stderr[-1800:]);cli.append(dict(layout_id=c['layout_id'],wait=c['wait'],passed=True));print(c['layout_id'],'actual CLI passed',flush=True)
sources=[Path(__file__),w/'prepare_minimum_motion_groups.py',parent/'PROTOCOL.json',parent/'RESULT.json',stage/'collect_paired_sorting.py',w/'MINIMUM_MOTION_AUDIT_VERSION_MAP.json',w/'audit_minimum_motion_source_contract.py',w/'verify_top_pressure_setting.py',*[w/n for n in drivers],*[w/n for n in drivers.values()],*[w/n for n in new.REPORTS]]
out=dict(passed=True,scope=__doc__,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),commands=items,actual_prelaunch_commands=cli,original_control_count=80,additional_count=56,complete_condition_count=10,driver_control_flow_unchanged_except_added_precision_assertions=True,source_sha256={str(q):sha(q) for q in sources},physical_validation=False,training_ready=False);(stage/'RUN_PROTOCOL_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS6CLI full8push2wait80+56 unchangeddriverflow')
