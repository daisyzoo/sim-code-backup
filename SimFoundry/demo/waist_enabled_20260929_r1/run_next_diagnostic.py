from pathlib import Path
import json,subprocess,os,time
root=Path(__file__).resolve().parent
status=root/'paired_compare_r2/STATUS.json'
for _ in range(300):
 s=json.loads(status.read_text())
 if s['stage']=='runtime_failed':raise RuntimeError('Upstream comparison runtime failure')
 if s['stage']=='numeric_complete_visual_review_pending':break
 time.sleep(2)
else:raise TimeoutError('Upstream comparison did not finish')
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
script=root.parents[1]/'scripts/collect_paired_sorting.py'
cmd=['./isaaclab.sh','-p',str(script),'--device','cuda','--viz','none','--newton-contacts','--role','diagnostic','--layouts','1','--layout-start','61001','--steps','160','--diagnostic-layout-json',str(root/'paired_compare_r2/swapped.json'),'--motion-protocol','waist_yaw_enabled_v1','--waist-coordinated-expert','--expert-staging-z','.92','--expert-crossed-contact-offset','-.04','--trace-episode-contacts','--trace-solved-contact-forces','--out-dir',str(root/'crossed_approach_r1')]
with (root/'crossed_approach_r1.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
(root/'CROSSED_RUN_RESULT.json').write_text(json.dumps(dict(returncode=r.returncode,training_ready=False)))
