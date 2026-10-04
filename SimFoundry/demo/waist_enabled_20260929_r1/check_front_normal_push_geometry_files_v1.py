"""Complete difficult front-box off-branch pose and body audit on marked fixture.
Original dynamics only, no new normal-strategy physical evidence/admission.
"""
from pathlib import Path
import datetime,hashlib,json,shutil,sys
W=Path(__file__).resolve().parent;D=W/'front_normal_geometry_files_r2';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_native_stream_v1 import inspect as inspect_stream
from audit_front_normal_pose_live_v1 import inspect as inspect_pose
from audit_front_normal_self_clearance_v1 import audit
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,allow_nan=False))
src=W/'front_normal_parent_math_files_r1/case_840020';case=D/'case_840020';shutil.copytree(src,case,copy_function=shutil.copy2);orig=W/'front_effective_height_physical_r1/case_840020';ep=case/'layout_840020_push_box_to_bin'
for name in ['runtime_configuration.json','runtime_geometry_provenance.json','runtime_collision_arrays.npz']:shutil.copy2(orig/name,case/name)
shutil.copytree(orig/'runtime_source',case/'runtime_source',copy_function=shutil.copy2)
for name in ['recontact_pose.json','terminal_joint_hold.json','region_approach.json']:
 if (orig/ep.name/name).exists():shutil.copy2(orig/ep.name/name,ep/name)
print('RUN native stream',flush=True);stream=inspect_stream(ep,fixture_only=True);write(ep/'FRONT_NORMAL_NATIVE_STREAM_V1_AUDIT.json',stream)
print('RUN full pose',flush=True);pose=inspect_pose(ep,allow_source_fixture=True);assert pose['passed'];write(ep/'FRONT_NORMAL_POSE_LIVE_V1_AUDIT.json',pose)
print('RUN full body',flush=True);body=audit(ep,allow_source_fixture=True);assert body['passed'] and body['fixture_only'] is True and body['episode_clearance_passed'] is True and body['training_ready'] is False
write(ep/'FRONT_NORMAL_SELF_CLEARANCE_V1_AUDIT.json',body)
sources={str(p):sha(p) for p in [Path(__file__),W/'audit_front_normal_self_clearance_v1.py',W/'front_normal_stage_audit_context_v1.py',W/'audit_front_normal_pose_live_v1.py',W/'audit_front_normal_initial_live_v1.py',ep/'raw.npz',ep/'FRONT_NORMAL_SELF_CLEARANCE_V1_AUDIT.json',ep/'FRONT_NORMAL_POSE_LIVE_V1_AUDIT.json',case/'runtime_geometry_provenance.json']}
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,frames=1200,pose_passed=True,body_passed=True,source_sha256=sources,physics_started=False,training_ready=False)
write(D/'RESULT.json',report);print({k:v for k,v in report.items() if k not in ['scope','source_sha256']},flush=True)
