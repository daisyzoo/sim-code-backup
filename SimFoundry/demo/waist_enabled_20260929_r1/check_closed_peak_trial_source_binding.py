"""Synthetic provenance fixture only, not a real fresh pilot or training data.
Uses old physical inputs plus declared fresh metadata to test admission damage;
no images copied, and no data conversion or physical-success claim is possible.
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys,tempfile
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from audit_closed_peak_trial_source_contract import verify_closed_peak_trial_source
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
stage=W/'staged_closed_peak_trial';parent=W/'peak_guard_groups_r1/case_840001';original=parent/'layout_840001_push_box_to_bin'
cp=W/'fresh_closed_peak_trial_contracts_r1/fresh_lateral_00.json';contract=json.loads(cp.read_text());checks=[]
with tempfile.TemporaryDirectory(prefix='closed_peak_trial_source_fixture_') as td:
 case=Path(td);ep=case/original.name;ep.mkdir();(case/'FIXTURE_ONLY.json').write_text(json.dumps(dict(synthetic=True,training_ready=False,scope=__doc__)))
 (case/'waist_pilot_contract.json').write_bytes(cp.read_bytes());shutil.copy2(parent/'runtime_collision_arrays.npz',case/'runtime_collision_arrays.npz')
 prov=json.loads((parent/'provenance.json').read_text());prov['args'].update(role='pilot',extended_waist_diagnostic=False,diagnostic_layout_json=None,waist_pilot_contract=str(case/'waist_pilot_contract.json'))
 sources=dict(contract['controller_source_sha256']);sources[str((stage/'collect_paired_sorting.py').relative_to(ROOT))]=sha(stage/'collect_paired_sorting.py');prov['source_sha256']=sources
 for rel,digest in sources.items():
  p=case/'source_snapshot'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,p);assert sha(p)==digest
 def save_prov():(case/'provenance.json').write_text(json.dumps(prov))
 save_prov()
 runtime=json.loads((parent/'SUBSTEP_RUNTIME_BINDING.json').read_text());source_files={}
 for path,row in runtime['source_files'].items():
  new=path.replace('/staged_peak_load_guard/','/staged_closed_peak_trial/');dest=case/row['snapshot'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(new,dest)
  source_files[new]=dict(sha256=sha(new),snapshot=row['snapshot'])
 runtime['source_files']=source_files
 def save_runtime():(case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime))
 save_runtime()
 for name in ['substep_contacts.npz','SUBSTEP_CONTACT_RECORDING.json','frontal_bypass.json','peak_load_updates.json']:shutil.copy2(original/name,ep/name)
 with np.load(original/'raw.npz') as z:
  raw={k:z[k].copy() for k in ['q','action','task_id']};meta=json.loads(str(z['collect_meta']))
 meta.update(collection_role='pilot',waist_pilot_contract_sha256=sha(cp),layout=next(d for d in contract['layouts'] if d['layout_id']==840001))
 def save_raw():np.savez_compressed(ep/'raw.npz',**raw,collect_meta=json.dumps(meta))
 save_raw();assert verify_closed_peak_trial_source(ep)['passed'];checks.append('synthetic_source_positive_not_physical_or_data_approval')
 def reject(name):
  try:verify_closed_peak_trial_source(ep)
  except (AssertionError,ValueError,KeyError):checks.append(name)
  else:raise AssertionError('Accepted invalid source: '+name)
 for key,value in [('role','diagnostic'),('expert_frontal_top_load_n',4.),('expert_top_tilt_recontact_rad',.05),('trace_substep_contacts',False),('peak_load_bias_guard',False),('waist_limit_rad',.9),('push_force_n',1.),('policy_port',9000),('steps',1199)]:
  saved=prov['args'][key];prov['args'][key]=value;save_prov();reject('changed_'+key);prov['args'][key]=saved
 save_prov()
 key=next(k for k in sources if k.endswith('/peak_load_bias_guard.py'));saved=sources.pop(key);save_prov();reject('omitted_runtime_source');sources[key]=saved;save_prov()
 path=case/'source_snapshot'/key;saved=path.read_bytes();path.write_bytes(b'fixture damage');reject('changed_archived_helper');path.write_bytes(saved)
 for key,value in [('collection_role','diagnostic'),('waist_pilot_contract_sha256','0'*64),('assist_frames',1),('push_assist',True)]:
  saved=meta[key];meta[key]=value;save_raw();reject('raw_'+key);meta[key]=saved
 save_raw()
 runtime['original_graph_setting']=False;save_runtime();reject('changed_graph');runtime['original_graph_setting']=True;save_runtime()
 path=case/'waist_pilot_contract.json';saved=path.read_bytes();changed=copy.deepcopy(contract);changed['gates']['non_target_max_xy_m']=.02;path.write_text(json.dumps(changed));reject('lowered_non_target_gate');path.write_bytes(saved)
 assert verify_closed_peak_trial_source(ep)['passed']
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,checks=checks,physical_validation=False,training_ready=False,fixture_removed_after_test=True,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'closed_peak_trial_source_binding.py',W/'audit_closed_peak_trial_source_contract.py',stage/'PREPARATION.json',cp,original/'raw.npz',parent/'provenance.json']})
with (W/'CLOSED_PEAK_TRIAL_SOURCE_BINDING_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print('PASS',len(checks),'synthetic source checks; temporary fixture removed')
