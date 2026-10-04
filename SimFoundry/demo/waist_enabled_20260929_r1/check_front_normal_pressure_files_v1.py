"""Actual file-wrapper pressure check on copied full original front-box fixture.
Phase report may be reused only when every listed byte source is unchanged.
Not new candidate physics; fixture admission stays false.
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys,traceback
W=Path(__file__).resolve().parent;D=W/'front_normal_pressure_files_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_pressure_files_v1 import audit
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,allow_nan=False))
src=W/'front_normal_geometry_files_r2/case_840020';name='layout_840020_push_box_to_bin';assert (src/name/'FRONT_NORMAL_POSE_LIVE_V1_AUDIT.json').exists()
case=D/'case_840020';shutil.copytree(src,case,copy_function=shutil.copy2);ep=case/name
phase=read(ep/'FRONT_NORMAL_POSE_LIVE_V1_AUDIT.json');assert phase['passed']
for name,h in phase['source_sha256'].items():assert sha(ep/name)==sha(src/ep.name/name)==h
quality=read(ep/'quality.json');assert quality['passed'] is False;quality['frames']=1200;write(ep/'quality.json',quality)
result=audit(ep,allow_source_fixture=True);assert result['passed'] and result['fixture_only'] and not result['training_ready'];write(ep/'FRONT_NORMAL_PRESSURE_FILES_V1_AUDIT.json',result)
negative=[]
try:audit(ep)
except AssertionError as e:assert str(e)=='Synthetic fixture is not physical evidence';negative.append('physical_entry_rejects_fixture')
else:raise AssertionError('fixture admitted')
for label,name,mutate in [('wrong_filtered_pressure','peak_load_updates.json',lambda d:d['final_control_states'][30].__setitem__('filtered_n',d['final_control_states'][30]['filtered_n']+.1)),('stale_phase_raw_hash','FRONT_NORMAL_POSE_LIVE_V1_AUDIT.json',lambda d:d['source_sha256'].__setitem__('raw.npz','0'*64))]:
 p=ep/name;original=p.read_bytes();bad=json.loads(original);mutate(bad);write(p,bad)
 try:
  try:audit(ep,allow_source_fixture=True)
  except AssertionError:
   stack=traceback.extract_tb(sys.exc_info()[2])
   expected='audit_front_normal_pressure_stream_v1.py' if label=='wrong_filtered_pressure' else 'audit_front_normal_pressure_files_v1.py'
   assert any(Path(f.filename).name==expected for f in stack),stack;negative.append(label)
  else:raise AssertionError('bad pressure or phase report accepted')
 finally:p.write_bytes(original)
assert read(ep/'quality.json')['passed'] is False
sources={str(p):sha(p) for p in [Path(__file__),W/'audit_front_normal_pressure_files_v1.py',W/'audit_front_normal_pressure_stream_v1.py',src/ep.name/'FRONT_NORMAL_POSE_LIVE_V1_AUDIT.json',ep/'FRONT_NORMAL_POSE_LIVE_V1_AUDIT.json',ep/'FRONT_NORMAL_PRESSURE_FILES_V1_AUDIT.json',ep/'raw.npz',ep/'peak_load_updates.json',ep/'quality.json']}
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,frames=1200,pressure_updates=result['pressure_updates'],negative_rejected=negative,source_sha256=sources,new_recovery_physics_verified=False,training_ready=False)
write(D/'RESULT.json',out);print({k:v for k,v in out.items() if k not in ['scope','source_sha256']},flush=True)
