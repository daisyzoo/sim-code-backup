"""Actual candidate CLI checks stopping before simulator construction."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys

W=Path(__file__).resolve().parent;repo=W.parents[1]
stage=W/'staged_peak_load_guard';parent=W/'staged_substep_observer'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((stage/'PREPARATION.json').read_text())
for path,h in prep['source_sha256'].items():assert sha(path)==h,path
source=(stage/'collect_paired_sorting.py').read_text();restored=source
for block in prep['candidate_blocks']:
    assert restored.count(block)==1;restored=restored.replace(block,'')
assert restored==(parent/'collect_paired_sorting.py').read_text()
protocol=json.loads((W/'substep_reference03_groups_r1/PROTOCOL.json').read_text())
commands=protocol['commands'];assert len(commands)==6 and sum(len(c['tasks']) for c in commands)==10
code="from pathlib import Path\nimport sys,types\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nm=types.ModuleType('__peak_guard_cli__');sys.modules[m.__name__]=m;m.__dict__['__file__']=str(p)\nexec(compile(s,str(p),'exec'),m.__dict__)\na=m.args\nassert a.expert_top_tilt_recontact_rad==.03 and a.expert_frontal_top_load_n==5. and a.horizon==10 and a.waist_limit_rad==1. and a.role=='diagnostic'\nprint('PEAK_GUARD_CLI_OK',a.peak_load_bias_guard,a.trace_substep_contacts)\n"
env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
checks=[]
def call(args):
    return subprocess.run([sys.executable,'-c',code,*args,'--out-dir','/tmp/peak_guard_cli_no_scene'],
                          env=env,cwd=repo,capture_output=True,text=True)
for c in commands:
    p=call(c['args']+['--peak-load-bias-guard'])
    assert p.returncode==0 and 'PEAK_GUARD_CLI_OK True True' in p.stdout,(p.stdout[-1000:],p.stderr[-1500:])
    checks.append(dict(kind='actual_cli',layout_id=c['layout_id'],wait=c['wait'],passed=True))
    print(checks[-1],flush=True)
p=call(commands[0]['args']);assert p.returncode==0 and 'PEAK_GUARD_CLI_OK False True' in p.stdout
checks.append(dict(kind='default_off',passed=True))
bad=[('missing_substep_observer',[], '--trace-substep-contacts'),
     ('missing_top_contact',[], '--expert-frontal-top-recontact'),
     ('changed_pressure',['--expert-frontal-top-load-n','4'],None),
     ('changed_tilt_guard',['--expert-top-tilt-recontact-rad','.05'],None),
     ('policy',['--policy-port','9000'],None),
     ('other_force_controller',['--expert-contact-load-n','1'],None),
     ('pilot',['--role','pilot'],None),
     ('idle',['--idle'],None)]
for name,extra,remove in bad:
    args=[x for x in commands[0]['args'] if x!=remove]+['--peak-load-bias-guard']+extra
    p=call(args)
    assert p.returncode==2 and 'Peak guard requires original5N/.03 diagnostic' in p.stderr,(name,p.returncode,p.stderr[-1500:])
    checks.append(dict(kind='rejected',case=name));print(checks[-1],flush=True)
files=[Path(__file__),stage/'PREPARATION.json',stage/'collect_paired_sorting.py',
       parent/'collect_paired_sorting.py',W/'substep_reference03_groups_r1/PROTOCOL.json']
dest=stage/'PRELAUNCH_CHECK.json';assert not dest.exists()
dest.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    passed=True,checks=checks,parent_recovered_byte_exact=True,
                    source_sha256={str(p):sha(p) for p in files},
                    physical_validation=False,training_ready=False),indent=2))
print('PASS',len(checks),'CLI checks; no simulator constructed')
