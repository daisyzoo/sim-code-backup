import os,json,hashlib,subprocess
from pathlib import Path
r=Path(__file__).resolve().parent;out=r/'waist78_probe_r1';out.mkdir(exist_ok=False)
assert json.loads((r/'frontal_load_recovery_smoke_r1/STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
settings=['--device','cuda','--viz','none','--newton-contacts','--role','diagnostic','--motion-protocol','waist_yaw_enabled_v1','--layouts','0','--wait-episodes','1','--wait-steps','180','--waist-limit-rad','.80','--waist-probe','--waist-probe-amplitude-rad','.78','--trace-viewer-every','10']
parent=json.loads((r/'frontal_load_recovery_smoke_r1/PROTOCOL.json').read_text());hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in parent['source_sha256']}
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,scope='Empty table physical yaw command/recording preflight at actual.78rad. Intentional motion, must fail wait stability. Not full-body clearance certificate, not deployment range validation.',training_ready=False),indent=2))
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,**kw),indent=2))
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
try:
 status('running')
 with (out/'probe.log').open('w') as log:ret=subprocess.run(['./isaaclab.sh','-p',str(r.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--out-dir',str(out/'case')],cwd=r.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 ep=out/'case/layout_10000_wait_no_package';q=json.loads((ep/'quality.json').read_text());assert q['frames']==180 and not q['training_ready']
 status('numeric_complete_actual_visual_review_pending',returncode=ret.returncode)
except BaseException as exc:status('runtime_failed',error=str(exc));raise
