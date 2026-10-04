"""Full enabled-wait native geometry fixture; independent original body math.
Not physical data or admission. Stored runtime geometry cannot bypass checks.
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys,traceback
W=Path(__file__).resolve().parent;D=W/'front_normal_geometry_files_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_native_stream_v1 import inspect as inspect_stream
from audit_front_normal_self_clearance_v1 import audit
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,allow_nan=False))
src=W/'front_normal_parent_math_files_r1/case_841010';case=D/'case_841010';shutil.copytree(src,case,copy_function=shutil.copy2);orig=W/'front_effective_height_physical_r1/case_841010';ep=case/'layout_841010_wait_no_package'
for name in ['runtime_configuration.json','runtime_geometry_provenance.json','runtime_collision_arrays.npz']:
 shutil.copy2(orig/name,case/name)
shutil.copytree(orig/'runtime_source',case/'runtime_source',copy_function=shutil.copy2)
stream=inspect_stream(ep,fixture_only=True);write(ep/'FRONT_NORMAL_NATIVE_STREAM_V1_AUDIT.json',stream)
result=audit(ep,allow_source_fixture=True);assert result['passed'] and result['fixture_only'] is True and result['episode_clearance_passed'] is True and result['training_ready'] is False
write(ep/'FRONT_NORMAL_SELF_CLEARANCE_V1_AUDIT.json',result)
negative=[]
try:audit(ep)
except AssertionError as e:assert str(e)=='Synthetic fixture is not physical evidence';negative.append('physical_entry_rejects_fixture')
else:raise AssertionError('physical entry accepted fixture')
path=ep/'self_clearance.json';original=read(path);bad=copy.deepcopy(original);row=next(r for r in bad['rows'] if r['phase']=='post' and r['step']==1);row['runtime_support_gaps_m'][0]+=.001;write(path,bad)
try:
 try:audit(ep,allow_source_fixture=True)
 except AssertionError:
  tb=traceback.extract_tb(sys.exc_info()[2]);assert any('near(gaps,row' in (f.line or '') for f in tb),tb
  negative.append('tampered_actual_runtime_body_gap')
 else:raise AssertionError('bad body geometry accepted')
finally:write(path,original)
# Restore exactly the original bytes, not merely equivalent JSON, for hash binding.
shutil.copy2(src/ep.name/'self_clearance.json',path)
assert sha(path)==sha(src/ep.name/'self_clearance.json')
sources={str(p):sha(p) for p in [Path(__file__),W/'audit_front_normal_self_clearance_v1.py',W/'front_normal_stage_audit_context_v1.py',W/'audit_front_normal_pose_live_v1.py',W/'audit_front_normal_initial_live_v1.py',ep/'raw.npz',path,ep/'FRONT_NORMAL_SELF_CLEARANCE_V1_AUDIT.json',case/'runtime_geometry_provenance.json']}
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,frames=70,negative_rejected=negative,original_body_geometry_verified=True,source_sha256=sources,physics_started=False,training_ready=False)
write(D/'RESULT.json',report);print({k:v for k,v in report.items() if k not in ['scope','source_sha256']},flush=True)
