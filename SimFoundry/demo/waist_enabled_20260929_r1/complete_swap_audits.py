"""Terminal numeric/evidence preparation only; actual human/model visual review pending."""
import os,json,time,subprocess,hashlib,datetime,sys
from pathlib import Path
root=Path(__file__).resolve().parent;run=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'baseline_complete_swap_r1'
while json.loads((run/'STATUS.json').read_text())['stage']=='running':time.sleep(10)
assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
p=json.loads((run/'PROTOCOL.json').read_text())
for name,digest in p['source_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
(run/'TERMINAL_SOURCE_VERIFICATION.json').write_text(json.dumps(dict(all_frozen_sources_match=True,verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False)))
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1');results=[]
for script in ['review_frontal_run.py','audit_run_camera_visibility.py','audit_run_support_mapping.py','audit_run_arm_contacts.py','audit_parcel_path_clearance.py','audit_top_alignment_stalls.py','audit_support_switch_events.py','audit_hand_obstacle_clearance.py','audit_phase_exposure.py']:
 print('START',script,flush=True)
 with (run/(script+'.log')).open('w') as log:r=subprocess.run(['/home/user/miniconda3/envs/env_isaaclab/bin/python',str(root/script),str(run)],env=env,stdout=log,stderr=subprocess.STDOUT)
 results.append(dict(script=script,returncode=r.returncode));print('DONE',results[-1],flush=True)
 (run/'AUDIT_EXECUTION.json').write_text(json.dumps(results,indent=2))
print('Numeric evidence prepared. Actual visual review STILL PENDING; training_ready=false',flush=True)
