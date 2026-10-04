"""Preserve original headroom provenance/observation gates for new79-source stage.
Adds explicit inactive-clearance declaration and exact source reconstruction.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;S=W/'staged_front_inactive_clearance';source=W/'front_recontact_headroom_v2_stage_source_binding.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();text=source.read_text().replace("S=W/'staged_front_recontact_headroom'","S=W/'staged_front_inactive_clearance'").replace('all 77 archived sources','all 79 archived sources')
a=text.index('def verify_preparation():');b=text.index('\ndef verify_settings',a)
block="""def verify_preparation():
 from front_recontact_headroom_v2_stage_source_binding import verify_preparation as verify_parent
 old,bound=verify_parent();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_front_recontact_headroom'
 assert sha(parent/'COLLECTOR_PREPARATION.json')==prep['parent_manifest_sha256']
 for p,h in prep['source_sha256'].items():assert sha(p)==h,p
 expected=prep['stage_sha256'];new={'inactive_clearance_lifecycle.py','inactive_clearance_proposal.py'}
 assert len(expected)==79 and set(expected)==set(old)|new
 assert {n for n in old if expected[n]!=old[n]}==set(prep['changed_parent_files'])=={'collect_paired_sorting.py','front_recontact_center_runtime.py'}
 assert set(prep['edits'])==set(prep['changed_parent_files'])
 for n,h in expected.items():assert sha(S/n)==h,n
 for n,edits in prep['edits'].items():
  restored=(S/n).read_text()
  for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
  assert restored==(parent/n).read_text()
 for n in new:assert sha(S/n)==sha(W/'inactive_hand_headroom_draft_r1'/n)
 for n in ['PARSER_CHECK.json','RUNTIME_JOINT_CHECK.json','INDEPENDENT_EVENT_CHECK.json']:
  proof=json.loads((S/n).read_text());assert proof['passed']
  for p,h in proof['source_sha256'].items():assert sha(p)==h,p
  bound[str(S/n)]=sha(S/n)
 bound[str(S/'COLLECTOR_PREPARATION.json')]=sha(S/'COLLECTOR_PREPARATION.json')
 return expected,bound
"""
text=text[:a]+block+text[b:]
old='def verify_settings(args):';new=old+"\n assert args['front_recontact_inactive_clearance'] is True\n args=dict(args);args.pop('front_recontact_inactive_clearance')";assert text.count(old)==1;text=text.replace(old,new)
old=" assert meta['front_recontact_center_landing'] is True and meta['front_recontact_center_failure'] is None";assert text.count(old)==1;text=text.replace(old,old+"\n spec=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())['inactive_clearance'];assert meta['front_inactive_clearance']==spec")
old="  assert plan['front_recontact_center_landing']==expected";assert text.count(old)==1;text=text.replace(old,old+"\n  assert plan['front_inactive_clearance']==spec")
old=" else:assert not data['rows'] and 'front_recontact_center_landing' not in plan";assert text.count(old)==1;text=text.replace(old,old+" and 'front_inactive_clearance' not in plan")
ast.parse(text);dest=W/'front_inactive_clearance_stage_source_binding.py'
with dest.open('x') as f:f.write(text)
with (S/'SOURCE_BINDING_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(source),parent_sha256=sha(source),path=str(dest),sha256=sha(dest),physical_started=False,training_ready=False),f,indent=2)
print(dest)
