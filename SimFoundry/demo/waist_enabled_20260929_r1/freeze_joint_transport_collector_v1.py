"""Freeze the isolated joint11 collector after saved-context wiring checks.
Not authorization to collect: native source fixtures and complete parent audit
family adaptation/checks still must finish before any physical run.
"""
from pathlib import Path
import json,hashlib,datetime,difflib,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';P=W/'staged_inactive_transport_v2';D=W/'joint_transport_runtime_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from joint_transport_runtime import SPEC
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not (S/'COLLECTOR_PREPARATION.json').exists()
 parent=json.loads((P/'COLLECTOR_PREPARATION.json').read_text());sources={str(P/'COLLECTOR_PREPARATION.json'):sha(P/'COLLECTOR_PREPARATION.json'),str(Path(__file__)):sha(__file__)}
 for n,h in parent['stage_sha256'].items():assert sha(P/n)==h,n
 for name in ['PARSER_CHECK.json','RUNTIME_CONTEXT_CHECK.json','NATIVE_HOOK_CHECK.json','INDEPENDENT_RECORD_CHECK.json']:
  p=D/name;r=json.loads(p.read_text());assert r['passed'] is True
  for f,h in r['source_sha256'].items():assert sha(f)==h,f
  sources[str(p)]=sha(p)
 for name in ['audit_joint_transport_records_v1.py','audit_joint_transport_stream_v1.py','joint_transport_stage_source_binding_v1.py']:sources[str(W/name)]=sha(W/name)
 added=['joint_transport_solver.py','joint_transport_certificate.py','joint_transport_paths.py','joint_transport_runtime.py'];names=list(parent['stage_sha256'])+added
 hashes={n:sha(S/n) for n in names};changed=[n for n,h in parent['stage_sha256'].items() if hashes[n]!=h];assert changed==['collect_paired_sorting.py']
 before=(P/'collect_paired_sorting.py').read_text().splitlines(keepends=True);after=(S/'collect_paired_sorting.py').read_text().splitlines(keepends=True);changes=[]
 for tag,a,b,c,d in difflib.SequenceMatcher(a=before,b=after,autojunk=False).get_opcodes():
  if tag=='equal':continue
  assert tag=='insert' and a==b;changes.append(dict(parent_line=a,new_lines=after[c:d]))
 assert len(changes)==7
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),parent_manifest_sha256=sha(P/'COLLECTOR_PREPARATION.json'),stage_sha256=hashes,changed_parent_files=changed,unchanged_parent_files=[n for n in parent['stage_sha256'] if n not in changed],added_modules=added,collector_insertions=changes,spec=SPEC,source_sha256=sources,collector_integrated=True,native_hook_checked=True,saved_context_record_stream_checked=True,native_physical_source_contract_validated=False,full_stream_audit_ready=False,physics_started=False,training_ready=False)
 with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(dict(frozen_sources=len(hashes),unchanged_parent_sources=len(out['unchanged_parent_files']),collector_insertions=len(changes),physics_started=False)))
if __name__=='__main__':main()
