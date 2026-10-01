"""Original70-frame empty-table condition to validate new runtime APIs/archives.
Not a replacement for the original8push2wait comparison or a training example.
"""
from pathlib import Path
import os,sys,json,hashlib,subprocess,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_self_clearance_task_ik';root=w/'self_clearance_runtime_preflight_r1';root.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protocol=json.loads((w/'joint_edge_retry_groups_r1/PROTOCOL.json').read_text());item=next(x for x in protocol['commands'] if x['wait']);args=item['args']+['--self-clearance-task-ik'];out=root/'case';source={str(p):sha(p) for p in stage.iterdir() if p.suffix in ['.py','.json']};source.update({str(repo/n):sha(repo/n) for n in protocol['source_sha256'] if not n.startswith('demo/')})
plan=dict(scope=__doc__,command=[sys.executable,str(stage/'collect_paired_sorting.py'),*args,'--out-dir',str(out)],source_sha256=source,parent_protocol_sha256=sha(w/'joint_edge_retry_groups_r1/PROTOCOL.json'),training_ready=False)
(root/'PROTOCOL.json').write_text(json.dumps(plan,indent=2));env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
with (root/'collector.log').open('w') as log:
    child=subprocess.Popen(plan['command'],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
    (root/'STATUS.json').write_text(json.dumps(dict(status='running',pid=os.getpid(),collector_pid=child.pid,training_ready=False)))
    code=child.wait()
for path,digest in source.items():assert sha(path)==digest
(root/'STATUS.json').write_text(json.dumps(dict(status='process_finished_review_pending',pid=os.getpid(),collector_pid=child.pid,returncode=code,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_unchanged=True,training_ready=False),indent=2));print('finished',code)
