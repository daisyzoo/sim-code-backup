"""Parse actual complete6 diagnostic CLIs; never initialize a simulator."""
from pathlib import Path
import sys,json,subprocess,hashlib,os
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_inward_correction';parent=w/'box_entry_lift_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();protocol=json.loads((parent/'PROTOCOL.json').read_text());rows=[]
env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
code="from pathlib import Path\nimport sys,types\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nm=types.ModuleType('__box_entry_cli__');sys.modules[m.__name__]=m;m.__dict__['__file__']=str(p)\nexec(compile(s,str(p),'exec'),m.__dict__)\na=m.args\nassert a.rear_box_inward_correction and a.rear_box_entry_lift and a.rear_box_center_preference and a.rear_slow_drag and a.minimum_motion_recontact and a.expert_frontal_top_load_n==5. and a.horizon==10 and a.expert_frontal_top_drag_step_m==.003 and a.waist_limit_rad==1. and not a.push_force_n and not a.wait_force_n\nprint('BOX_INWARD_CLI_OK')\n"
def check(c,invalid=None):
 args=c['args']+['--rear-box-inward-correction','--out-dir','/tmp/box_inward_cli_no_simulator']
 if invalid=='no_entry':args.remove('--rear-box-entry-lift')
 if invalid=='no_parent_seed':args.remove('--rear-joint-edge-parent-seed-retry')
 if invalid=='no_center':args.remove('--rear-box-center-preference')
 if invalid=='no_slow':args.remove('--rear-slow-drag')
 if invalid=='no_minimum':args.remove('--minimum-motion-recontact')
 if invalid=='no_rear_cop':args.remove('--rear-cop-centering')
 if invalid=='global_step':args[args.index('--expert-frontal-top-drag-step-m')+1]='0.0015'
 child=subprocess.run([sys.executable,'-c',code,*args],env=env,cwd=repo,capture_output=True,text=True)
 if invalid:assert child.returncode==2 and 'error:' in child.stderr,(invalid,child.stdout[-1000:],child.stderr[-1600:])
 else:assert child.returncode==0 and 'BOX_INWARD_CLI_OK' in child.stdout,(c['layout_id'],child.stdout[-1000:],child.stderr[-1600:])
 row=dict(layout_id=c['layout_id'],wait=c['wait'],invalid=invalid,passed=True);rows.append(row);print(row,flush=True)
for c in protocol['commands']:check(c)
for invalid in ['no_entry','no_parent_seed','no_center','no_slow','no_minimum','no_rear_cop','global_step']:check(protocol['commands'][0],invalid)
assert len(rows)==13
files=[Path(__file__),stage/'collect_paired_sorting.py',parent/'PROTOCOL.json'];(stage/'PRELAUNCH_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,rows=rows,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False),indent=2));print('COMPLETE6 valid7 invalid no simulator',flush=True)
