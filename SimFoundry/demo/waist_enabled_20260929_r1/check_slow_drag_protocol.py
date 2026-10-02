"""All six actual collector CLI parses and unchanged complete experiment inventory."""
from pathlib import Path
import ast,json,sys,subprocess,hashlib,os
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)];stage=w/'staged_rear_slow_drag';parent=w/'minimum_motion_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
from prepare_slow_drag_groups import commands,run
import minimum_motion_run_contract as old
import slow_drag_run_contract as new
mapping=json.loads((w/'SLOW_DRAG_AUDIT_VERSION_MAP.json').read_text())
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
p,items=commands();assert len(items)==6 and sum(len(c['tasks']) for c in items if not c['wait'])==8 and sum(len(c['tasks']) for c in items if c['wait'])==2
control=[]
for c in items:
 for task in c['tasks']:
  if c['wait']:continue
  plan=json.loads((parent/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"/'frontal_bypass.json').read_text())['plan'];expected=[rename(n) for n in old.controls(plan)];assert new.controls(plan)==expected;control+=expected
assert len(control)==80 and len(new.ADDITIONAL)*8==56
assert new.ADDITIONAL==[rename(n) for n in old.ADDITIONAL]
for wait in [True,False]:assert new.primary(wait)==[rename(n) for n in old.primary(wait)]
assert new.REPORTS=={rename(k):(rename(v[0]),v[1]) for k,v in old.REPORTS.items()}
drivers={'minimum_motion_run_contract.py':'slow_drag_run_contract.py','run_minimum_motion_groups.py':'run_slow_drag_groups.py','watch_minimum_motion_audits.py':'watch_slow_drag_audits.py','close_minimum_motion_groups.py':'close_slow_drag_groups.py'}
for a,b in drivers.items():
 s=rename((w/a).read_text()).replace('minimum_motion_run_contract','slow_drag_run_contract')
 if a.startswith(('run_','close_')):s=s.replace("assert prov['args']['minimum_motion_recontact'] is True","assert prov['args']['rear_slow_drag'] is True and prov['args']['minimum_motion_recontact'] is True")
 if a.startswith('close_'):s=s.replace("assert meta['minimum_motion_recontact'] is True","assert meta['rear_slow_drag'] is True and meta['minimum_motion_recontact'] is True")
 assert ast.dump(ast.parse(s))==ast.dump(ast.parse((w/b).read_text())),b
for script in set(control)|set(new.ADDITIONAL)|set(new.primary(True))|set(new.primary(False)):assert (w/script).is_file()
env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1');cli=[]
def parse(c,invalid=None):
 args=[x.replace(str(run/'layouts'),str(parent/'layouts')) for x in c['args']]+['--out-dir','/tmp/rear_slow_drag_prelaunch_only']
 if invalid=='no_minimum_motion':args.remove('--minimum-motion-recontact')
 elif invalid=='global_step':args[args.index('--expert-frontal-top-drag-step-m')+1]='0.0015'
 elif invalid=='no_rear_cop':args.remove('--rear-cop-centering')
 elif invalid=='no_continuous':args.remove('--expert-frontal-top-continuous-drag')
 code="from pathlib import Path\nimport sys,types\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nm=types.ModuleType('__slow_protocol__');sys.modules[m.__name__]=m;m.__dict__['__file__']=str(p)\nexec(compile(s,str(p),'exec'),m.__dict__)\na=m.args\nassert a.rear_slow_drag and a.minimum_motion_recontact and a.rear_joint_edge_parent_seed_retry and a.rear_joint_edge_analytic_retry and a.precise_clearance_task_ik and a.recontact_interior_preference and a.unloaded_recontact_pose and a.self_clearance_task_ik and a.expert_frontal_top_load_n==5. and a.horizon==10 and not hasattr(a,'push_assist') and not a.push_force_n and not a.wait_force_n and a.expert_frontal_top_drag_step_m==.003\nprint('SLOW_PROTOCOL_PRELAUNCH_OK')\n"
 child=subprocess.run([sys.executable,'-c',code,*args],env=env,cwd=repo,capture_output=True,text=True)
 if invalid:assert child.returncode==2 and 'error:' in child.stderr,(invalid,child.stdout[-1000:],child.stderr[-1800:])
 else:assert child.returncode==0 and 'SLOW_PROTOCOL_PRELAUNCH_OK' in child.stdout,(c['layout_id'],child.stdout[-1000:],child.stderr[-1800:])
 return dict(layout_id=c['layout_id'],wait=c['wait'],passed=True,invalid_rejected=invalid)
for c in items:cli.append(parse(c));print(c['layout_id'],'actual CLI passed',flush=True)
negative=[]
for invalid in ['no_minimum_motion','global_step','no_rear_cop','no_continuous']:negative.append(parse(items[0],invalid));print('rejected',invalid,flush=True)
sources=[Path(__file__),w/'prepare_slow_drag_groups.py',parent/'PROTOCOL.json',parent/'RESULT.json',stage/'collect_paired_sorting.py',w/'SLOW_DRAG_AUDIT_VERSION_MAP.json',w/'audit_slow_drag_source_contract.py',w/'verify_top_pressure_setting.py',*[w/n for n in drivers],*[w/n for n in drivers.values()],*[w/n for n in new.REPORTS]]
(stage/'RUN_PROTOCOL_CHECK.json').write_text(json.dumps(dict(passed=True,commands=items,actual_prelaunch_commands=cli,negative_cli_rejected=negative,original_control_count=80,additional_count=56,complete_condition_count=10,driver_control_flow_unchanged_except_added_flag_assertions=True,source_sha256={str(q):sha(q) for q in sources},physical_validation=False,training_ready=False),indent=2));print('PASS6CLI +4negative full8push2wait80+56 unchangeddriverflow',flush=True)
