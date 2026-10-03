"""Versioned native initial/normal audit adaptation; original math stays frozen."""
from pathlib import Path
import hashlib,json,datetime
W=Path(__file__).resolve().parent;S=W/'staged_front_recontact_center';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
def write(parent,new,changes):
 p=W/parent;t=W/new;s=p.read_text();edits=[]
 for a,b in changes:
  assert s.count(a)==1,(new,a[:80],s.count(a));s=s.replace(a,b,1);edits.append(dict(old=a,new=b))
 with t.open('x') as f:f.write(s)
 back=s
 for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'],1)
 assert back==p.read_text();records.append(dict(parent=str(p),target=str(t),parent_sha256=sha(p),target_sha256=sha(t),changes=edits))
write('audit_front_drive_1mm_v2_initial_live.py','audit_front_recontact_initial_live.py',[
 ("S=W/'staged_front_drive_1mm'","S=W/'staged_front_recontact_center'"),
 ('def verify_files(ep):\n ep=Path(ep)','def verify_files(ep, *, verified_recovery_events=None):\n ep=Path(ep)\n if verified_recovery_events is None:\n  from audit_front_recontact_stream import verify_files as verify_recovery_files\n  recovery_result=verify_recovery_files(ep)\n  verified_recovery_events={r[\'step\']:{k:v for k,v in r.items() if k!=\'step\'} for r in json.loads((ep/\'front_recontact_center.json\').read_text())[\'rows\'] if r[\'kind\'] in (\'command\',\'handover\')}\n  assert set(verified_recovery_events)=={r[\'step\'] for r in recovery_result[\'rows\']}\n recovery_center=recovery_normal=recovery_anchor=None'),
 ("  if center is not None:\n   near(coordinate['inactive_anchor'],captured_anchor,1e-9)","  recovery_event=verified_recovery_events.get(t)\n  if recovery_event is not None:\n   assert event['kind']=='unchanged' and recovery_event['kind'] in ('command','handover')\n   if recovery_event['kind']=='handover':\n    recovery_center=np.array(recovery_event['captured_center_local']);recovery_normal=recovery_event['captured_normal_local_up'];recovery_anchor=recovery_event['captured_inactive_anchor_world']\n  if center is not None:\n   near(coordinate['inactive_anchor'],recovery_anchor if recovery_anchor is not None else captured_anchor,1e-9)"),
 ("   reference=center+normal_local*(np.min(vertices@normal_local)-center@normal_local)\n   near(row['projected_support_reference']['center_local'],center,0)","   active_center=recovery_center if recovery_center is not None else center\n   reference=active_center+normal_local*(np.min(vertices@normal_local)-active_center@normal_local)\n   near(row['projected_support_reference']['center_local'],active_center,0)"),
 ("and event['kind'] not in ('command','handover'):","and event['kind'] not in ('command','handover') and recovery_event is None:"),
 ("near(coordinate['contact_normal_tracking']['target_local_up'],captured_normal,2e-6)","near(coordinate['contact_normal_tracking']['target_local_up'],recovery_normal if recovery_normal is not None else captured_normal,2e-6)"),
 ('from front_drive_1mm_v2_stage_source_binding import verify_observation_binding','from front_recontact_stage_source_binding import verify_observation_binding'),
 ("names=['raw.npz','front_initial_center.json'","names=['front_recontact_center.json','raw.npz','front_initial_center.json'"),
 ("'FRONT_INITIAL_CENTER_LIVE_V2_AUDIT.json'","'FRONT_RECONTACT_INITIAL_LIVE_AUDIT.json'")])
write('audit_front_initial_center_normal.py','audit_front_recontact_normal_rows.py',[
 ('*,enabled=True,verified_front_events=None):','*,enabled=True,verified_front_events=None,verified_front_recovery_events=None):'),
 ("    assert not set(verified_events)&set(verified_front_events)\n    verified_events={**verified_events,**verified_front_events}","    verified_front_recovery_events={} if verified_front_recovery_events is None else verified_front_recovery_events\n    assert not set(verified_events)&set(verified_front_events)\n    assert not (set(verified_events)|set(verified_front_events))&set(verified_front_recovery_events)\n    assert not verified_front_recovery_events or side=='left'\n    verified_events={**verified_events,**verified_front_events,**verified_front_recovery_events}"),
 ("controller,field=('verified_unloaded_front_initial_joint_path','front_initial_center_override') if t in verified_front_events else ('verified_unloaded_recontact_joint_path','recontact_pose_override')","controller,field=('verified_unloaded_front_recontact_joint_path','front_recontact_center_override') if t in verified_front_recovery_events else ('verified_unloaded_front_initial_joint_path','front_initial_center_override') if t in verified_front_events else ('verified_unloaded_recontact_joint_path','recontact_pose_override')"),
 ("            assert row.get('recontact_pose_override' if t in verified_front_events else 'front_initial_center_override') is None","            assert all(row.get(k) is None for k in ('recontact_pose_override','front_initial_center_override','front_recontact_center_override') if k!=field)\n            if t in verified_front_recovery_events:assert event['context']['recontacts']>0 and event['real_recontact_index']==event['context']['recontacts']"),
 ("assert row.get('controller_kind') not in ('verified_unloaded_recontact_joint_path','verified_unloaded_front_initial_joint_path')","assert row.get('controller_kind') not in ('verified_unloaded_recontact_joint_path','verified_unloaded_front_initial_joint_path','verified_unloaded_front_recontact_joint_path')"),
 ("assert row.get('recontact_pose_override') is None and row.get('front_initial_center_override') is None","assert row.get('recontact_pose_override') is None and row.get('front_initial_center_override') is None and row.get('front_recontact_center_override') is None")])
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256={str(Path(__file__)):sha(__file__)},inverse_restore_passed=True,full_audit_family_ready=False,simulation_started=False,training_ready=False)
with (S/'CAPTURE_AUDIT_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print('prepared2 capture audit adapters')
