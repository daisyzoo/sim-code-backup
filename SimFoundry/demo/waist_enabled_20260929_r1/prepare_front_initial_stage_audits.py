"""Isolated native audit adapters, source/diff preparation only; not launch approval.
Retain margin originals and original geometry, normal and KKT math. Complete
combined native fixtures and remaining reference/pressure/height adapters required.
"""
from pathlib import Path
import json,hashlib,ast,datetime
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=[]
def base(name):
 p=W/name;s=p.read_text();s=s.replace('terminal_margin_stage','front_initial_stage').replace('TERMINAL_MARGIN_STAGE','FRONT_INITIAL_STAGE').replace('staged_terminal_release_margin','staged_front_initial_center');return p,s

def write(parent,s,edits):
 dest=W/parent.name.replace('terminal_margin_stage','front_initial_stage');assert not dest.exists();ast.parse(s);dest.write_text(s);records.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits))
def change(s,edits,old,new):
 assert s.count(old)==1,(old[:100],s.count(old));edits.append(dict(old=old,new=new));return s.replace(old,new)
# Source binding delegates to independently checked new stage binding.
p=W/'front_initial_stage_source_binding.py';assert not p.exists();p.write_text('"""Explicit alias for the isolated first-front stage source contract."""\nfrom front_initial_center_stage_source_binding import verify_trial_provenance, verify_observation_binding\n')
parent,s=base('audit_terminal_margin_stage_contract.py');write(parent,s,[])
parent,s=base('audit_terminal_margin_stage_pose_live.py');e=[]
s=change(s,e,'from audit_recontact_pose_normal import verify_normal_rows','from audit_front_initial_center_normal import verify_normal_rows\nfrom audit_front_initial_center_live_v2 import verify_files as verify_front_files')
s=change(s,e,"    ep=Path(ep)\n    with np.load", "    ep=Path(ep)\n    front_result=verify_front_files(ep)\n    front_events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'front_initial_center.json').read_text())['rows'] if r['kind'] in ('command','handover')}\n    assert set(front_events)=={r['step'] for r in front_result.get('rows',[])}\n    with np.load")
s=change(s,e,"        assert not (event and event['kind']=='stop'),'stopped recovery is not a passing episode'", """        assert not (event and event['kind']=='stop'),'stopped recovery is not a passing episode'
        if t in front_events:
            fe=front_events[t];assert event is None and not selected
            assert f['front_initial_center_phase']==('measured_handover' if fe['kind']=='handover' else 'tracking')
            assert t in holds and holds[t]['held'] is False
            near(holds[t]['output_upper_command'],u[t],0);near(holds[t]['previous_upper_command'],u[t-1],0);near(holds[t]['current_upper_q'],q[t],1e-7)
            assert final[t]['accepted'] is True
            near(final[t]['command'],u[t],0);near(final[t]['current'],q[t],1e-7);near(final[t]['previous'],u[t-1],0)
            if fe['kind']=='handover':
                near(f['target_xyz'],fe['observed_support_xyz'],1e-9);near(f['observed_support_xyz'],fe['observed_support_xyz'],1e-9)
                near(f['control_offset_local'],fe['reference']['reference_local'],1e-9)
                assert f['projected_support_reference']==c['active_support_reference']==fe['reference']
                near(c['control_point_positions'][side],fe['observed_support_xyz'],2e-6)
                assert f['push_x_anchor_m'] is None and f['approach_xy_bias_m']==[0.,0.]""")
