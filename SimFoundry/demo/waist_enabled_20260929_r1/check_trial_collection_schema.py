"""Isolated v2 schema/catalog/source checks; no physical or training admission."""
from pathlib import Path
import sys,json,hashlib,importlib.util,copy,tempfile,unittest
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_trial_collection';sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['waist_trial_collection','waist_pilot_protocol']:
 spec=importlib.util.spec_from_file_location('simfoundry.data.'+name,stage/(name+'.py'));mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
from simfoundry.data.waist_pilot_protocol import validate_manifest,validate_waist_contract,semantic_settings,REQUIRED_SOURCES,GATES
from simfoundry.data.waist_trial_collection import validate_trial_sources,EXTRA_SOURCES
catalog=w/'fresh_pilot_layout_proposal_r1/PROPOSAL.json';proposal=json.loads(catalog.read_text());p=w/'y_path_nearhalf_groups_r1/case_897003/provenance.json';settings=semantic_settings(json.loads(p.read_text())['args']);settings['expert_top_contact_bout_yaw_hold']=False
hashes={x:sha(repo/x) for x in REQUIRED_SOURCES|EXTRA_SOURCES if (repo/x).exists()};hashes['simfoundry/data/waist_trial_collection.py']=sha(stage/'waist_trial_collection.py')
base=dict(version=2,motion_protocol='waist_yaw_enabled_v1',approved_for_pilot=True,admission_kind='frozen_trial_collection',collection_admission_only=True,training_ready=False,feasibility=[],gates=GATES,collector_settings=settings,prelaunch_collector_settings=settings,pilot_collector_sha256=sha(repo/'scripts/collect_paired_sorting.py'),controller_source_sha256=hashes)
positive=[]
for filename in proposal['plan_sha256']:
 path=catalog.parent/filename;layout=json.loads(path.read_text());c=dict(base,layouts=layout['layouts'],wait_layouts=layout['wait_layouts'],trial_plan=dict(catalog_path=str(catalog),catalog_sha256=sha(catalog),group_plan_path=str(path),group_plan_sha256=sha(path)));validate_manifest(c);positive.append(filename)
# Final c is a real frozen validation group; no geometry or split resampling.
negative=[]
def rejects(label,edit):
 bad=copy.deepcopy(c);edit(bad)
 try:validate_manifest(bad)
 except (ValueError,KeyError):negative.append(label)
 else:raise AssertionError(label)
rejects('training_approval',lambda x:x.update(training_ready=True))
rejects('missing_collection_scope',lambda x:x.pop('collection_admission_only'))
rejects('pretend_feasibility',lambda x:x.update(feasibility=[{'claimed':'passed'}]))
rejects('unknown_version',lambda x:x.update(version=3))
rejects('old_version_without_successful_evidence',lambda x:x.update(version=1))
rejects('horizon_relaxation',lambda x:x['gates'].update(policy_horizon=50))
rejects('non_target_relaxation',lambda x:x['gates'].update(non_target_max_xy_m=.02))
rejects('missing_swap',lambda x:x.update(layouts=x['layouts'][:1]))
rejects('missing_wait',lambda x:x.update(wait_layouts=[]))
rejects('missing_new_source',lambda x:x['controller_source_sha256'].pop('simfoundry/data/waist_trial_collection.py'))
rejects('experimental_yaw_profile',lambda x:x['collector_settings'].update(expert_top_contact_bout_yaw_hold=True))
rejects('catalog_hash',lambda x:x['trial_plan'].update(catalog_sha256='0'*64))
rejects('group_hash',lambda x:x['trial_plan'].update(group_plan_sha256='0'*64))
rejects('resplit_both_assignments',lambda x:[d.update(planned_split='train') for d in x['layouts']])
rejects('new_layout_ids',lambda x:[d.update(layout_id=d['layout_id']+100000) for d in x['layouts']])
# Actual source-byte verification using isolated tiny source files.
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);f=root/'a.py';f.write_text('x=1\n');fixture=dict(controller_source_sha256={'a.py':sha(f)});validate_trial_sources(fixture,root,require_live_sources=True);f.write_text('x=2\n')
 try:validate_trial_sources(fixture,root,require_live_sources=True)
 except ValueError:negative.append('changed_live_source')
 else:raise AssertionError('changed source accepted')
 validate_trial_sources(fixture,root,require_live_sources=False) # downstream recorded-source audit still required
 contract=root/'c.json';contract.write_text(json.dumps(c));validate_waist_contract(contract,require_live_sources=False)
 for kwargs in [dict(layout_id=999999),dict(settings=dict(settings,environment_seed=99))]:
  try:validate_waist_contract(contract,require_live_sources=False,**kwargs)
  except ValueError:negative.append('runtime_'+next(iter(kwargs)))
  else:raise AssertionError(kwargs)
 # v1 failed feasibility stays failed; v2 does not retroactively rewrite it.
 failed=root/'failed';failed.mkdir();objects={'COMPLETE_GROUP_READINESS.json':{'complete_group_feasibility_passed':False,'errors':['original task failed'],'rows':[]},'RESULT.json':{'rows':[]},'PROTOCOL.json':{'source_sha256':{}}}
 for name,obj in objects.items():(failed/name).write_text(json.dumps(obj))
 v1=copy.deepcopy(c);v1['version']=1;v1['feasibility']=[dict(root=str(failed),readiness_sha256=sha(failed/'COMPLETE_GROUP_READINESS.json'),result_sha256=sha(failed/'RESULT.json'),protocol_sha256=sha(failed/'PROTOCOL.json'))];contract.write_text(json.dumps(v1))
 try:validate_waist_contract(contract,require_live_sources=False)
 except ValueError as e:assert 'Incomplete or failed waist feasibility' in str(e);negative.append('v1_failed_feasibility')
 else:raise AssertionError('v1 failed proof accepted')
# Existing dispatch/data rejection tests run with candidate protocol imported.
suite=unittest.TestSuite()
for pattern in ['test_waist_pilot_protocol.py','test_waist_pilot_audit.py','test_converter_waist_admission.py']:
 suite.addTests(unittest.defaultTestLoader.discover(str(repo/'tests'),pattern=pattern))
with (stage/'legacy_regression.log').open('w') as log:r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
assert r.wasSuccessful()
m=json.loads((stage/'MANIFEST.json').read_text());assert sha(repo/'simfoundry/data/waist_pilot_protocol.py')==m['production_protocol_sha256']
report=dict(passed=True,frozen_groups_checked=positive,negative_cases=negative,legacy_test_count=r.testsRun,production_protocol_unchanged=True,scope='Actual immutable12 catalog groups plus adversarial contract/source cases. Legacy converter tests include fixture mocks. No new v2 data collected; no end-to-end physical conversion/admission proof or runtime collector wiring yet. Must finish these before installation.',training_ready=False)
(stage/'SCHEMA_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
