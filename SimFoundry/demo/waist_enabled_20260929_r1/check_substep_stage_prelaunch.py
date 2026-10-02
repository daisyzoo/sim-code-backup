"""Real collector CLI parsing and exact parent-source recovery, no scene launch."""
from pathlib import Path
import ast,json,hashlib,datetime,subprocess,sys,os,copy
W=Path(__file__).resolve().parent;repo=W.parents[1];stage=W/'staged_substep_observer';parent=W/'staged_box_inward_correction';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prep=json.loads((stage/'PREPARATION.json').read_text())
for name,h in prep['source_sha256'].items():assert sha(Path(name))==h
source=(stage/'collect_paired_sorting.py').read_text();restored=source
for block in prep['instrumentation_blocks']:assert restored.count(block)==1;restored=restored.replace(block,'')
assert restored==(parent/'collect_paired_sorting.py').read_text()
protocol=json.loads((W/'tilt05_groups_r1/PROTOCOL.json').read_text());commands=protocol['commands'];assert len(commands)==6 and sum(len(c['tasks']) for c in commands)==10
code="from pathlib import Path\nimport sys,types\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nm=types.ModuleType('__substep_cli__');sys.modules[m.__name__]=m;m.__dict__['__file__']=str(p)\nexec(compile(s,str(p),'exec'),m.__dict__)\na=m.args\nassert a.expert_top_tilt_recontact_rad==.05 and a.expert_frontal_top_load_n==5. and a.horizon==10 and a.waist_limit_rad==1. and a.role=='diagnostic'\nprint('SUBSTEP_CLI_OK',a.trace_substep_contacts)\n"
env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
checks=[]
def call(args):return subprocess.run([sys.executable,'-c',code,*args,'--out-dir','/tmp/substep_cli_no_simulator'],env=env,cwd=repo,capture_output=True,text=True)
for c in commands:
 p=call(c['args']+['--trace-substep-contacts']);assert p.returncode==0 and 'SUBSTEP_CLI_OK True' in p.stdout,(p.stdout[-1000:],p.stderr[-1500:]);checks.append(dict(kind='actual_cli',layout_id=c['layout_id'],wait=c['wait'],passed=True));print(checks[-1],flush=True)
p=call(commands[0]['args']);assert p.returncode==0 and 'SUBSTEP_CLI_OK False' in p.stdout;checks.append(dict(kind='default_off',passed=True))
for name,extra in [('pilot',['--role','pilot']),('policy',['--policy-port','9000']),('idle',['--idle']),('push_force',['--push-force-n','1']),('wait_force',['--wait-force-n','1']),('missing_original_force_observer',[])]:
 args=commands[0]['args']+['--trace-substep-contacts']+extra
 if name=='missing_original_force_observer':args=[x for x in args if x!='--trace-solved-contact-forces']
 p=call(args);assert p.returncode==2 and 'Substep observation requires diagnostic expert' in p.stderr,(name,p.returncode,p.stderr[-2000:]);checks.append(dict(kind='rejected',case=name));print(checks[-1],flush=True)
files=[Path(__file__),stage/'PREPARATION.json',stage/'collect_paired_sorting.py',parent/'collect_paired_sorting.py',W/'tilt05_groups_r1/PROTOCOL.json']
p=stage/'PRELAUNCH_CHECK.json';assert not p.exists();p.write_text(json.dumps(dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,source_sha256={str(f):sha(f) for f in files},parent_collector_recovered_byte_exact=True,physical_validation=False,training_ready=False),indent=2));print('PASS',len(checks),'actual CLI checks; no scene launch')
