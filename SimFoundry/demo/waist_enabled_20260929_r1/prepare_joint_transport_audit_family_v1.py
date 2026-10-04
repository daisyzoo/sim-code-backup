"""Version original214 parent audits and joint10 stream checks without raw edits.
Only names and the explicitly verified parent-ledger contract change. A joint
proposal may move waist/active joints; its full independent certificate replaces
only the former inactive-five identity assumption. Actual history remains raw.
"""
from pathlib import Path
import ast,json,hashlib,datetime,re
W=Path(__file__).resolve().parent;S=W/'staged_joint_transport_v1';D=W/'joint_transport_runtime_preparation_r1';P=W/'staged_inactive_transport_v2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 for n in ['RUNTIME_CONTEXT_CHECK.json','NATIVE_HOOK_CHECK.json','INDEPENDENT_RECORD_CHECK.json','SOURCE_PREPARATION_CHECK.json','NATIVE_WAIT_STREAM_CHECK.json']:
  p=D/n;report=json.loads(p.read_text());assert report['passed']
  for f,h in report['source_sha256'].items():assert sha(f)==h,f
 old=json.loads((P/'AUDIT_FAMILY_V3_PREPARATION.json').read_text())
 for r in old['adapters']:assert sha(r['path'])==r['sha256'],r['path']
 names={Path(r['path']).name for r in old['adapters']}|{'inactive_transport_command_ledger_v2.py'}
 mapping={n[:-3]:n[:-3].replace('inactive_transport_a3_','joint_transport_j1_') for n in names if 'inactive_transport_a3_' in n}
 mapping.update(audit_inactive_transport_front_recovery_stream_v3='audit_joint_transport_front_recovery_stream_v1',inactive_transport_command_ledger_v2='joint_transport_command_ledger_v1',inactive_transport_stage_source_binding_v2='joint_transport_stage_source_binding_v1',audit_inactive_transport_stream_v2='audit_joint_transport_stream_v1',audit_inactive_transport_records_v1='audit_joint_transport_records_v1',staged_inactive_transport_v2='staged_joint_transport_v1',INACTIVE_TRANSPORT_A3_='JOINT_TRANSPORT_J1_',INACTIVE_TRANSPORT_STREAM_V2_AUDIT='JOINT_TRANSPORT_STREAM_V1_AUDIT',INACTIVE_TRANSPORT_FRONT_RECOVERY_STREAM_V3_AUDIT='JOINT_TRANSPORT_FRONT_RECOVERY_STREAM_V1_AUDIT',inactive_transport_clearance='joint_transport_clearance')
 pattern=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};assert len(inverse)==len(mapping);back=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))))
 rows=[]
 for name in sorted(names):
  src=W/name;dst=W/(mapping[src.stem]+'.py');assert not dst.exists();original=src.read_text();text=pattern.sub(lambda m:mapping[m.group()],original);assert back.sub(lambda m:inverse[m.group()],text)==original;edits=[]
  if name=='inactive_transport_command_ledger_v2.py':
   oldline="   fixed=np.r_[0:6] if c['side']=='left' else np.r_[0,6:11];assert c['side'] in ('left','right') and np.array_equal(parent[fixed],actual[t,fixed])"
   newline="""   assert c['side'] in ('left','right') and p['geometry_certified'] is True
   certificate=r['certificate'];assert certificate['passed'] is True and all(v is True for v in certificate['checks'].values())
   assert certificate['certificate']['passed'] is True and certificate['certificate']['stationarity_residual']<=1e-6
   assert r['proposal']['parent_height_task_preserved'] is True and r['proposal']['original_contact_primal_preserved'] is True
   assert set(r['paths'])=={'nominal','predicted'} and all(v['passed'] is True for v in r['paths'].values())"""
   assert text.count(oldline)==1;text=text.replace(oldline,newline);edits=[dict(old=oldline,new=newline,reason='Joint active/waist motion explicitly allowed; bind original joint independent certificate instead of inactive-five identity.')]
  ast.parse(text);restored=text
  for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
  assert back.sub(lambda m:inverse[m.group()],restored)==original
  with dst.open('x') as f:f.write(text)
  rows.append(dict(parent=str(src),parent_sha256=sha(src),path=str(dst),sha256=sha(dst),edits=edits))
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=rows,replacements=mapping,syntax_inverse_restore_passed=True,original_parent_invocations=214,joint_stream_invocations=10,expected_full_invocations=224,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'AUDIT_FAMILY_V3_PREPARATION.json',S/'COLLECTOR_PREPARATION.json',W/'audit_joint_transport_stream_v1.py',W/'audit_joint_transport_records_v1.py',W/'joint_transport_stage_source_binding_v1.py']},native_adapter_checks_passed=False,physics_started=False,training_ready=False)
 with (D/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps(dict(adapters=len(rows),inverse_restore=True,expected_invocations=224,physics=False)))
if __name__=='__main__':main()