s=change(s,e,'normal=verify_normal_rows(q,coords,experts,set(fs),verified,audit.hand,side)','normal=verify_normal_rows(q,coords,experts,set(fs),verified,audit.hand,side,verified_front_events=front_events)')
s=change(s,e,'records=records,normal=normal,scope=__doc__','records=records,front_records=front_result.get("rows",[]),front_result=front_result,normal=normal,scope=__doc__')
s=change(s,e,"FILES=['raw.npz'","FILES=['front_initial_center.json','raw.npz'")
s=change(s,e,"'audit_recontact_pose_normal.py','audit_unloaded_wrist_prior_live.py'", "'audit_front_initial_center_normal.py','audit_front_initial_center_live_v2.py','audit_front_initial_center_planning_v2.py','audit_front_initial_center_preflight.py','audit_front_initial_center_events.py','audit_unloaded_wrist_prior_live.py'")
write(parent,s,e)
parent,s=base('terminal_margin_stage_audit_context.py');e=[]
s+='''\n\ndef verified_front_events(ep):
    from audit_front_initial_stage_pose_live import inspect
    ep=Path(ep);result=inspect(ep)
    assert result==json.loads((ep/'FRONT_INITIAL_STAGE_POSE_LIVE_V2_AUDIT.json').read_text())
    events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'front_initial_center.json').read_text())['rows'] if r['kind'] in ('command','handover')}
    assert set(events)=={r['step'] for r in result['front_records']}
    return events
'''
e.append(dict(kind='append independently verified front event accessor'));write(parent,s,e)
parent,s=base('audit_terminal_margin_stage_normal_live.py');e=[]
s=change(s,e,'from front_initial_stage_audit_context import verified_events','from front_initial_stage_audit_context import verified_events,verified_front_events')
s=change(s,e,'from audit_recontact_pose_normal import verify_normal_rows','from audit_front_initial_center_normal import verify_normal_rows')
s=change(s,e,'ep=Path(ep);events=verified_events(ep)','ep=Path(ep);events=verified_events(ep);front=verified_front_events(ep)')
s=change(s,e,'events,model,side)','events,model,side,verified_front_events=front)')
s=change(s,e,"'raw.npz','coordination.json'","'front_initial_center.json','FRONT_INITIAL_STAGE_POSE_LIVE_V2_AUDIT.json','raw.npz','coordination.json'")
write(parent,s,e)
parent,s=base('audit_terminal_margin_stage_task_optimality.py');e=[]
old=s.split('def verify_task_rows(',1)[1].split('\ndef inspect(ep):',1)[0]
s=change(s,e,'def verify_task_rows('+old,'from audit_front_initial_center_task_rows import verify_task_rows\n')
s=change(s,e," assert set(events)=={r['step'] for r in pose['records']}"," assert set(events)=={r['step'] for r in pose['records']}\n front={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'front_initial_center.json').read_text())['rows'] if r['kind'] in ('command','handover')}\n assert set(front)=={r['step'] for r in pose['front_records']}")
s=change(s,e,'verify_task_rows(ep,geom,events)','verify_task_rows(ep,geom,events,verified_front_events=front)')
s=change(s,e," out.update(stationarity_version=VERSION", " out.update(task_row_auditor_sha256=sha(w/'audit_front_initial_center_task_rows.py'))\n out.update(stationarity_version=VERSION")
write(parent,s,e)
parent,s=base('audit_terminal_margin_stage_self_clearance.py');e=[]
s=change(s,e,'def audit(ep,verified_events=None):','def audit(ep,verified_events=None,*,verified_front_events=None):')
s=change(s,e," assert q.shape==u.shape==(count,11)"," if verified_front_events is None:\n  if task=='wait_no_package':verified_front_events={}\n  else:\n   from front_initial_stage_audit_context import verified_front_events as checked_front\n   verified_front_events=checked_front(ep)\n assert not set(verified_events)&set(verified_front_events)\n verified_events={**verified_events,**verified_front_events}\n assert q.shape==u.shape==(count,11)")
s=change(s,e,"  if c.get('controller_kind')=='verified_unloaded_recontact_joint_path':\n   assert t in verified_events and c['recontact_pose_override']==verified_events[t]", "  if c.get('controller_kind') in ('verified_unloaded_recontact_joint_path','verified_unloaded_front_initial_joint_path'):\n   kind,field=('verified_unloaded_front_initial_joint_path','front_initial_center_override') if t in verified_front_events else ('verified_unloaded_recontact_joint_path','recontact_pose_override')\n   assert c['controller_kind']==kind and t in verified_events and c[field]==verified_events[t]\n   assert c.get('recontact_pose_override' if t in verified_front_events else 'front_initial_center_override') is None")
write(parent,s,e)
manifest=W/'FRONT_INITIAL_STAGE_AUDITS_PREPARATION.json';assert not manifest.exists();manifest.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,generator_sha256=sha(__file__),global_replacements=[['terminal_margin_stage','front_initial_stage'],['TERMINAL_MARGIN_STAGE','FRONT_INITIAL_STAGE'],['staged_terminal_release_margin','staged_front_initial_center']],adapters=records,source_alias=dict(path=str(p),sha256=sha(p)),syntax_passed=True,combined_native_positive_tested=False,simulation_started=False,training_ready=False,remaining=['combined native pose/self clearance fixture','persistent center versus reset surface reference ledger','front height adapter','pressure/loaded/history binding','original release margin stability correction','complete audit inventory and run protocol']),indent=2));print('Prepared',len(records),'isolated adapters, syntax only; not ready to launch')
