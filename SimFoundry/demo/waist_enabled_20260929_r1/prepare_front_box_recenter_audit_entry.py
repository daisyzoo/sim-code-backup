"""Bind right-box v3 source and extend original independent stream to both sides."""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;S=W/'staged_front_box_recenter_v3';D=W/'front_box_recenter_draft_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
def save(name,text,parent):
 ast.parse(text);p=W/name
 with p.open('x') as f:f.write(text)
 records.append(dict(path=str(p),sha256=sha(p),parent=str(parent),parent_sha256=sha(parent)))
parent=W/'front_inactive_clearance_stage_source_binding.py';text=parent.read_text().replace('all 79 archived','all 81 archived').replace("S=W/'staged_front_inactive_clearance'","S=W/'staged_front_box_recenter_v3'")
text=text.replace("new={'inactive_clearance_lifecycle.py','inactive_clearance_proposal.py'}","new={'front_box_recenter_'+v+'.py' for v in ['lifecycle_static','selection','lifecycle','runtime']}")
text=text.replace('len(expected)==79','len(expected)==81').replace("{'collect_paired_sorting.py','front_recontact_center_runtime.py'}","{'collect_paired_sorting.py','waist_coordination_clearance.py'}")
a=" for n in new:assert sha(S/n)==sha(W/'inactive_hand_headroom_draft_r1'/n)";b=""" for n in new:
  restored=(S/n).read_text()
  for e in reversed(prep['new_source_edits'].get(n,[])):
   assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
  assert restored==(W/'front_box_recenter_draft_r1'/n).read_text()
 assert set(prep['new_source_edits'])=={'front_box_recenter_runtime.py'}""";assert text.count(a)==1;text=text.replace(a,b)
text=text.replace("['PARSER_CHECK.json','RUNTIME_JOINT_CHECK.json','INDEPENDENT_EVENT_CHECK.json']","['PARSER_CHECK.json','COLLECTOR_HOOK_CHECK.json','DISPATCH_GUARD_CHECK.json']")
text=text.replace('front_recontact_inactive_clearance','front_box_recenter').replace("['inactive_clearance']","['box_recenter']").replace("['front_inactive_clearance']","['front_box_recenter']")
text=text.replace("selected=bool(task=='nudge_mailer_to_bin' and plan.get('front_route_selected'))","selected=bool(task in ('nudge_mailer_to_bin','push_box_to_bin') and plan.get('front_route_selected'))")
a="  assert plan['front_recontact_center_landing']==expected\n  assert plan['front_box_recenter']==spec";b="""  if task=='nudge_mailer_to_bin':
   assert plan['front_recontact_center_landing']==expected and 'front_box_recenter' not in plan
   assert all('front_box_recenter_version' not in r for r in data['rows'])
  else:
   assert plan['front_box_recenter']==spec and 'front_recontact_center_landing' not in plan
   assert all(r.get('front_box_recenter_version')=='front_box_recenter_v1' for r in data['rows'])""";assert text.count(a)==1;text=text.replace(a,b)
save('front_box_recenter_stage_source_binding.py',text,parent)
parent=W/'audit_front_recontact_headroom_stream.py';text=parent.read_text().replace("S=W/'staged_front_recontact_headroom'","S=W/'staged_front_box_recenter_v3'")
a="sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()";b=a+"\nimport importlib.util\n_spec=importlib.util.spec_from_file_location('independent_box_events',W/'front_box_recenter_draft_r1/audit_front_box_recenter_events.py')\n_box_events=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_box_events)\nBoxRecoveryEventAudit=_box_events.RecoveryEventAudit"
assert text.count(a)==1;text=text.replace(a,b)
text=text.replace('def __init__(self,repo,stage):','def __init__(self,repo,stage,side="left"):\n  assert side in ("left","right");self.side=side;self.inactive="right" if side=="left" else "left"')
text=text.replace('self.audit=RecoveryEventAudit(self.repo,self.stage)','self.audit=(BoxRecoveryEventAudit if self.side=="right" else RecoveryEventAudit)(self.repo,self.stage)')
text=text.replace("self.selection.hand.fk(current,'left')","self.selection.hand.fk(current,self.side)").replace("self.selection.hand.fk(current,'right')","self.selection.hand.fk(current,self.inactive)").replace("self.selection.hand.vertices['left']","self.selection.hand.vertices[self.side]").replace("coordinate['active_side']=='left'","coordinate['active_side']==self.side")
a="  assert type(step) is int and step==self.last_step+1";b="""  assert scene['side']==self.side
  if self.side=='right':assert event.get('front_box_recenter_version')=='front_box_recenter_v1'
  else:assert 'front_box_recenter_version' not in event
"""+a;assert text.count(a)==1;text=text.replace(a,b)
a="selected=bool(task=='nudge_mailer_to_bin' and fr['plan'].get('front_route_selected'))";assert text.count(a)==1;text=text.replace(a,"selected=bool(fr['plan'].get('front_route_selected'))")
a=" with np.load(ep/'trace.npz') as z:target=z['mailer'].astype(float);other=z['box'].astype(float)\n with np.load(ep/'parcel_orientation.npz') as z:tq=z['mailer'].astype(float);oq=z['box'].astype(float)";b=""" side='right' if task=='push_box_to_bin' else 'left';target_key='box' if side=='right' else 'mailer';other_key='mailer' if side=='right' else 'box'
 actor='parcel_box' if side=='right' else 'mailer'
 with np.load(ep/'trace.npz') as z:target=z[target_key].astype(float);other=z[other_key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:tq=z[target_key].astype(float);oq=z[other_key].astype(float)""";assert text.count(a)==1;text=text.replace(a,b)
text=text.replace('checker=RecoveryStreamAudit(ROOT,S)','checker=RecoveryStreamAudit(ROOT,S,side)')
text=text.replace("any('left_wrist_roll' in name for name in c['shapes']) and any('/mailer/' in name for name in c['shapes'])","any(side+'_wrist_roll' in name for name in c['shapes']) and any('/'+actor+'/' in name for name in c['shapes'])")
text=text.replace("scene=dict(side='left',target_xyz=", "scene=dict(side=side,target_xyz=").replace('other_size=[.14,.09,.045])','other_size=([.15,.145,.04] if side=="right" else [.14,.09,.045]))')
text=text.replace('from front_recontact_headroom_v2_stage_source_binding import verify_observation_binding','from front_box_recenter_stage_source_binding import verify_observation_binding').replace("'FRONT_RECONTACT_HEADROOM_STREAM_AUDIT.json'","'FRONT_BOX_RECENTER_STREAM_AUDIT.json'")
text=text.replace("W/'audit_front_recontact_center_events.py',", "W/'audit_front_recontact_center_events.py',W/'front_box_recenter_draft_r1/audit_front_box_recenter_events.py',")
save('audit_front_box_recenter_stream.py',text,parent)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256={str(p):sha(p) for p in [Path(__file__),S/'COLLECTOR_PREPARATION.json',D/'audit_front_box_recenter_events.py']},native_checks_pending=True,training_ready=False)
with (S/'AUDIT_ENTRY_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(files=len(records),checks_pending=True)))
