"""Parse all six original commands with independent interior precision enabled.
Stops before AppLauncher construction. No simulator, physics, new data or audit
source-version approval. Integration AST equivalence is checked separately.
"""
from pathlib import Path
import json,sys,subprocess,hashlib,datetime,os
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_precise_parent_seed';parent=w/'precise_interior_groups_r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=json.loads((parent/'PROTOCOL.json').read_text());check=json.loads((stage/'INTEGRATION_CHECK.json').read_text());assert check['passed']
for n,h in check['source_sha256'].items():assert sha(Path(n))==h,n
rows=[];env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
for c in p['commands']:
 args=c['args']+['--rear-joint-edge-parent-seed-retry','--out-dir','/tmp/interior_precision_prelaunch_only']
 code="from pathlib import Path\nimport sys,types\np=Path("+repr(str(stage/'collect_paired_sorting.py'))+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nm=types.ModuleType('__interior_precision_prelaunch__');sys.modules[m.__name__]=m;m.__dict__['__file__']=str(p)\nexec(compile(s,str(p),'exec'),m.__dict__)\na=m.args\nassert a.rear_joint_edge_parent_seed_retry and a.rear_joint_edge_analytic_retry and a.precise_clearance_task_ik and a.self_clearance_task_ik and a.recontact_interior_preference and a.unloaded_recontact_pose and a.horizon==10 and a.expert_frontal_top_load_n==5.\nprint('PARENT_SEED_PRELAUNCH_OK')\n"
 child=subprocess.run([sys.executable,'-c',code,*args],cwd=repo,env=env,capture_output=True,text=True);assert child.returncode==0 and 'PARENT_SEED_PRELAUNCH_OK' in child.stdout,(c['layout_id'],child.stdout[-1000:],child.stderr[-2000:]);rows.append(dict(layout_id=c['layout_id'],wait=c['wait'],passed=True));print(c['layout_id'],'passed',flush=True)
(stage/'PRELAUNCH_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,source_sha256={str(q):sha(q) for q in [Path(__file__),stage/'collect_paired_sorting.py',stage/'INTEGRATION_CHECK.json',parent/'PROTOCOL.json']},physical_validation=False,audit_version_ready=False,training_ready=False),indent=2));print('ALL6PASS no physical launch',flush=True)
