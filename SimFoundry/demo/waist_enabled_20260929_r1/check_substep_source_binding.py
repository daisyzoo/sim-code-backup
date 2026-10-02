"""Synthetic native provenance fixture around an unchanged real parent episode.
This tests source admission only; fixture metadata is not actual runtime evidence.
"""
from pathlib import Path
import os,json,hashlib,tempfile,datetime
import numpy as np
from audit_substep_source_contract import verify_substep_source
W=Path(__file__).resolve().parent;repo=W.parents[1];stage=W/'staged_substep_observer';parent=W/'box_inward_groups_r1/case_840001';original=parent/'layout_840001_push_box_to_bin';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
case=Path(tempfile.mkdtemp(prefix='substep_source_fixture_'));ep=case/original.name;ep.mkdir()
for name in ['raw.npz','frontal_bypass.json']:os.link(original/name,ep/name)
os.link(parent/'runtime_collision_arrays.npz',case/'runtime_collision_arrays.npz')
prov=json.loads((parent/'provenance.json').read_text());prov['args']['trace_substep_contacts']=True
source={}
for rel in prov['source_sha256']:
 new=rel.replace('/staged_box_inward_correction/','/staged_substep_observer/');source[new]=sha(repo/new)
helpers=json.loads((stage/'PREPARATION.json').read_text())['helpers']
for name in helpers:source[str((stage/name).relative_to(repo))]=sha(stage/name)
prov['source_sha256']=source
for rel,h in source.items():
 p=case/'source_snapshot'/rel;p.parent.mkdir(parents=True,exist_ok=True);os.link(repo/rel,p)
(case/'provenance.json').write_text(json.dumps(prov))
with np.load(case/'runtime_collision_arrays.npz') as z:ownership=z['shape_body'].tolist()
metadata=dict(fixture_cpu=False,expected_substeps=24,control_decimation=8,substeps_per_physics_tick=3,solver_dt_s=1/360,all_graphable=True,expected_manager_steps=1,geom_to_shape=[[0]],shape_body=ownership)
lib=Path('/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages');nm=repo.parent/'IsaacLab/source/isaaclab_newton/isaaclab_newton/physics';paths=[nm/'newton_manager.py',nm/'mjwarp_manager.py',lib/'newton/_src/solvers/mujoco/solver_mujoco.py',lib/'mujoco_warp/_src/support.py',*[stage/n for n in helpers]]
rs={}
for p in paths:
 h=sha(p);dest=case/'substep_runtime_sources'/(h+'_'+p.name);dest.parent.mkdir(exist_ok=True);os.link(p,dest);rs[str(p)]=dict(sha256=h,snapshot=str(dest.relative_to(case)))
runtime=dict(observer_installed=True,original_graph_setting=True,training_ready=False,metadata=metadata,source_files=rs);(case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime))
(ep/'substep_contacts.npz').write_bytes(b'SYNTHETIC SOURCE ADMISSION FIXTURE ONLY; NOT A NUMERIC NPZ')
record=dict(metadata=metadata,training_ready=False,recording_sha256=sha(ep/'substep_contacts.npz'));(ep/'SUBSTEP_CONTACT_RECORDING.json').write_text(json.dumps(record))
checks=[];out=verify_substep_source(ep);assert out['passed'];checks.append(dict(kind='synthetic_native_source_admitted_original_numeric_metadata_unchanged'))
def reject(name):
 try:verify_substep_source(ep)
 except (AssertionError,KeyError,ValueError):checks.append(dict(rejected=name))
 else:raise AssertionError('accepted '+name)
# Change only fixture-owned JSON, never linked archive files.
for name,key,value in [('disabled_observer','trace_substep_contacts',False),('wrong_reference_threshold','expert_top_tilt_recontact_rad',.05),('wrong_pressure','expert_frontal_top_load_n',4.),('pilot','role','pilot')]:
 saved=prov['args'][key];prov['args'][key]=value;(case/'provenance.json').write_text(json.dumps(prov));reject(name);prov['args'][key]=saved
(case/'provenance.json').write_text(json.dumps(prov))
for name,key,value in [('wrong_substep_count','expected_substeps',23),('wrong_dt','solver_dt_s',1/120),('cpu_fixture','fixture_cpu',True),('wrong_shape_ownership','shape_body',[])]:
 saved=metadata[key];metadata[key]=value;(case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime));(ep/'SUBSTEP_CONTACT_RECORDING.json').write_text(json.dumps(record));reject(name);metadata[key]=saved
(case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime));(ep/'SUBSTEP_CONTACT_RECORDING.json').write_text(json.dumps(record))
first=next(iter(rs));saved=rs[first]['sha256'];rs[first]['sha256']='0'*64;(case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime));reject('corrupted_runtime_source_hash');rs[first]['sha256']=saved;(case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime))
record['recording_sha256']='0'*64;(ep/'SUBSTEP_CONTACT_RECORDING.json').write_text(json.dumps(record));reject('corrupted_recording_hash');record['recording_sha256']=sha(ep/'substep_contacts.npz');(ep/'SUBSTEP_CONTACT_RECORDING.json').write_text(json.dumps(record))
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,synthetic_case_directory=str(case),actual_runtime_launched=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_substep_source_contract.py',W/'substep_source_binding.py',stage/'PREPARATION.json',parent/'provenance.json',original/'raw.npz',original/'frontal_bypass.json']})
p=W/'SUBSTEP_SOURCE_BINDING_CHECK.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print('PASS',len(checks),'source admission tests; synthetic fixture not physical')
