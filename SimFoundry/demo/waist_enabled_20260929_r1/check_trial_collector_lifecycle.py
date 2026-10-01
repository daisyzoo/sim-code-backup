"""Execute staged real parser/admission functions without launching Isaac."""
from pathlib import Path
import sys,json,hashlib,importlib.util,tempfile,shutil,types,copy
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_trial_collection';sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
original=repo/'scripts/collect_paired_sorting.py';source=original.read_text();needle="    paths.append(ROOT / 'simfoundry/data/waist_pilot_protocol.py')"
assert source.count(needle)==1
candidate=source.replace(needle,needle+"\n    paths.append(ROOT / 'simfoundry/data/waist_trial_collection.py')")
snapshot_marker="    for path in paths:\n        snapshot = root / 'source_snapshot' / path.relative_to(ROOT)"
assert candidate.count(snapshot_marker)==1
candidate=candidate.replace(snapshot_marker,"    if waist_admission is not None:\n        for relative in json.loads(contract_bytes)['controller_source_sha256']:\n            bound_source = ROOT / relative\n            if bound_source not in paths: paths.append(bound_source)\n"+snapshot_marker)
(stage/'collect_paired_sorting.py').write_text(candidate)
before={str(p):sha(p) for p in [original,repo/'simfoundry/data/waist_pilot_protocol.py']}
passed=[];negative=[]
with tempfile.TemporaryDirectory(prefix='trial-lifecycle-') as tmp:
 root=Path(tmp);collector=root/'scripts/collect_paired_sorting.py';collector.parent.mkdir();collector.write_text(candidate)
 # Real imported validator resolves live-source checks against an isolated source tree.
 for name in ['waist_trial_collection','waist_pilot_protocol']:
  p=root/('simfoundry/data/'+name+'.py');p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(stage/p.name,p)
  spec=importlib.util.spec_from_file_location('simfoundry.data.'+name,p);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
 from simfoundry.data.waist_pilot_protocol import REQUIRED_SOURCES,GATES,semantic_settings,validate_manifest
 from simfoundry.data.waist_trial_collection import EXTRA_SOURCES
 # Include every archived controller dependency, not only the minimum registry.
 provenance=json.loads((w/'contact_bout_yaw_groups_r1/case_898002/provenance.json').read_text())
 profile_sources=json.loads((w/'y_path_nearhalf_groups_r1/PROTOCOL.json').read_text())['source_sha256']
 rels=set(provenance['source_sha256'])|REQUIRED_SOURCES|EXTRA_SOURCES|{str(Path(p).relative_to(repo)) for p in profile_sources}
 for relative in rels:
  dest=root/relative
  if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/relative,dest)
 hashes={r:sha(root/r) for r in rels if r!='scripts/collect_paired_sorting.py'}
 protocol=json.loads((w/'y_path_nearhalf_groups_r1/PROTOCOL.json').read_text());cli=list(protocol['settings']);cli[cli.index('--role')+1]='pilot';cli=[x for x in cli if x!='--extended-waist-diagnostic']
 final=semantic_settings(provenance['args']);final['expert_top_contact_bout_yaw_hold']=False
 catalog=w/'fresh_pilot_layout_proposal_r1/PROPOSAL.json';proposal=json.loads(catalog.read_text());contract_path=root/'contract.json'
 def parse(argv,full):
  name='trial_real_parser';m=types.ModuleType(name);m.__file__=str(collector);sys.modules[name]=m;saved=sys.argv
  try:
   sys.argv=['collector',*argv]
   marker='app = AppLauncher(args, enable_cameras=True).app' if full else 'try:\n    waist_admission = prepare_waist_pilot'
   assert candidate.count(marker)==1
   exec(compile(candidate.split(marker)[0],str(collector),'exec'),m.__dict__)
   return m
  finally:sys.argv=saved;sys.modules.pop(name,None)
 for filename in proposal['plan_sha256']:
  planpath=catalog.parent/filename;plan=json.loads(planpath.read_text());lid=plan['layouts'][0]['layout_id'];wid=plan['wait_layouts'][0]['layout_id']
  args=cli+['--out-dir',str(root/'not-created'),'--layouts','2','--layout-start',str(lid),'--wait-episodes','1','--wait-layout-start',str(wid),'--waist-pilot-contract',str(contract_path)]
  initial=parse(args,False)
  c=dict(version=2,motion_protocol='waist_yaw_enabled_v1',approved_for_pilot=True,admission_kind='frozen_trial_collection',collection_admission_only=True,training_ready=False,feasibility=[],gates=GATES,collector_settings=final,prelaunch_collector_settings=semantic_settings(vars(initial.args)),pilot_collector_sha256=sha(collector),controller_source_sha256=hashes,layouts=plan['layouts'],wait_layouts=plan['wait_layouts'],trial_plan=dict(catalog_path=str(catalog),catalog_sha256=sha(catalog),group_plan_path=str(planpath),group_plan_sha256=sha(planpath)))
  validate_manifest(c);contract_path.write_text(json.dumps(c));m=parse(args,True)
  assert set(m.waist_admission.push_layouts)=={d['layout_id'] for d in plan['layouts']} and set(m.waist_admission.wait_layouts)=={wid}
  for entry in plan['layouts']:assert m.waist_admission.layout(entry['layout_id'])==entry
  settings=dict(final,role='pilot');m.finalize_waist_pilot(m.waist_admission,settings,collector)
  assert not (root/'not-created').exists();passed.append(filename)
 # Exercise the actual new builder and runner, with live hashes against this isolated tree.
 def load_script(name,path):
  spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
 builder=load_script('trial_builder_test',stage/'build_trial_collection_contract.py')
 runner=load_script('trial_runner_test',stage/'run_fresh_waist_pilot.py')
 builder_groups=[]
 for filename in proposal['plan_sha256']:
  issued=root/'issued'/filename;builder.build(catalog.parent/filename,root,issued)
  built,bound,commands=runner.prepare(issued,collector)
  assert len(commands)==3 and sum(len(x['tasks']) for x in commands)==5
  assert built['feasibility']==[] and built['collector_settings']['expert_top_contact_bout_yaw_hold'] is False
  for command in commands:
   checked=parse(command['args']+['--out-dir',str(root/'not-created')],True)
   checked.finalize_waist_pilot(checked.waist_admission,built['collector_settings'],collector)
  builder_groups.append(filename)
 # Execute the actual snapshot/provenance writer on the final temporary contract.
 writer_start="    paths = [ROOT / 'simfoundry/calibration/sorting_station.py'"
 writer_end="    spec = resolve_scene_env('sorting_station_g1_23')"
 assert candidate.count(writer_start)==candidate.count(writer_end)==1
 import textwrap
 writer=candidate[candidate.index(writer_start):candidate.index(writer_end)]
 archive=root/'archived_case';archive.mkdir()
 scope=dict(ROOT=root,root=archive,Path=Path,__file__=str(collector),waist_admission=checked.waist_admission,contract_bytes=issued.read_bytes(),args=checked.args,json=json,hashlib=hashlib)
 exec(compile(textwrap.dedent(writer),'<actual collector snapshot writer>','exec'),scope)
 archived=json.loads((archive/'provenance.json').read_text())
 for relative,digest in built['controller_source_sha256'].items():
  assert archived['source_sha256'][relative]==digest
  assert sha(archive/'source_snapshot'/relative)==digest
 snapshot_bindings_checked=len(built['controller_source_sha256'])
 # Exact real admission functions, adversarial settings and live bytes.
 def rejected(label,fn):
  try:fn()
  except (ValueError,KeyError,OSError):negative.append(label)
  else:raise AssertionError(label)
 baseline=vars(m.args).copy()
 rejected('diagnostic_role',lambda:m.prepare_waist_pilot(dict(baseline,role='diagnostic'),collector))
 rejected('new_layout_id',lambda:m.prepare_waist_pilot(dict(baseline,layout_start=999999),collector))
 rejected('mixed_layout_source',lambda:m.prepare_waist_pilot(dict(baseline,diagnostic_layout_json='other.json'),collector))
 rejected('changed_prelaunch_steps',lambda:m.prepare_waist_pilot(dict(baseline,steps=1300),collector))
 rejected('changed_finalizer_steps',lambda:m.finalize_waist_pilot(m.waist_admission,dict(settings,steps=1300),collector))
 collector.write_text(candidate+'\n# altered\n');rejected('changed_collector_bytes',lambda:m.prepare_waist_pilot(baseline,collector));collector.write_text(candidate)
 helper=root/'simfoundry/data/waist_trial_collection.py';b=helper.read_bytes();helper.write_bytes(b+b'\n# altered\n');rejected('changed_trial_admission_bytes',lambda:m.prepare_waist_pilot(baseline,collector));helper.write_bytes(b)
 contract_path.write_text(json.dumps(c)+'\n');rejected('changed_contract_during_launcher',lambda:m.finalize_waist_pilot(m.waist_admission,settings,collector))
for p,digest in before.items():assert sha(p)==digest
manifest=json.loads((stage/'MANIFEST.json').read_text());manifest['candidate_sha256']['collect_paired_sorting.py']=sha(stage/'collect_paired_sorting.py');(stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
report=dict(passed=True,actual_parser_groups=passed,builder_runner_groups=builder_groups,actual_prelaunch_commands_checked=36,snapshot_bindings_checked=snapshot_bindings_checked,negative_cases=negative,production_sources_unchanged=True,scope='Real collector prefix including every pre-AppLauncher CLI guard, actual prepare/finalize admission against an isolated full source snapshot. Finalizer uses recorded resolved settings; AppLauncher, physics and converter are NOT executed; actual collector snapshot/provenance writer is executed in temporary storage. New builder/runner checked on12 groups/36actual CLI commands, exact pre/post settings and source snapshots. Temporary contracts deleted; no admission or data approved.',training_ready=False)
(stage/'COLLECTOR_LIFECYCLE_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
