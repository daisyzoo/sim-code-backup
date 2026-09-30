"""Original wait gates plus source/intent checks; actual visual approval separate."""
from pathlib import Path
import json,sys,hashlib,numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parents[1]))
from simfoundry.data.paired_sorting import audit_rollout
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS
p=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with np.load(p/'raw.npz') as z:
 q=z['q'];action=z['action'];meta=json.loads(str(z['collect_meta']));task=str(z['task_id']);prompt=str(z['instruction'])
with np.load(p/'trace.npz') as z:trace={k:z[k] for k in z.files}
settings=json.loads((p.parent/'provenance.json').read_text())['args'];saved=json.loads((p/'quality.json').read_text());errors=[]
if task!='wait_no_package' or prompt!=PAIRED_SORTING_PROMPTS['wait_no_package']:errors.append('Not the exact wait task/instruction')
for key,want in [('motion_protocol','waist_yaw_enabled_v1'),('assist_frames',0),('push_assist',False),('idle_diagnostic',False),('waist_probe',False),('wait_force_n',0.),('push_force_n',0.),('collision_pipeline','newton')]:
 if meta.get(key)!=want:errors.append('Unexpected raw metadata: '+key)
if settings.get('policy_port')!=0 or settings.get('waist_probe') or settings.get('idle') or settings.get('environment_seed') is None:errors.append('Requires ordinary expert wait with explicit seed')
for key in ('motion_protocol','waist_limit_rad','waist_wait_tolerance_rad','environment_seed'):
 if meta.get(key)!=settings.get(key):errors.append('Metadata/provenance mismatch: '+key)
if q.shape!=(settings['wait_steps'],23) or action.shape!=q.shape:errors.append('Frame/state/action shape mismatch')
report=audit_rollout(task,q,action,trace,motion_protocol=settings['motion_protocol'],waist_limit_rad=settings['waist_limit_rad'],waist_wait_tolerance_rad=settings['waist_wait_tolerance_rad'])
if not saved['passed'] or not report['passed']:errors.append('Original saved/recomputed wait gates failed')
result=dict(passed=not errors,errors=errors,original_audit=report,frames=len(q),sampled_rgb_frames=np.linspace(0,len(q)-1,8,dtype=int).tolist(),actual_visual_review='pending',raw_sha256=sha(p/'raw.npz'),trace_sha256=sha(p/'trace.npz'),provenance_sha256=sha(p.parent/'provenance.json'),auditor_sha256=sha(Path(__file__)),scope='Original zero/empty-table/palm drift15mm/waist drift configured10mrad/action-continuity gates. Ordinary expert wait only, no probe or assistance. Source-frozen runner and actual visual review are separate; not model or training admission.',training_ready=False)
(p/'WAIT_STABILITY_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
