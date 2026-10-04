"""Prepare separate77-source collector and strict source binding for headroom v1.
Same explicit default-off recovery flag; versioned source and declared numeric
headroom identify the new experiment. Current running sources are untouched.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;P=W/'staged_front_recontact_center';S=W/'staged_front_recontact_headroom';D=W/'front_bag_recontact_headroom_draft_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not S.exists();S.mkdir()
for n in ['PROBE_RESULT.json','GUARD_CHECK.json']:
 d=json.loads((D/n).read_text());assert d['passed']
 for p,h in d['source_sha256'].items():assert sha(p)==h,p
old=json.loads((P/'COLLECTOR_PREPARATION.json').read_text());hashes=old['stage_sha256'];assert len(hashes)==77
spec=dict(version='front_recontact_headroom_v1',entry_inactive_height_m=.841,nominal_predicted_inactive_height_m=.8405,original_measured_inactive_height_m=.84,original_numerical_tolerance_m=2e-7,waiting_consumes_no_attempt=True)
collector=(P/'collect_paired_sorting.py').read_text();edits=[]
line=next(x for x in collector.splitlines() if "frontal_plan['front_recontact_center_landing']=dict(" in x);new=line[:-1]+',planning_headroom='+repr(spec)+')';edits.append(dict(old=line,new=new));collector=collector.replace(line,new)
a="        episode.collect_meta['front_recontact_center_landing']=True";b=a+"\n        episode.collect_meta['front_recontact_planning_headroom']="+repr(spec);assert collector.count(a)==1;edits.append(dict(old=a,new=b));collector=collector.replace(a,b)
changed=[]
for name,h in hashes.items():
 assert sha(P/name)==h,name
 text=(D/name).read_text() if (D/name).exists() else (P/name).read_text()
 if name=='collect_paired_sorting.py':text=collector
 if name.endswith('.py'):ast.parse(text)
 with (S/name).open('x') as f:f.write(text)
 if sha(S/name)!=h:changed.append(name)
assert set(changed)=={'collect_paired_sorting.py','front_recontact_center_tracking.py','front_recontact_center_lifecycle.py','front_recontact_center_lifecycle_static.py'}
restored=collector
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(P/'collect_paired_sorting.py').read_text()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),parent_manifest_sha256=sha(P/'COLLECTOR_PREPARATION.json'),stage_sha256={n:sha(S/n) for n in hashes},changed_parent_files=changed,unchanged_parent_files=sorted(set(hashes)-set(changed)),collector_edits=edits,planning_headroom=spec,runtime_helpers=old['runtime_helpers'],source_sha256={str(p):sha(p) for p in [Path(__file__),P/'COLLECTOR_PREPARATION.json',D/'PREPARATION.json',D/'PROBE_RESULT.json',D/'GUARD_CHECK.json']},collector_integrated=True,simulation_started=False,training_ready=False)
with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
# Preserve original complete binding, replacing only stage preparation and the
# explicitly versioned declaration. No original observation gate is removed.
source=W/'front_recontact_stage_source_binding.py';text=source.read_text().replace("S=W/'staged_front_recontact_center'","S=W/'staged_front_recontact_headroom'")
start=text.index('REPORTS=');end=text.index('\ndef verify_settings',start)
new_block="""REPORTS=[]

def verify_preparation():
 from front_recontact_stage_source_binding import verify_preparation as verify_parent
 old_sources,bound=verify_parent()
 prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=Path(prep['parent'])
 assert parent==W/'staged_front_recontact_center' and sha(parent/'COLLECTOR_PREPARATION.json')==prep['parent_manifest_sha256']
 for p,h in prep['source_sha256'].items():assert sha(p)==h,p
 expected=prep['stage_sha256'];assert len(expected)==77 and set(expected)==set(old_sources)
 assert {n for n in expected if expected[n]!=old_sources[n]}==set(prep['changed_parent_files'])=={'collect_paired_sorting.py','front_recontact_center_tracking.py','front_recontact_center_lifecycle.py','front_recontact_center_lifecycle_static.py'}
 for n,h in expected.items():assert sha(S/n)==h,n
 restored=(S/'collect_paired_sorting.py').read_text()
 for e in reversed(prep['collector_edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(parent/'collect_paired_sorting.py').read_text()
 draft=W/'front_bag_recontact_headroom_draft_r1'
 for n in prep['runtime_helpers']:assert sha(S/n)==sha(draft/n),n
 for n in ['PROBE_RESULT.json','GUARD_CHECK.json']:
  proof=json.loads((draft/n).read_text());assert proof['passed']
  for p,h in proof['source_sha256'].items():assert sha(p)==h,p
  bound[str(draft/n)]=sha(draft/n)
 bound[str(S/'COLLECTOR_PREPARATION.json')]=sha(S/'COLLECTOR_PREPARATION.json')
 return expected,bound
"""
text=text[:start]+new_block+text[end:]
a=" assert meta['front_recontact_center_landing'] is True and meta['front_recontact_center_failure'] is None";assert a in text;text=text.replace(a,a+"\n assert meta['front_recontact_planning_headroom']=="+repr(spec))
a=next(x for x in text.splitlines() if x.startswith('  expected=dict(enabled=True,side='));b=a[:-1]+',planning_headroom='+repr(spec)+')';text=text.replace(a,b)
text=text.replace('all 71 archived sources','all 77 archived sources');ast.parse(text);dst=W/'front_recontact_headroom_stage_source_binding.py'
with dst.open('x') as f:f.write(text)
with (S/'SOURCE_BINDING_PREPARATION.json').open('x') as f:json.dump(dict(parent=str(source),parent_sha256=sha(source),path=str(dst),sha256=sha(dst),new_stage=str(S),physics_started=False,training_ready=False),f,indent=2)
print(dict(stage=str(S),runtime_files=77,changed=changed,physics_started=False))
