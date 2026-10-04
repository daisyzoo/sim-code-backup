"""Freeze a new collector stage for version admission repair, without physics.
Original failed stage/protocol remain unchanged. Two audit consumers are isolated
as candidates; full audit-family/source integration is still required.
"""
from pathlib import Path
import ast,json,hashlib,datetime,shutil,copy
W=Path(__file__).resolve().parent;P=W/'front_box_trailing_admission_preparation_r2';S=W/'staged_front_box_trailing_v1';T=W/'staged_front_box_trailing_v2';C=W/'front_box_trailing_admission_fix_candidate_v1';P.mkdir(exist_ok=False);T.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
proof=read(C/'NATIVE_ADMISSION_CHECK.json');assert proof['passed'] and proof['native_saved_events']==392
for p,h in proof['source_sha256'].items():assert sha(p)==h,p
parent={}
for p in S.iterdir():
 if p.is_file():assert not p.is_symlink();parent[p.name]=sha(p);shutil.copy2(p,T/p.name)
name='waist_coordination_clearance.py';shutil.copy2(C/name,T/name);edit=proof['only_edit'];assert (T/name).read_text().replace(edit['new'],edit['old'])==(S/name).read_text()
for n,h in parent.items():assert n==name or sha(T/n)==h,n
old="e.get('front_box_recenter_version')=='front_box_recenter_v1'";new="e.get('front_box_recenter_version') in ('front_box_recenter_v1','front_box_trailing_20mm_reserve_05mm_v1')";consumers=[]
event_source=W/'joint_transport_reserve_physical_r1/case_840020/layout_840020_push_box_to_bin/front_recontact_center.json';events={r['step']:r for r in read(event_source)['rows'] if r['kind'] in ['command','handover']}
for filename,var in [('audit_front_box_trailing_r1_normal_rows.py','verified_front_recovery_events'),('front_box_trailing_r1_reference_ledger.py','verified_recovery_events')]:
 p=W/filename;text=p.read_text();assert text.count(old)==1;modified=text.replace(old,new);assert modified.replace(new,old)==text;(C/filename).write_text(modified)
 def guard(source):
  node=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assert) and 'front_box_recenter_version' in ast.unparse(n.test));return compile(ast.Expression(node.test),'<actual verified event version assertion>','eval')
 original=guard(text);fixed=guard(modified);ctx=dict(side='right',**{var:events});assert eval(original,ctx) and eval(fixed,ctx)
 changed=copy.deepcopy(events)
 for e in changed.values():e['front_box_recenter_version']='front_box_trailing_20mm_reserve_05mm_v1'
 ctx=dict(side='right',**{var:changed});assert not eval(original,ctx) and eval(fixed,ctx)
 bad=copy.deepcopy(changed);next(iter(bad.values()))['front_box_recenter_version']='unknown';assert not eval(fixed,dict(side='right',**{var:bad}))
 bad=copy.deepcopy(changed);next(iter(bad.values()))['context']['scene']['side']='left';assert not eval(fixed,dict(side='right',**{var:bad}))
 consumers.append(dict(parent=str(p),parent_sha256=sha(p),candidate=str(C/filename),candidate_sha256=sha(C/filename),events=len(events),default_original_preserved=True,trailing_events_accepted=True,unknown_version_rejected=True,wrong_side_rejected=True,edit=dict(old=old,new=new)))
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(S),stage=str(T),parent_files=parent,stage_sha256={n:sha(T/n) for n in parent},changed_files={name:edit},collector_entry_unchanged=True,archive_already_includes_changed_guard=True,guard_runtime_native_check=str(C/'NATIVE_ADMISSION_CHECK.json'),audit_consumer_candidates=consumers,source_sha256={str(p):sha(p) for p in [Path(__file__),C/'NATIVE_ADMISSION_CHECK.json',event_source]},full_audit_family_ready=False,native_full_collector_check_pending=True,physical_launch_ready=False,physics_started=False,training_ready=False)
with (P/'STAGE_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(prepared=True,stage_files=len(parent),changed_stage_files=1,audit_consumers=2,saved_events_each=len(events),physical_started=False)))
