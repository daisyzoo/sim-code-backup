from pathlib import Path
import sys,json,hashlib,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));from simfoundry.data.waist_pilot_protocol import semantic_settings
run=Path(sys.argv[1]);protocol=json.loads((run/'PROTOCOL.json').read_text());case=run/('case_'+str(protocol['layout_ids'][0]));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prov=json.loads((case/'provenance.json').read_text());c=json.loads((case/'waist_pilot_contract.json').read_text());assert c['version']==2 and c['training_ready'] is False and c['feasibility']==[]
assert prov['args']['role']=='pilot' and prov['args']['expert_top_contact_bout_yaw_hold'] is False
assert semantic_settings(prov['args'])==c['collector_settings']
for relative,h in prov['source_sha256'].items():assert sha(case/'source_snapshot'/relative)==h
for relative,h in c['controller_source_sha256'].items():assert prov['source_sha256'][relative]==h
assert prov['source_sha256']['scripts/collect_paired_sorting.py']==c['pilot_collector_sha256'];assert sha(case/'waist_pilot_contract.json')==sha(protocol['contract_path'])
check=dict(passed=True,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_archived_sources=len(prov['source_sha256']),contract_bound_dependencies=len(c['controller_source_sha256']),role='pilot',contact_bout_yaw_hold=False,scope='Actual post-AppLauncher settings and source writer on newly started simulation. Physical trajectory incomplete; zero first recorded frame, original task/pose/wait and visual quality not yet reviewed.',training_ready=False);(run/'STARTUP_SOURCE_CHECK.json').write_text(json.dumps(check,indent=2));print(check)
