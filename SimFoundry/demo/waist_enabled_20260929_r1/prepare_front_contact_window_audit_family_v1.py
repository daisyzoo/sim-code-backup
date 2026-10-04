"""Derive original224 audit schedule unchanged and add10 explicit window audits.
Only module/stage/report names change in original mathematics. No physical job
is launched, and preparation/imports alone are not execution or admission proof.
"""
from pathlib import Path
import ast,json,hashlib,re,datetime
W=Path(__file__).resolve().parent;D=W/'front_contact_window_preparation_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
oldpath=W/'front_loaded_z_quarter_preparation_r1/AUDIT_FAMILY_PREPARATION.json';old=read(oldpath);parents=old['adapters'];assert len(parents)==42
proofs=[D/'OBSERVATION_STREAM_CHECK_V1.json',D/'SOURCE_BINDING_CHECK_V3.json',D/'NATIVE_LIFECYCLE_CHECK_V3.json',D/'FULL_PARENT_LOSS_LIFECYCLE_CHECK_V2.json']
for p in proofs:
 proof=read(p);assert proof['passed']
 for f,h in proof['source_sha256'].items():assert sha(f)==h,f
mapping={Path(r['path']).stem:Path(r['path']).stem.replace('front_loaded_z_quarter','front_window') for r in parents};assert len(set(mapping.values()))==42
mapping.update(front_loaded_z_quarter_stage_source_binding_v1='front_contact_window_stage_source_binding_v2',staged_front_loaded_z_quarter_v1='staged_front_contact_window_v2',FRONT_LOADED_Z_QUARTER_R1_='FRONT_WINDOW_R1_',FRONT_LOADED_Z_QUARTER_STREAM_V2_AUDIT='FRONT_WINDOW_PARENT_STREAM_V2_AUDIT')
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));entries=[]
for row in parents:
 parent=Path(row['path']);assert sha(parent)==row['sha256'];dest=W/(mapping[parent.stem]+'.py');s=pat.sub(lambda m:mapping[m.group()],parent.read_text());edits=[]
 if parent.name=='front_loaded_z_quarter_r1_v4_stage_run_contract.py':
  addition="""
# Additional window evidence audit on every condition, including empty/unselected
# stream identity. The complete parent224 schedule remains a strict subset.
_primary_original_inventory=primary
def primary(wait):
 return _primary_original_inventory(wait)+['audit_front_contact_window_stream_v1.py']
REPORTS['audit_front_contact_window_stream_v1.py']=('FRONT_CONTACT_WINDOW_STREAM_AUDIT_V1.json',('passed',))
"""
  s+=addition;edits.append(dict(append=addition))
 restored=s
 for edit in reversed(edits):assert restored.endswith(edit['append']);restored=restored[:-len(edit['append'])]
 assert rev.sub(lambda m:inverse[m.group()],restored)==parent.read_text();ast.parse(s)
 with dest.open('x') as f:f.write(s)
 entries.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits,math_preserved=True))
paths=[Path(__file__),oldpath,*proofs,W/'front_contact_window_stage_source_binding_v2.py',W/'audit_front_contact_window_stream_v1.py',W/'front_contact_window_observation_audit_v1.py',W/'front_contact_window_loss_lifecycle_v2.py']
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=entries,replacements=mapping,source_binding=str(W/'front_contact_window_stage_source_binding_v2.py'),original_invocations=224,additional_window_invocations=10,expected_full_invocations=234,source_sha256={str(p):sha(p) for p in paths},native_family_checks_pending=True,physical_launch_ready=False,training_ready=False)
with (D/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(adapters=len(entries),original=224,additional=10,total=234)))
