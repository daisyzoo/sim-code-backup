from pathlib import Path
import json,subprocess,os
import numpy as np
root=Path(__file__).resolve().parent
script=root.parents[1]/'scripts/collect_paired_sorting.py'
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
base=['./isaaclab.sh','-p',str(script),'--device','cuda','--viz','none','--newton-contacts','--role','diagnostic','--motion-protocol','waist_yaw_enabled_v1']
def run(name,args):
 (root/'WIDER_WAIST_STATUS.json').write_text(json.dumps(dict(stage=name,training_ready=False)))
 with (root/f'{name}.log').open('w') as log:
  p=subprocess.run(base+args+['--out-dir',str(root/name)],cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 return p.returncode
try:
 run('wide_empty_probe_r1',['--layouts','0','--wait-episodes','1','--wait-steps','120','--waist-limit-rad','.80','--waist-probe'])
 ep=root/'wide_empty_probe_r1/layout_10000_wait_no_package'
 with np.load(ep/'raw.npz') as z:
  q=z['q'];a=z['action'];err=float(abs(q[1:,12]-a[:-1,12]).max())
  assert q[:,12].min()<-.62 and q[:,12].max()>.62
  assert abs(q[0,12:]).max()<1e-4 and abs(a[0,12:]).max()<1e-4
  assert err<.02
 quality=json.loads((ep/'quality.json').read_text())
 assert quality['metrics']['left_table_pen_frames']==quality['metrics']['right_table_pen_frames']==0
 (root/'WIDE_EMPTY_PREFLIGHT.json').write_text(json.dumps(dict(waist_min_rad=float(q[:,12].min()),waist_max_rad=float(q[:,12].max()),max_one_step_error_rad=err,scope='Empty table yaw command/recording and palm-table proxy only; not full-body collision certification or a valid wait sample',training_ready=False),indent=2))
 run('wide_rear_bypass_r1',['--layouts','1','--layout-start','61001','--steps','320','--diagnostic-layout-json',str(root/'paired_compare_r2/swapped.json'),'--waist-limit-rad','.65','--waist-coordinated-expert','--bounded-coupled-ik','--inactive-retract-m','.10','--expert-staging-z','.92','--expert-crossed-contact-offset','-.04','--expert-rear-bypass-m','.18','--trace-episode-contacts','--trace-solved-contact-forces'])
 for task in ('push_box_to_bin','nudge_mailer_to_bin'):
  assert (root/f'wide_rear_bypass_r1/layout_61001_{task}/quality.json').exists()
 (root/'WIDER_WAIST_STATUS.json').write_text(json.dumps(dict(stage='numeric_complete_review_pending',training_ready=False)))
except BaseException as exc:
 (root/'WIDER_WAIST_STATUS.json').write_text(json.dumps(dict(stage='runtime_or_preflight_failed',error=str(exc),training_ready=False)));raise
