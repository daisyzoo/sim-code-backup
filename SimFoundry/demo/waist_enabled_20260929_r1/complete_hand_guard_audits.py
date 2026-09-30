import os,json,time,subprocess,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
run=root/'frontal_hand_guard_r1'
while json.loads((run/'STATUS.json').read_text())['stage']=='running':time.sleep(10)
assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
protocol=json.loads((run/'PROTOCOL.json').read_text())
for path,sha in protocol['source_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,path
(run/'TERMINAL_SOURCE_VERIFICATION.json').write_text(json.dumps(dict(all_frozen_sources_match=True,training_ready=False)))
env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
scripts=['review_frontal_run.py','audit_run_camera_visibility.py','audit_run_support_mapping.py','audit_support_hysteresis_live.py','audit_forward_contact_geometry.py','audit_guarded_recovery_events.py','audit_run_arm_contacts.py','audit_cross_axis_admittance.py','audit_push_x_anchor.py','audit_parcel_path_clearance.py','audit_top_alignment_stalls.py','audit_support_switch_events.py','audit_hand_obstacle_clearance.py','audit_hand_guard_live.py']
results=[]
for script in scripts:
 print('START',script,flush=True)
 with (run/(script+'.log')).open('w') as log:r=subprocess.run(['/home/user/miniconda3/envs/env_isaaclab/bin/python',str(root/script),str(run)],env=env,stdout=log,stderr=subprocess.STDOUT)
 results.append(dict(script=script,returncode=r.returncode));print('DONE',results[-1],flush=True)
(run/'AUDIT_EXECUTION.json').write_text(json.dumps(results,indent=2))
