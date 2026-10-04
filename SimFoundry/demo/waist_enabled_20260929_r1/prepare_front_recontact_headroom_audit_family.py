"""Rebind existing full214 audit family to isolated headroom sources/stream.
All verifier mathematics retained. Source/stream changes have separate evidence.
No claim of readiness until native-shaped checks and inventory verification.
"""
from pathlib import Path
import ast,datetime,hashlib,json,re
W=Path(__file__).resolve().parent;S=W/'staged_front_recontact_center';H=W/'staged_front_recontact_headroom';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
names=set()
for manifest,key,pathkey in [('AUDIT_FAMILY_PREPARATION.json','adapters','path'),('CAPTURE_AUDIT_PREPARATION.json','records','target'),('LOADED_INPUT_PREPARATION.json','records','path'),('AUDIT_V3_PREPARATION.json','records','path')]:
 d=json.loads((S/manifest).read_text())
 if key not in d:
  print(manifest,d.keys());raise AssertionError('manifest schema')
 for r in d[key]:names.add(Path(r[pathkey]).name)
names.update(['front_recontact_reference_ledger.py','front_recontact_loaded_episode_inputs.py'])
names.discard('front_recontact_stage_source_binding.py');names.discard('audit_front_recontact_stream.py')
mapping={n[:-3]:n[:-3].replace('front_recontact_','front_recontact_headroom_',1) for n in names}
mapping.update(front_recontact_stage_source_binding='front_recontact_headroom_v2_stage_source_binding',audit_front_recontact_stream='audit_front_recontact_headroom_stream',staged_front_recontact_center='staged_front_recontact_headroom')
for n in ['V1','V2','V3','INITIAL_LIVE']:mapping['FRONT_RECONTACT_'+n]='FRONT_RECONTACT_HEADROOM_'+n
pattern=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)))
def rename(s):return pattern.sub(lambda m:mapping[m.group()],s)
rows=[];pending=[]
for name in sorted(names):
 p=W/name;t=W/(mapping[p.stem]+'.py');assert not t.exists(),t
 orig=p.read_text();s=rename(orig);ast.parse(s)
 # Single regex replacement permits exact reverse reconstruction, no chained accidental rename.
 inverse={v:k for k,v in mapping.items()};assert len(inverse)==len(mapping)
 back=re.sub('|'.join(re.escape(k) for k in sorted(inverse,key=len,reverse=True)),lambda m:inverse[m.group()],s)
 assert back==orig,name
 pending.append((p,t,s))
for p,t,s in pending:
 with t.open('x') as f:f.write(s)
 rows.append(dict(parent=str(p),parent_sha256=sha(p),path=str(t),sha256=sha(t)))
proofs=[Path(__file__),H/'INDEPENDENT_STREAM_CHECK.json',H/'WAIT_STREAM_CHECK.json',H/'SOURCE_BINDING_CHECK.json',W/'front_recontact_headroom_v2_stage_source_binding.py',W/'audit_front_recontact_headroom_stream.py']
with (H/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=rows,replacements=mapping,source_sha256={str(p):sha(p) for p in proofs},syntax_and_inverse_restore_passed=True,expected_full_invocations=214,full_audit_family_ready=False,simulation_started=False,training_ready=False),f,indent=2)
print(json.dumps(dict(modules=len(rows),expected_checks=214,ready=False)))
