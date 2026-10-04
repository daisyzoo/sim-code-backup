"""Rebind complete parent214 audit family, preserving verifier mathematics.
Uses corrected parentv4 report routing; no frozen old report is altered.
"""
from pathlib import Path
import ast,datetime,hashlib,json,re
W=Path(__file__).resolve().parent;P=W/'staged_front_recontact_headroom';S=W/'staged_front_inactive_clearance';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['INDEPENDENT_STREAM_CHECK.json','SOURCE_BINDING_CHECK.json','RUNTIME_JOINT_CHECK.json']:
 d=json.loads((S/name).read_text());assert d['passed']
 for p,h in d['source_sha256'].items():assert sha(p)==h,p
parent=json.loads((P/'AUDIT_FAMILY_PREPARATION.json').read_text());names={Path(x['path']).name for x in parent['adapters']};names.add('front_recontact_headroom_v4_stage_run_contract.py')
names.discard('audit_front_recontact_headroom_stream.py');names.discard('front_recontact_headroom_v2_stage_source_binding.py')
mapping={n[:-3]:n[:-3].replace('front_recontact_headroom_','front_inactive_clearance_',1) for n in names}
mapping.update(front_recontact_headroom_v2_stage_source_binding='front_inactive_clearance_stage_source_binding',audit_front_recontact_headroom_stream='audit_front_inactive_clearance_stream',staged_front_recontact_headroom='staged_front_inactive_clearance',FRONT_RECONTACT_HEADROOM_='FRONT_INACTIVE_CLEARANCE_')
pattern=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)));inverse={v:k for k,v in mapping.items()};assert len(inverse)==len(mapping);back=re.compile('|'.join(re.escape(k) for k in sorted(inverse,key=len,reverse=True)));pending=[]
for n in sorted(names):
 src=W/n;dst=W/(mapping[src.stem]+'.py');assert not dst.exists(),dst;original=src.read_text();text=pattern.sub(lambda m:mapping[m.group()],original);ast.parse(text);assert back.sub(lambda m:inverse[m.group()],text)==original;pending.append((src,dst,text))
rows=[]
for src,dst,text in pending:
 with dst.open('x') as f:f.write(text)
 rows.append(dict(parent=str(src),parent_sha256=sha(src),path=str(dst),sha256=sha(dst)))
files=[Path(__file__),P/'AUDIT_FAMILY_PREPARATION.json',S/'INDEPENDENT_STREAM_CHECK.json',S/'SOURCE_BINDING_CHECK.json',W/'front_inactive_clearance_stage_source_binding.py',W/'audit_front_inactive_clearance_stream.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=rows,replacements=mapping,syntax_and_inverse_restore_passed=True,expected_full_invocations=214,source_sha256={str(p):sha(p) for p in files},full_audit_family_ready=False,physical_started=False,training_ready=False)
with (S/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(adapters=len(rows),full_audit_family_ready=False))
