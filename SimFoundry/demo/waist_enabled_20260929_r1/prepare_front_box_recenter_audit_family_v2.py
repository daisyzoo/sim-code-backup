"""Rebind complete parent214 audit family, preserving verifier mathematics.
Uses corrected parentv4 report routing; no frozen old report is altered.
"""
from pathlib import Path
import ast,datetime,hashlib,json,re
W=Path(__file__).resolve().parent;P=W/'staged_front_recontact_headroom';S=W/'staged_front_box_recenter_v3';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['INDEPENDENT_STREAM_CHECK.json','SOURCE_BINDING_CHECK.json','COLLECTOR_HOOK_CHECK.json']:
 d=json.loads((S/name).read_text());assert d['passed']
 for p,h in d['source_sha256'].items():assert sha(p)==h,p
parent=json.loads((P/'AUDIT_FAMILY_PREPARATION.json').read_text());names={Path(x['path']).name for x in parent['adapters']};names.add('front_recontact_headroom_v4_stage_run_contract.py')
names.discard('audit_front_recontact_headroom_stream.py');names.discard('front_recontact_headroom_v2_stage_source_binding.py')
mapping={n[:-3]:n[:-3].replace('front_recontact_headroom_','front_box_recenter_a2_',1) for n in names}
mapping.update(front_recontact_headroom_v2_stage_source_binding='front_box_recenter_stage_source_binding',audit_front_recontact_headroom_stream='audit_front_box_recenter_stream',staged_front_recontact_headroom='staged_front_box_recenter_v3',FRONT_RECONTACT_HEADROOM_='FRONT_BOX_RECENTER_A2_')
mapping['FRONT_RECONTACT_HEADROOM_STREAM_AUDIT.json']='FRONT_BOX_RECENTER_STREAM_AUDIT.json'
pattern=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)));inverse={v:k for k,v in mapping.items()};assert len(inverse)==len(mapping);back=re.compile('|'.join(re.escape(k) for k in sorted(inverse,key=len,reverse=True)));pending=[]
for n in sorted(names):
 src=W/n;dst=W/(mapping[src.stem]+'.py');assert not dst.exists(),dst;original=src.read_text();text=pattern.sub(lambda m:mapping[m.group()],original);ast.parse(text);assert back.sub(lambda m:inverse[m.group()],text)==original;pending.append((src,dst,text))
side_edits={
'audit_front_box_recenter_a2_normal_rows.py':[("assert not verified_front_recovery_events or side=='left'","assert all(e['context']['scene']['side']==side and (side=='left' or e.get('front_box_recenter_version')=='front_box_recenter_v1') for e in verified_front_recovery_events.values())")],
'front_box_recenter_a2_reference_ledger.py':[("assert not verified_recovery_events or side=='left'","assert all(e['context']['scene']['side']==side and (side=='left' or e.get('front_box_recenter_version')=='front_box_recenter_v1') for e in verified_recovery_events.values())"),("assert side=='left' and b['kind'] in ('command','handover')","assert b['context']['scene']['side']==side and b['kind'] in ('command','handover')")],
'audit_front_box_recenter_a2_v1_stage_self_clearance.py':[("assert c['active_side']=='left' and verified_events[t]['context']['recontacts']>0","assert c['active_side']==verified_events[t]['context']['scene']['side']==('right' if task=='push_box_to_bin' else 'left') and verified_events[t]['context']['recontacts']>0")],
'front_box_recenter_a2_loaded_episode_inputs.py':[("assert self.front['selected'] and self.side=='left' and set(recovery_rows)==set(range(1,self.n))","assert self.front['selected'] and all(r.get('context',{}).get('scene',{}).get('side',self.side)==self.side for r in recovery_rows.values()) and set(recovery_rows)==set(range(1,self.n))")]
}
side_edits['audit_front_box_recenter_a2_v3_stage_self_clearance.py']=side_edits['audit_front_box_recenter_a2_v1_stage_self_clearance.py']
side_edits['audit_front_box_recenter_a2_task_rows.py']=[("assert c['active_side']=='left' and verified_events[t]['context']['recontacts']>0","assert c['active_side']==side==verified_events[t]['context']['scene']['side'] and verified_events[t]['context']['recontacts']>0")]
rows=[]
for src,dst,text in pending:
 original_mapped=text
 for a,b in side_edits.get(dst.name,[]):
  assert text.count(a)==1,(dst.name,a);text=text.replace(a,b)
 ast.parse(text)
 restored=text
 for a,b in reversed(side_edits.get(dst.name,[])):restored=restored.replace(b,a)
 assert restored==original_mapped

 with dst.open('x') as f:f.write(text)
 rows.append(dict(parent=str(src),parent_sha256=sha(src),path=str(dst),sha256=sha(dst),side_edits=side_edits.get(dst.name,[])))
files=[Path(__file__),P/'AUDIT_FAMILY_PREPARATION.json',S/'INDEPENDENT_STREAM_CHECK.json',S/'SOURCE_BINDING_CHECK.json',W/'front_box_recenter_stage_source_binding.py',W/'audit_front_box_recenter_stream.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=rows,replacements=mapping,syntax_and_inverse_restore_passed=True,side_guards_bound_to_verified_scene=True,expected_full_invocations=214,source_sha256={str(p):sha(p) for p in files},full_audit_family_ready=False,physical_started=False,training_ready=False)
with (S/'AUDIT_FAMILY_V2_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(adapters=len(rows),full_audit_family_ready=False))
