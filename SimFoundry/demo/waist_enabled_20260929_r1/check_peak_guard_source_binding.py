"""Synthetic native source admission fixture; never actual candidate execution.
Copies source archives; raw fixture carries reference states and declared candidate
metadata. Numeric task, image and new-controller execution are not established.
"""
from pathlib import Path
import copy,json,hashlib,tempfile,datetime,shutil
import numpy as np
from audit_peak_guard_source_contract import verify_peak_guard_source
W=Path(__file__).resolve().parent;repo=W.parents[1];stage=W/'staged_peak_load_guard'
parent=W/'substep_reference03_groups_r1/case_840001';original=parent/'layout_840001_push_box_to_bin'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
case=Path(tempfile.mkdtemp(prefix='peak_guard_source_fixture_'));ep=case/original.name;ep.mkdir()
shutil.copy2(parent/'runtime_collision_arrays.npz',case/'runtime_collision_arrays.npz')
prov=json.loads((parent/'provenance.json').read_text());prov['args']['peak_load_bias_guard']=True
sources={}
for rel in prov['source_sha256']:
 new=rel.replace('/staged_substep_observer/','/staged_peak_load_guard/');sources[new]=sha(repo/new)
for name in json.loads((stage/'PREPARATION.json').read_text())['helpers']:
 sources[str((stage/name).relative_to(repo))]=sha(stage/name)
prov['source_sha256']=sources
for rel,h in sources.items():
 dest=case/'source_snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/rel,dest)
(case/'provenance.json').write_text(json.dumps(prov))
runtime=json.loads((parent/'SUBSTEP_RUNTIME_BINDING.json').read_text());rs={}
for path,row in runtime['source_files'].items():
 new=path.replace('/staged_substep_observer/','/staged_peak_load_guard/');dest=case/row['snapshot'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(new,dest)
 rs[new]=dict(sha256=sha(Path(new)),snapshot=row['snapshot'])
runtime['source_files']=rs;(case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime))
# Copying these inputs proves source-binding behavior only, not a changed run.
shutil.copy2(original/'substep_contacts.npz',ep/'substep_contacts.npz')
record=json.loads((original/'SUBSTEP_CONTACT_RECORDING.json').read_text());(ep/'SUBSTEP_CONTACT_RECORDING.json').write_text(json.dumps(record))
fr=json.loads((original/'frontal_bypass.json').read_text())
plan=dict(enabled=True,previous_action_substeps=24,peak_threshold_multiplier=2.,negative_increment_only=True,original_filter_and_upward_relief=True,original_guard_priority=True,training_ready=False)
fr['plan']['peak_load_bias_guard']=plan;(ep/'frontal_bypass.json').write_text(json.dumps(fr))
with np.load(original/'raw.npz') as z:
 raw={k:z[k].copy() for k in ['q','action','task_id']};meta=json.loads(str(z['collect_meta']))
meta['peak_load_bias_guard']=True;meta['frontal_bypass_plan']['peak_load_bias_guard']=copy.deepcopy(plan)
def save_raw():np.savez_compressed(ep/'raw.npz',**raw,collect_meta=json.dumps(meta))
save_raw()
pressure=dict(rows=[],final_control_states=[],executed_action_count=1200,wait=False,training_ready=False)
(ep/'peak_load_updates.json').write_text(json.dumps(pressure))
checks=[];assert verify_peak_guard_source(ep)['passed'];checks.append('synthetic_native_source_admitted_not_physics')
def reject(name):
 try:verify_peak_guard_source(ep)
 except (AssertionError,KeyError,ValueError):checks.append(name)
 else:raise AssertionError('accepted '+name)
for name,key,val in [('candidate_disabled','peak_load_bias_guard',False),('observer_disabled','trace_substep_contacts',False),('changed_tilt','expert_top_tilt_recontact_rad',.05),('changed_load','expert_frontal_top_load_n',4.),('policy','policy_port',9000),('other_controller','expert_contact_load_n',1.)]:
 saved=prov['args'][key];prov['args'][key]=val;(case/'provenance.json').write_text(json.dumps(prov));reject(name);prov['args'][key]=saved
(case/'provenance.json').write_text(json.dumps(prov))
key=next(k for k in sources if k.endswith('/peak_load_bias_guard.py'));saved=sources.pop(key);(case/'provenance.json').write_text(json.dumps(prov));reject('missing_candidate_source');sources[key]=saved;(case/'provenance.json').write_text(json.dumps(prov))
p=case/'source_snapshot'/key;saved=p.read_bytes();p.write_bytes(b'fixture corruption');reject('corrupted_archived_candidate');p.write_bytes(saved)
meta['peak_load_bias_guard']=False;save_raw();reject('raw_candidate_flag_missing');meta['peak_load_bias_guard']=True
meta['frontal_bypass_plan']['peak_load_bias_guard']['peak_threshold_multiplier']=3.;save_raw();reject('raw_plan_wrong_threshold');meta['frontal_bypass_plan']['peak_load_bias_guard']['peak_threshold_multiplier']=2.
meta['assist_frames']=1;save_raw();reject('raw_assist');meta['assist_frames']=0;save_raw()
saved=runtime['original_graph_setting'];runtime['original_graph_setting']=False;(case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime));reject('changed_graph_setting');runtime['original_graph_setting']=saved;(case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime))
record['recording_sha256']='0'*64;(ep/'SUBSTEP_CONTACT_RECORDING.json').write_text(json.dumps(record));reject('corrupted_recording_hash');record['recording_sha256']=sha(ep/'substep_contacts.npz');(ep/'SUBSTEP_CONTACT_RECORDING.json').write_text(json.dumps(record))
pressure['executed_action_count']=1199;(ep/'peak_load_updates.json').write_text(json.dumps(pressure));reject('pressure_frame_count_mismatch');pressure['executed_action_count']=1200;(ep/'peak_load_updates.json').write_text(json.dumps(pressure))
assert verify_peak_guard_source(ep)['passed']
files=[Path(__file__),W/'audit_peak_guard_source_contract.py',W/'peak_guard_source_binding.py',stage/'PREPARATION.json',parent/'provenance.json',original/'raw.npz',original/'frontal_bypass.json']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,checks=checks,synthetic_case_directory=str(case),physical_validation=False,training_ready=False,source_sha256={str(p):sha(p) for p in files})
dest=W/'PEAK_GUARD_SOURCE_BINDING_CHECK.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print('PASS',len(checks),'source admission checks; synthetic only')
