"""Temporary synthetic command logs over real poses test the independent auditor.
Never executed, never copied into a data run, never training evidence.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,json,tempfile,subprocess,sys,importlib.util,hashlib
import numpy as np
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_bounded_top_lead';sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
name='simfoundry.data.bounded_top_lead';spec=importlib.util.spec_from_file_location(name,stage/'bounded_top_lead.py');helper=importlib.util.module_from_spec(spec);sys.modules[name]=helper;spec.loader.exec_module(helper)
source=(stage/'collect_paired_sorting.py').read_text();blocks=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.If) and ast.unparse(n.test)=='bounded_top_lead is not None'];assert len(blocks)==1;code=compile(ast.Module(body=blocks,type_ignores=[]),'actual staged transition fixture','exec');reports=[]
with tempfile.TemporaryDirectory(prefix='unexecuted_lead_audit_') as directory:
 for layout,task in ((62013,'nudge_mailer_to_bin'),(62013,'push_box_to_bin'),(62012,'push_box_to_bin')):
  original=root/f'contact_center_groups_r1/case_{layout}'/(f'layout_{layout}_'+task);ep=Path(directory)/str(layout)/task/original.name;ep.mkdir(parents=True)
  for f in ('raw.npz','trace.npz','parcel_orientation.npz','solved_contact_forces.json','contact_center_calibration.json'):
   if (original/f).exists():(ep/f).symlink_to(original/f)
  provenance=json.loads((original.parent/'provenance.json').read_text());provenance['args']['expert_top_object_relative_lead_m']=.024;(ep.parent/'provenance.json').write_text(json.dumps(provenance))
  fr=json.loads((original/'frontal_bypass.json').read_text());fr['plan']['bounded_top_object_lead']=dict(enabled=True,desired_axis_lead_m=.024);state=NS(rear=NS(plan=fr['plan']),route_report=fr['plan'].get('front_route_candidates'),drag_step_m=.003,command=None);cal={r['step']:r for r in json.loads((ep/'contact_center_calibration.json').read_text())['rows']} if (ep/'contact_center_calibration.json').exists() else {};key='box' if task.startswith('push') else 'mailer';positions=np.load(ep/'trace.npz')[key];controller=helper.BoundedTopLead(.024);altered=[]
  for row in fr['rows']:
   t=row['step'];scope=dict(bounded_top_lead=controller,frontal_state=state,waypoint=copy.deepcopy(row),contact_center_calibration=NS(center_local=[0,0,0] if cal.get(t,{}).get('calibrated_after',False) else None),parcel_xyz=lambda env,actor,t=t:positions[t].tolist(),env=None,target_actor=key);exec(code,scope);altered.append(scope['waypoint'])
  fr['rows']=altered;payload=json.dumps(fr);(ep/'frontal_bypass.json').write_text(payload)
  proc=subprocess.run([sys.executable,str(root/'audit_bounded_top_lead_live.py'),str(ep)],capture_output=True,text=True)
  assert proc.returncode==0,proc.stdout+proc.stderr
  actual=json.loads((ep/'BOUNDED_TOP_LEAD_LIVE_AUDIT.json').read_text());assert actual['enabled'] and actual['checked_override_frames']==sum('bounded_top_object_lead' in r for r in altered)
  if actual['checked_override_frames']:
   changed=next(r for r in fr['rows'] if 'bounded_top_object_lead' in r);changed['target_xyz']=list(changed['target_xyz']);changed['target_xyz'][0]+=.01
   negative='10mm_command_tamper'
  else:
   fr['rows'].append(dict(step=1,mode='top_push',target_xyz=[0,0,0]));negative='uncalibrated_top_in_side_push'
  (ep/'frontal_bypass.json').write_text(json.dumps(fr))
  bad=subprocess.run([sys.executable,str(root/'audit_bounded_top_lead_live.py'),str(ep)],capture_output=True,text=True);assert bad.returncode!=0,'Tampered command accepted'
  reports.append(dict(episode=original.name,fixture_positive_passed=True,checked_frames=actual['checked_override_frames'],max_reconstruction_error_m=actual['max_reconstruction_error_m'],negative=negative,negative_rejected=True,original_raw_sha256=sha(original/'raw.npz')))
out=dict(rows=reports,candidate_sha256={n:sha(stage/n) for n in ('collect_paired_sorting.py','bounded_top_lead.py')},auditor_sha256=sha(root/'audit_bounded_top_lead_live.py'),checker_sha256=sha(__file__),scope='Temporary synthetic command rows from actual staged AST over unchanged real poses; real action arrays were not changed or executed. Independent math/lifecycle auditor fixture and tamper rejection only. No enabled physics evidence, model or data admission. Temporary files removed.',training_ready=False)
(stage/'AUDITOR_FIXTURE_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
