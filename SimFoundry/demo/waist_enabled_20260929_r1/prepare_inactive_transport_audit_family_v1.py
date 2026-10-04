"""Preserve original214 audit mathematics; add10 transport stream audits.
Explicit parent command outputs are separate from immutable actual prior actions.
"""
from pathlib import Path
import ast,json,hashlib,datetime,re
W=Path(__file__).resolve().parent;P=W/'staged_front_box_recenter_v3';S=W/'staged_inactive_transport_v1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for n in ['NATIVE_HOOK_CHECK.json','INDEPENDENT_RECORD_CHECK.json','SOURCE_BINDING_CHECK.json','NATIVE_WAIT_STREAM_CHECK.json']:
 d=json.loads((S/n).read_text());assert d['passed']
 for p,h in d['source_sha256'].items():
  if '/inactive_transport_source_fixture_' not in p:assert sha(p)==h,p
old=json.loads((P/'AUDIT_FAMILY_V2_PREPARATION.json').read_text());names={Path(r['path']).name for r in old['adapters']};names.add('audit_front_box_recenter_stream.py')
mapping={n[:-3]:n[:-3].replace('front_box_recenter_a2_','inactive_transport_a1_',1) for n in names if n!='audit_front_box_recenter_stream.py'}
mapping.update(audit_front_box_recenter_stream='audit_inactive_transport_front_recovery_stream_v1',front_box_recenter_stage_source_binding='inactive_transport_stage_source_binding_v1',staged_front_box_recenter_v3='staged_inactive_transport_v1',FRONT_BOX_RECENTER_A2_='INACTIVE_TRANSPORT_A1_',FRONT_BOX_RECENTER_STREAM_AUDIT='INACTIVE_TRANSPORT_FRONT_RECOVERY_STREAM_AUDIT')
pattern=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)));inverse={v:k for k,v in mapping.items()};assert len(inverse)==len(mapping);back=re.compile('|'.join(re.escape(k) for k in sorted(inverse,key=len,reverse=True)))
changes={}
def edit(name,old,new):changes.setdefault(name,[]).append(dict(old=old,new=new))
for version in [1,3]:
 n=f'audit_inactive_transport_a1_v{version}_stage_self_clearance.py'
 edit(n," priority_records={r['step']:r for r in json.loads((ep/'front_loaded_z_priority.json').read_text())['rows']}"," from inactive_transport_command_ledger_v1 import load_transport_ledger\n transport_parent,transport_proof=load_transport_ledger(ep)\n priority_records={r['step']:r for r in json.loads((ep/'front_loaded_z_priority.json').read_text())['rows']}")
 edit(n,'  near(target,u[t],0);controller_frames+=1',"  near(target,transport_parent[t],0)\n  transport=coords[t]['inactive_transport_clearance'] if isinstance(coords,dict) else c['inactive_transport_clearance']\n  near(transport['parent_command'],target,0);near(transport['output_command'],u[t],0);controller_frames+=1")
 # No actual-final geometry or previous-action input is changed.
n='inactive_transport_a1_loaded_episode_inputs.py'
edit(n,' def __init__(self,episode):',' def __init__(self,episode,*,allow_source_fixture=False):')
line="  self.sources[str(self.ep/'raw.npz')]=sha(self.ep/'raw.npz');self.n=len(self.q)"
edit(n,line,line+"\n  from inactive_transport_command_ledger_v1 import load_transport_ledger\n  self.transport_parent,self.transport_proof=load_transport_ledger(self.ep,allow_source_fixture=allow_source_fixture)\n  self.sources[str(self.ep/'INACTIVE_TRANSPORT_STREAM_V1_AUDIT.json')]=sha(self.ep/'INACTIVE_TRANSPORT_STREAM_V1_AUDIT.json')\n  self.sources[str(W/'inactive_transport_command_ledger_v1.py')]=sha(W/'inactive_transport_command_ledger_v1.py')")
edit(n,'output=self.u[t] if unissued_output is None else unissued_output','output=self.transport_parent[t] if unissued_output is None else unissued_output')
for version in [1,2]:
 n=f'audit_inactive_transport_a1_v{version}_z_execution.py'
 edit(n,'e=EpisodeInputs(ep);records=','e=EpisodeInputs(ep,allow_source_fixture=allow_source_fixture);records=')
 edit(n,'e.hand,e.q[t],e.u[t],side,e.oxy[t]','e.hand,e.q[t],e.transport_parent[t],side,e.oxy[t]')
for n in [x+'.py' for x in mapping.values() if x.startswith('inactive_transport_a1_') and x.endswith('_stage_run_contract')]:
 # The new full-stream check runs before every original primary audit.
 oldline=" return ['audit_inactive_transport_a1_v2_execution.py','audit_inactive_transport_front_recovery_stream_v1.py']"
 # Earlier contract versions may intentionally use v1 execution; handle below.
for name in sorted(names):
 src=W/name;dst=W/(mapping[src.stem]+'.py');assert not dst.exists(),dst
 text=pattern.sub(lambda m:mapping[m.group()],src.read_text());assert back.sub(lambda m:inverse[m.group()],text)==src.read_text()
 if dst.name.endswith('_stage_run_contract.py'):
  node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='primary');line=next(x for x in ast.get_source_segment(text,node).splitlines() if x.startswith(' return ['));edit(dst.name,line,line.replace(' return ['," return ['audit_inactive_transport_stream_v1.py',",1))
  textadd="\nREPORTS['audit_inactive_transport_stream_v1.py']=('INACTIVE_TRANSPORT_STREAM_V1_AUDIT.json',('passed',))\n"
 else:textadd=''
 for e in changes.get(dst.name,[]):assert text.count(e['old'])==1,(dst.name,e['old']);text=text.replace(e['old'],e['new'])
 text+=textadd;ast.parse(text)
 restored=text[:-len(textadd)] if textadd else text
 for e in reversed(changes.get(dst.name,[])):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert back.sub(lambda m:inverse[m.group()],restored)==src.read_text()
 with dst.open('x') as f:f.write(text)
 changes.setdefault(dst.name,[])
# Preserve exact parent and generated file identities.
rows=[dict(parent=str(W/n),parent_sha256=sha(W/n),path=str(W/(mapping[n[:-3]]+'.py')),sha256=sha(W/(mapping[n[:-3]]+'.py')),edits=changes[mapping[n[:-3]]+'.py']) for n in sorted(names)]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=rows,replacements=mapping,syntax_inverse_restore_passed=True,original_full_invocations=214,additional_transport_invocations=10,expected_full_invocations=224,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'AUDIT_FAMILY_V2_PREPARATION.json',W/'inactive_transport_command_ledger_v1.py',W/'audit_inactive_transport_stream_v1.py',W/'inactive_transport_stage_source_binding_v1.py']},native_adapter_checks_passed=False,physics_started=False,training_ready=False)
with (S/'AUDIT_FAMILY_V1_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(adapters=len(rows),original_invocations=214,additional=10,physics=False)))
