"""Replay actual collector front-recovery admission block on saved command events.
Bind the old and trailing version mismatch; preserve every other original guard.
CPU statement execution only; no candidate physical outcome or missing failure
context is invented. Original failed collector and records remain immutable.
"""
from pathlib import Path
import ast,json,copy,hashlib,datetime,types
import numpy as np
import torch
W=Path(__file__).resolve().parent;S=W/'staged_front_box_trailing_v1';D=W/'front_box_trailing_admission_fix_candidate_v1';D.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=S/'waist_coordination_clearance.py';text=source.read_text();old="front_recontact_override.get('front_box_recenter_version')=='front_box_recenter_v1'";new="front_recontact_override.get('front_box_recenter_version') in ('front_box_recenter_v1','front_box_trailing_20mm_reserve_05mm_v1')";assert text.count(old)==1;modified=text.replace(old,new);assert modified.replace(new,old)==text;(D/source.name).write_text(modified)
def program(text):
 fn=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step');block=next(n for n in fn.body if isinstance(n,ast.If) and ast.unparse(n.test)=='front_recontact_override is not None');wrapper=ast.parse('def replay():\n pass');wrapper.body[0].body=[block];return compile(ast.fix_missing_locations(wrapper),'<actual front recovery admission>','exec')
original=program(text);candidate=program(modified)
def replay(code,event):
 current=np.asarray(event['context']['current'],dtype=np.float32);env=dict(np=np,torch=torch,front_recontact_override=event,robot=types.SimpleNamespace(data=types.SimpleNamespace(joint_pos=types.SimpleNamespace(torch=torch.tensor(current[None])))),joint_ids=list(range(11)),indices=list(range(12,23)),default=np.zeros(23),action=np.zeros(23),bounded=True,clearance_geometry=object(),previous_command=np.asarray(event['context']['previous_command']),state=types.SimpleNamespace(side='right'),palms={},points={},active_point_offset=None,active_support_reference=None,anchor={'left':np.zeros(3),'right':np.zeros(3)})
 exec(code,env);out=env['replay']();assert out['controller_kind']=='verified_unloaded_front_recontact_joint_path';np.testing.assert_array_equal(env['action'][12:23],np.asarray(event['command'],dtype=np.float32));return out
record=W/'joint_transport_reserve_physical_r1/case_840020/layout_840020_push_box_to_bin/front_recontact_center.json';data=json.loads(record.read_text());events=[r for r in data['rows'] if r['kind'] in ['command','handover']];assert len(events)==392
rows=[]
for e in events:
 assert e['front_box_recenter_version']=='front_box_recenter_v1';replay(original,e);replay(candidate,e);v=copy.deepcopy(e);v['front_box_recenter_version']='front_box_trailing_20mm_reserve_05mm_v1'
 try:replay(original,v)
 except ValueError as err:assert str(err)=='Front recovery override not currently unloaded'
 else:raise AssertionError('Original guard unexpectedly accepted trailing marker')
 replay(candidate,v);rows.append(dict(step=e['step'],kind=e['kind'],observed_load_n=e['context']['observed_load_n'],filtered_load_n=e['context']['filtered_load_n'],old_accepts_original=True,old_rejects_new_marker=True,fixed_accepts_both=True))
negatives=[];base=copy.deepcopy(events[0]);base['front_box_recenter_version']='front_box_trailing_20mm_reserve_05mm_v1'
changes=[('unknown_version',('front_box_recenter_version',),'unknown'),('guard_stop',('context','guard_stop'),True),('not_selected',('context','selected'),False),('loaded',('context','observed_load_n'),.001),('filtered_loaded',('context','filtered_load_n'),.051),('negative_filtered',('context','filtered_load_n'),-.001),('wrong_mode',('context','parent_mode'),'top_push'),('wrong_side',('context','scene','side'),'left'),('invalid_counter',('context','recontacts'),0),('wrong_real_counter',('real_recontact_index',),999),('geometry_rejected',('proposal','command_check','accepted'),False),('nominal_rejected',('proposal','nominal_scene','accepted'),False),('predicted_rejected',('proposal','predicted_scene','accepted'),False),('proposal_not_applied',('proposal','applied'),False)]
for label,path,value in changes:
 e=copy.deepcopy(base);obj=e
 for key in path[:-1]:obj=obj[key]
 obj[path[-1]]=value
 try:replay(candidate,e)
 except ValueError:negatives.append(label)
 else:raise AssertionError('Accepted invalid actual admission '+label)
paths=[Path(__file__),source,D/source.name,S/'trailing_runtime.py',S/'collect_paired_sorting.py',record,W/'front_box_trailing_physical_r1/STATUS.json',W/'front_box_trailing_physical_r1/case_840020/STATUS.json',W/'front_box_trailing_physical_r1/case_840020/progress.json']
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,native_saved_events=len(events),negative_rejections=negatives,rows=rows,source_sha256={str(p):sha(p) for p in paths},only_edit=dict(old=old,new=new),original_inverse_exact=True,physical_failure_actual_event_not_saved=True,interpretation='For any right trailing recovery command the old version predicate is false even with observed_load=0 and all other admission conditions satisfied. Actual failed event load is unavailable, so the generic error cannot be interpreted as proved residual load. Candidate repair admits the declared version while preserving original load/context/phase/proposal checks.',collector_integrated=False,audit_family_updated=False,physics_started=False,training_ready=False)
with (D/'NATIVE_ADMISSION_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,events=len(events),negative=len(negatives),physics_started=False)),flush=True)
