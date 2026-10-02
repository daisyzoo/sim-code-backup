"""Separate declared supplements for exact metadata recomputation only.
Every original audit file/result stays immutable; original constraints unchanged.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();original=json.loads((W/'REAR_LATCHED_ORIGINAL_AUDIT_PREPARATION.json').read_text());names=[r['output'] for r in original['files']];mapping={n:n+'_v2' for n in names};mapping.update(audit_rear_corridor_latched_native='audit_rear_corridor_latched_native_v2',audit_rear_corridor_latched_records='audit_rear_corridor_latched_records_v2');rows=[]
for name in names:
 src=W/(name+'.py');out=W/(mapping[name]+'.py');assert not out.exists();s=src.read_text();edits=[]
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):
  count=s.count(a)
  if count:assert b not in s;s=s.replace(a,b);edits.append(dict(old=a,new=b,count=count))
 for a,b in [('REAR_LATCHED_','REAR_LATCHED_V2_'),('REAR_CORRIDOR_LATCHED_NATIVE_AUDIT','REAR_CORRIDOR_LATCHED_NATIVE_V2_AUDIT')]:
  count=s.count(a)
  if count:assert b not in s;s=s.replace(a,b);edits.append(dict(old=a,new=b,count=count))
 back=s
 for e in reversed(edits):assert back.count(e['new'])==e['count'];back=back.replace(e['new'],e['old'])
 assert back==src.read_text();ast.parse(s);out.write_text(s);rows.append(dict(parent=name,output=mapping[name],parent_sha256=sha(src),output_sha256=sha(out),edits=edits))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rows,mapping=mapping,correction_sha256=sha(W/'REAR_LATCHED_AUDIT_EQUALITY_V2_PREPARATION.json'),scope=__doc__,training_ready=False);dest=W/'REAR_LATCHED_AUDIT_SUPPLEMENTS_V2_PREPARATION.json';assert not dest.exists();dest.write_text(json.dumps(report,indent=2));print('Prepared',len(rows),'separate reversible audit supplements.')
