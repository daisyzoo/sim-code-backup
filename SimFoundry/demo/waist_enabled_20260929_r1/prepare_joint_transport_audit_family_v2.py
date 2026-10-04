"""Correct parent-coordinate stage boundary in a new immutable J2 audit family.
J1 failure remains. Only the old parent's waist target is viewed at its original
boundary, bound to the independently audited joint input; raw history unchanged.
"""
from pathlib import Path
import ast,json,hashlib,datetime,re
W=Path(__file__).resolve().parent;D=W/'joint_transport_runtime_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((D/'AUDIT_FAMILY_PREPARATION.json').read_text());rows=[];mapping={Path(r['path']).stem:Path(r['path']).stem.replace('joint_transport_j1_','joint_transport_j2_') for r in old['adapters'] if 'joint_transport_j1_' in Path(r['path']).stem};mapping['JOINT_TRANSPORT_J1_']='JOINT_TRANSPORT_J2_';inverse={v:k for k,v in mapping.items()};pattern=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));back=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))))
for r in old['adapters']:
 src=Path(r['path']);assert sha(src)==r['sha256']
 if src.stem not in mapping:continue
 dst=W/(mapping[src.stem]+'.py');assert not dst.exists();text=pattern.sub(lambda m:mapping[m.group()],src.read_text());edits=[]
 if src.name=='joint_transport_j1_loaded_episode_inputs.py':
  oldline="  return dict(step=t,selected=selected,metadata=metadata,coordinate=self.coords.get(t),row=self.rows.get(t)"
  newline="  from joint_transport_parent_coordinate_v1 import parent_coordinate\n  coordinate=parent_coordinate(self.coords.get(t),self.transport_parent[t],self.u[t])\n  return dict(step=t,selected=selected,metadata=metadata,coordinate=coordinate,row=self.rows.get(t)"
  assert text.count(oldline)==1;text=text.replace(oldline,newline);edits.append(dict(old=oldline,new=newline))
  line="  self.sources[str(W/'joint_transport_command_ledger_v1.py')]=sha(W/'joint_transport_command_ledger_v1.py')"
  replacement=line+"\n  self.sources[str(W/'joint_transport_parent_coordinate_v1.py')]=sha(W/'joint_transport_parent_coordinate_v1.py')"
  assert text.count(line)==1;text=text.replace(line,replacement);edits.append(dict(old=line,new=replacement))
 ast.parse(text);restored=text
 for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert back.sub(lambda m:inverse[m.group()],restored)==src.read_text()
 with dst.open('x') as f:f.write(text)
 rows.append(dict(parent=str(src),parent_sha256=sha(src),path=str(dst),sha256=sha(dst),edits=edits))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=rows,replacements=mapping,syntax_inverse_restore_passed=True,original_parent_invocations=214,joint_stream_invocations=10,expected_full_invocations=224,shared_unchanged_adapters=[r for r in old['adapters'] if Path(r['path']).stem not in mapping],source_sha256={str(p):sha(p) for p in [Path(__file__),D/'AUDIT_FAMILY_PREPARATION.json',D/'J1_PARENT_CONTEXT_CHECK.json',W/'joint_transport_parent_coordinate_v1.py']},native_adapter_checks_passed=False,physics_started=False,training_ready=False)
with (D/'AUDIT_FAMILY_V2_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(new_adapters=len(rows),only_math_adapter='parent_coordinate_boundary',physics=False)))
