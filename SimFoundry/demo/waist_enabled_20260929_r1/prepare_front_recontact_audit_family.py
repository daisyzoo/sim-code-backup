"""Prepare isolated full audit family with distinct verified front-recovery events.
Original204 checks retained; add explicit full recovery-stream audit per condition.
This preparation does not imply imports, fixture checks or physics are complete.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;S=W/'staged_front_recontact_center';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=json.loads((W/'FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json').read_text())
renames=[('front_drive_1mm_v2_stage_source_binding','front_recontact_stage_source_binding'),('audit_front_drive_1mm_v2_initial_live','audit_front_recontact_initial_live'),('staged_front_drive_1mm','staged_front_recontact_center'),('front_drive_1mm_v2','front_recontact_v1'),('FRONT_DRIVE_1MM_V2','FRONT_RECONTACT_V1'),('audit_front_initial_center_normal','audit_front_recontact_normal_rows'),('audit_front_initial_center_task_rows','audit_front_recontact_task_rows')]
def rename(s):
 for a,b in renames:s=s.replace(a,b)
 return s
inputs=[Path(x['path']) for x in parent['adapters'] if Path(x['path']).name not in ['front_drive_1mm_v2_stage_source_binding.py','audit_front_drive_1mm_v2_initial_live.py']]+[W/'audit_front_initial_center_task_rows.py'];pending=[]
for p in inputs:
 s=rename(p.read_text());edits=[]
 def change(a,b):
  global s
  assert s.count(a)==1,(p.name,a[:100],s.count(a));s=s.replace(a,b,1);edits.append(dict(old=a,new=b))
 if p.name=='front_drive_1mm_v2_stage_audit_context.py':
  s+='''\n\ndef verified_front_recovery_events(ep):
    from audit_front_recontact_v1_stage_pose_live import inspect
    ep=Path(ep);result=inspect(ep)
    assert result==json.loads((ep/'FRONT_RECONTACT_V1_STAGE_POSE_LIVE_V2_AUDIT.json').read_text())
    data=json.loads((ep/'front_recontact_center.json').read_text())
    events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in data['rows'] if r['kind'] in ('command','handover')}
    assert set(events)=={r['step'] for r in result['front_recovery_records']}
    return events
'''
  edits.append(dict(old='',new=s[len(rename(p.read_text())):]))
 if p.name=='audit_front_drive_1mm_v2_stage_pose_live.py':
  change("FILES=['front_initial_center.json'","FILES=['front_recontact_center.json','front_initial_center.json'")
  change('    front_result=verify_front_files(ep)',"    from audit_front_recontact_stream import verify_files as verify_recovery_files\n    recovery_result=verify_recovery_files(ep)\n    recovery_events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'front_recontact_center.json').read_text())['rows'] if r['kind'] in ('command','handover')}\n    assert set(recovery_events)=={r['step'] for r in recovery_result['rows']}\n    front_result=verify_front_files(ep,verified_recovery_events=recovery_events)")
  change("    assert set(front_events)=={r['step'] for r in front_result.get('rows',[])}","    assert set(front_events)=={r['step'] for r in front_result.get('rows',[])}\n    assert not set(front_events)&set(recovery_events)")
  change("        if t in front_events:\n            fe=front_events[t];assert event is None and not selected\n            assert f['front_initial_center_phase']==('measured_handover' if fe['kind']=='handover' else 'tracking')","        if t in front_events or t in recovery_events:\n            fe=front_events[t] if t in front_events else recovery_events[t];assert event is None and not selected\n            field='front_initial_center_phase' if t in front_events else 'front_recontact_center_phase'\n            assert f[field]==('measured_handover' if fe['kind']=='handover' else 'tracking')")
  change('verified_front_events=front_events)','verified_front_events=front_events,verified_front_recovery_events=recovery_events)')
  change('front_result=front_result,normal=normal','front_result=front_result,front_recovery_records=recovery_result["rows"],front_recovery_result=recovery_result,normal=normal')
  change("'audit_front_recontact_initial_live.py','audit_front_initial_center_planning_v2.py'","'audit_front_recontact_initial_live.py','audit_front_recontact_stream.py','audit_front_recontact_center_events.py','audit_front_initial_center_planning_v2.py'")
 if p.name=='audit_front_drive_1mm_v2_stage_normal_live.py':
  change('import verified_events,verified_front_events','import verified_events,verified_front_events,verified_front_recovery_events')
  change('front=verified_front_events(ep)','front=verified_front_events(ep);recovery=verified_front_recovery_events(ep)')
  change('verified_front_events=front)','verified_front_events=front,verified_front_recovery_events=recovery)')
  change("['front_initial_center.json','FRONT_RECONTACT_V1_STAGE_POSE", "['front_recontact_center.json','front_initial_center.json','FRONT_RECONTACT_V1_STAGE_POSE")
 if p.name=='audit_front_drive_1mm_v2_stage_region_reference.py':
  change('import verified_events,verified_front_events','import verified_events,verified_front_events,verified_front_recovery_events')
  change('from front_initial_center_reference_ledger import verified_reference_lifetimes','from front_recontact_reference_ledger import verified_reference_lifetimes')
  change(' front=verified_front_events(ep)\n if front:',' front=verified_front_events(ep);recovery=verified_front_recovery_events(ep)\n if front or recovery:')
  change('result=verified_reference_lifetimes(rows,front)',"result=verified_reference_lifetimes(rows,front,recovery,side='right' if 'push_box' in ep.name else 'left')")
  change("w/'front_initial_center_reference_ledger.py'","w/'front_recontact_reference_ledger.py'")
 if p.name in ['audit_front_drive_1mm_v2_stage_self_clearance.py','audit_front_initial_center_task_rows.py']:
  change('*,verified_front_events=None):','*,verified_front_events=None,verified_front_recovery_events=None):')
  a=" assert not set(verified_events)&set(verified_front_events)\n verified_events={**verified_events,**verified_front_events}"
  extra=" verified_front_recovery_events={} if verified_front_recovery_events is None else verified_front_recovery_events\n"
  if p.name.endswith('self_clearance.py'):
   extra=" if verified_front_recovery_events is None:\n  if task=='wait_no_package':verified_front_recovery_events={}\n  else:\n   from front_recontact_v1_stage_audit_context import verified_front_recovery_events as checked_recovery\n   verified_front_recovery_events=checked_recovery(ep)\n"
  change(a,extra+" assert not set(verified_events)&set(verified_front_events)\n assert not (set(verified_events)|set(verified_front_events))&set(verified_front_recovery_events)\n verified_events={**verified_events,**verified_front_events,**verified_front_recovery_events}")
  change("in ('verified_unloaded_recontact_joint_path','verified_unloaded_front_initial_joint_path'):","in ('verified_unloaded_recontact_joint_path','verified_unloaded_front_initial_joint_path','verified_unloaded_front_recontact_joint_path'):")
  change("kind,field=('verified_unloaded_front_initial_joint_path','front_initial_center_override') if t in verified_front_events else ('verified_unloaded_recontact_joint_path','recontact_pose_override')","kind,field=('verified_unloaded_front_recontact_joint_path','front_recontact_center_override') if t in verified_front_recovery_events else ('verified_unloaded_front_initial_joint_path','front_initial_center_override') if t in verified_front_events else ('verified_unloaded_recontact_joint_path','recontact_pose_override')")
  change("   assert c.get('recontact_pose_override' if t in verified_front_events else 'front_initial_center_override') is None","   assert all(c.get(k) is None for k in ('recontact_pose_override','front_initial_center_override','front_recontact_center_override') if k!=field)\n   if t in verified_front_recovery_events:assert c['active_side']=='left' and verified_events[t]['context']['recontacts']>0 and verified_events[t]['real_recontact_index']==verified_events[t]['context']['recontacts']")
 if p.name=='audit_front_drive_1mm_v2_stage_task_optimality.py':
  change(" assert set(front)=={r['step'] for r in pose['front_records']}"," assert set(front)=={r['step'] for r in pose['front_records']}\n recovery={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'front_recontact_center.json').read_text())['rows'] if r['kind'] in ('command','handover')}\n assert set(recovery)=={r['step'] for r in pose['front_recovery_records']}")
  change('verified_front_events=front)','verified_front_events=front,verified_front_recovery_events=recovery)')
 if p.name=='audit_front_drive_1mm_v2_stage_front_height.py':
  change('*,verified_front_events=None):','*,verified_front_events=None,verified_front_recovery_events=None):')
  change(' verified_front_events={} if verified_front_events is None else verified_front_events'," verified_front_events={} if verified_front_events is None else verified_front_events\n verified_front_recovery_events={} if verified_front_recovery_events is None else verified_front_recovery_events\n assert not set(verified_front_events)&set(verified_front_recovery_events)\n assert set(verified_front_recovery_events)<={r['step'] for r in log['rows']}")
  change("  if mode=='top_cross' and t not in verified_front_events", "  if t in verified_front_recovery_events:\n   event=verified_front_recovery_events[t];assert event['kind'] in ('command','handover') and count>0\n   assert event['context']['recontacts']==event['real_recontact_index']==count\n   assert mode==('top_press' if event['kind']=='handover' else 'top_cross')\n   assert r['front_recontact_center_phase']==('measured_handover' if event['kind']=='handover' else 'tracking')\n  if mode=='top_cross' and t not in verified_front_events and t not in verified_front_recovery_events")
  change('import verified_front_events\n result=', 'import verified_front_events,verified_front_recovery_events\n result=')
  change('verified_front_events=verified_front_events(ep))','verified_front_events=verified_front_events(ep),verified_front_recovery_events=verified_front_recovery_events(ep))')
 if p.name=='front_drive_1mm_v2_stage_run_contract.py':
  change("return ['audit_front_recontact_v1_execution.py']+","return ['audit_front_recontact_v1_execution.py','audit_front_recontact_stream.py']+")
  change("ADDITIONAL=['audit_front_recontact_v1_stage_region_continuity.py'","REPORTS['audit_front_recontact_stream.py']=('FRONT_RECONTACT_STREAM_AUDIT.json',('passed',))\nADDITIONAL=['audit_front_recontact_v1_stage_region_continuity.py'")
 ast.parse(s);back=s
 for e in reversed(edits):
  assert back.count(e['new'])==1,(p.name,'inverse');back=back.replace(e['new'],e['old'],1)
 assert back==rename(p.read_text()),p
 dest=W/rename(p.name);assert not dest.exists(),dest;pending.append((p,dest,s,edits))
for p,dest,s,edits in pending:
 with dest.open('x') as f:f.write(s)
records=[dict(parent=str(p),parent_sha256=sha(p),path=str(dest),sha256=sha(dest),edits=edits) for p,dest,s,edits in pending]
proofs=[W/'FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json',Path(__file__),W/'front_recontact_stage_source_binding.py',W/'audit_front_recontact_stream.py',W/'audit_front_recontact_initial_live.py',W/'audit_front_recontact_normal_rows.py',W/'front_recontact_reference_ledger.py',S/'INDEPENDENT_STREAM_CHECK.json',S/'SOURCE_BINDING_CHECK.json',S/'INITIAL_REFERENCE_SWITCH_CHECK.json']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=records,global_replacements=renames,source_sha256={str(p):sha(p) for p in proofs},syntax_and_inverse_restore_passed=True,parent_invocations=204,expected_full_invocations=214,full_audit_family_ready=False,configuration_import_fixture_checks_pending=True,physics_started=False,training_ready=False)
with (S/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(modules=len(records),expected_checks=214,ready=False)))
