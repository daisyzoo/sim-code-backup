"""Four source/contact file-wrapper branches on marked diagnostic fixtures.
Original physical contacts are copied for verification; no new candidate
physics. Fixture quality explicitly remains false and raw contains no images.
"""
from pathlib import Path
import datetime,hashlib,json,shutil,sys
W=Path(__file__).resolve().parent;D=W/'front_normal_observation_wrappers_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_contacts_v2 import audit
from audit_front_normal_stage_contract_v2 import verify_front_recontact_v1_stage_source
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();fixture_root=W/'front_normal_observation_binding_checks_r2';proof=read(fixture_root/'RESULT.json');assert proof['passed'];rows=[];sources={}
for cid,task in [(840020,'push_box_to_bin'),(840023,'nudge_mailer_to_bin'),(840022,'push_box_to_bin'),(841010,'wait_no_package')]:
 # Copy a new isolated case; never mutate the prior successful fixture proof.
 src=fixture_root/f'case_{cid}';case=D/f'case_{cid}';shutil.copytree(src,case,copy_function=shutil.copy2);ep=case/f'layout_{cid}_{task}';original=W/f'front_effective_height_physical_r1/case_{cid}'/ep.name
 shutil.copy2(original/'solved_contact_forces.json',ep/'solved_contact_forces.json');n=70 if task=='wait_no_package' else 1200
 (ep/'quality.json').write_text(json.dumps(dict(frames=n,passed=False,training_ready=False,reasons=['source_contact_wrapper_fixture_not_collected']),indent=2))
 contract=verify_front_recontact_v1_stage_source(ep);contact=audit(ep);assert contract['passed'] and contact['passed'];assert read(ep/'quality.json')['passed'] is False
 r=dict(episode=ep.name,frames=n,contract_passed=True,contact_wrapper_passed=True,source_binding=contact['source_binding'],quality_passed=False,training_ready=False);rows.append(r)
 for p in [original/'solved_contact_forces.json',ep/'raw.npz',ep/'substep_contacts.npz',ep/'quality.json',case/'provenance.json']:sources[str(p)]=sha(p)
 print(json.dumps({k:v for k,v in r.items() if k!='source_binding'}),flush=True)
for p in [Path(__file__),fixture_root/'RESULT.json',W/'front_normal_stage_source_binding_v3.py',W/'audit_front_normal_contacts_v2.py',W/'audit_front_normal_stage_contract_v2.py']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,source_sha256=sources,physics_started=False,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=True,branches=len(rows))),flush=True)
