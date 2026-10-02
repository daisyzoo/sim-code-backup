from pathlib import Path
import sys,json,tempfile,os,copy,hashlib,datetime,ast,importlib
import numpy as np
W=Path('/home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1');S=W/'staged_terminal_directional_lead';sys.path[:0]=[str(S),str(W),str(W.parents[1])]
from terminal_directional_lead_state import DirectionalLeadFeedback
from audit_terminal_lead_stage_feedback import verify_measurements
from audit_terminal_margin_contact_stability_supplement import audit_files
from terminal_lead_stage_source_binding import verify_trial_provenance
import terminal_lead_stage_run_contract as new
import terminal_margin_stage_run_contract as old
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();B=W/'terminal_margin_physical_r1';records=[];negative=[];prep=json.loads((W/'TERMINAL_LEAD_STAGE_AUDIT_PREPARATION.json').read_text())
for r in prep['files']:assert sha(W/r['parent'])==r['parent_sha256'] and sha(W/r['new'])==r['new_sha256'];ast.parse((W/r['new']).read_text())
for mod in ['audit_terminal_lead_stage_contract','audit_terminal_lead_stage_pose_live','audit_terminal_lead_stage_pressure','audit_terminal_lead_stage_contacts','audit_terminal_lead_stage_stability']:importlib.import_module(mod)
root=Path(tempfile.mkdtemp(prefix='terminal_lead_measurement_'));mutated=None;bindings={};inventory=0
for ep in sorted(B.glob('case_*/layout_*')):
 if not (ep/'raw.npz').exists():continue
 historical=verify_measurements(ep,enabled=False);assert historical['passed'];wait=ep.name.endswith('wait_no_package');fr=None if wait else json.loads((ep/'frontal_bypass.json').read_text());original=old.primary(wait)+['audit_terminal_margin_stage_contacts.py','audit_terminal_margin_stage_pressure.py'];adapted=new.primary(wait)+['audit_terminal_lead_stage_contacts.py','audit_terminal_lead_stage_pressure.py']
 if fr:original+=old.controls(fr['plan'])+old.ADDITIONAL;adapted+=new.controls(fr['plan'])+new.ADDITIONAL
 original+=['audit_terminal_margin_stage_release.py'];adapted+=['audit_terminal_lead_stage_release.py']
 assert len(original)==len(adapted)
 for a,b in zip(original,adapted):assert b==('audit_terminal_lead_stage_stability.py' if a=='audit_contact_stability_control.py' else a.replace('terminal_margin_stage','terminal_lead_stage'))
 inventory+=len(set(original))
 if fr:
  original_stability=json.loads((ep/'TERMINAL_MARGIN_CONTACT_STABILITY_SUPPLEMENT.json').read_text());actual_stability=audit_files(ep,margin_enabled=True)
  for k,v in actual_stability.items():assert original_stability[k]==v,(ep,k)
 fixture=root/ep.name;fixture.mkdir()
 for name in ['raw.npz','trace.npz','parcel_orientation.npz']:
  if (ep/name).exists():os.link(ep/name,fixture/name)
 if fr:
  controls=json.loads((ep/'expert_control.json').read_text());d=copy.deepcopy(fr);key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';size={'box':(.14,.09,.045),'mailer':(.15,.145,.04)};feedback=DirectionalLeadFeedback(fr['plan']['initial_target_xyz'][0],fr['plan']['obstacle_initial_xyz'][0],task_direction=fr['plan']['direction'])
  with np.load(ep/'trace.npz') as z:tr={k:z[k].astype(float) for k in [key,other]}
  with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].astype(float) for k in [key,other]}
  for row in d['rows']:
   f=row.get('clearance_feedback')
   if not f or not f.get('eligible'):continue
   t=row['step'];previous=controls[t-1]['target_xyz'] if controls[t-1]['mode']=='top_push' else row['observed_support_xyz'];proposal=feedback.propose(tr[key][t],tr[other][t],size[key],size[other],ori[key][t],ori[other][t],row['observed_support_xyz'],previous,fr['plan']['initial_top_proposal']['goal_y'],step_m=min(.003,fr['plan']['top_recontact']['drag_step_m']));assert proposal['eligible'];row['clearance_feedback']=proposal;row['target_xyz']=[*proposal['command_xy'],row['target_xyz'][2]];controls[t]['target_xyz']=row['target_xyz']
  (fixture/'frontal_bypass.json').write_text(json.dumps(d));(fixture/'expert_control.json').write_text(json.dumps(controls))
 else:d=None
 verified=verify_measurements(fixture,enabled=True);assert verified['passed'],verified['errors'][:3]
 records.append(dict(episode=ep.name,historical_feedback_rows=historical['checked_feedback_rows'],counterfactual_changed_rows=verified['changed_rows'],same_original_audit_count=len(set(original)),historical_stability_identical=True if fr else None,fixture_is_not_rollout=True));bindings[str(ep/'raw.npz')]=sha(ep/'raw.npz')
 if verified['changed_rows'] and mutated is None:mutated=(fixture,copy.deepcopy(d))
for case in sorted(B.glob('case_*')):
 if not case.is_dir():continue
 try:verify_trial_provenance(case)
 except (AssertionError,KeyError):pass
 else:raise AssertionError('old sources accepted')
assert len(records)==10 and inventory==194 and mutated
fixture,d=mutated;idx=next(i for i,r in enumerate(d['rows']) if 'terminal_directional_lead_floor' in (r.get('clearance_feedback') or {}))
for label in ['wrong_x','wrong_goal','missing_floor','oversized_command','wrong_phase','wrong_direction','stale_previous_annotation']:
 bad=copy.deepcopy(d);r=bad['rows'][idx];f=r['clearance_feedback']
 if label=='wrong_x':f['command_xy'][0]+=.01
 elif label=='wrong_goal':f['object_goal_xy'][1]+=.01
 elif label=='missing_floor':del f['terminal_directional_lead_floor']
 elif label=='oversized_command':f['command_xy'][1]+=.01
 elif label=='wrong_phase':f['stage']='clearance_x'
 elif label=='wrong_direction':bad['plan']['direction']*=-1
 else:f['terminal_directional_lead_floor']['original_command_y']+=.01
 (fixture/'frontal_bypass.json').write_text(json.dumps(bad))
 try:result=verify_measurements(fixture,enabled=True);rejected=not result['passed']
 except AssertionError:rejected=True
 assert rejected,label;negative.append(label)
(fixture/'frontal_bypass.json').write_text(json.dumps(d))
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Full ten parent episodes,194 original audits retained, exact independent stability formula comparison. Enabled command fixtures use old future observations and are NOT candidate rollouts or new-source episodes.',records=records,negative_classes=negative,old_sources_rejected=True,original_audit_invocations=inventory,new_feedback_invocations=10,source_sha256={**bindings,**{str(W/r['new']):sha(W/r['new']) for r in prep['files']},**{str(W/n):sha(W/n) for n in ['audit_terminal_lead_stage_feedback.py','audit_terminal_lead_stage_stability.py']}},stage_sha256=json.loads((S/'PREPARATION.json').read_text())['stage_sha256'],fixture_root=str(root),fixture_driver_sha256=sha(__file__),simulation_started=False,training_ready=False)
p=W/'TERMINAL_LEAD_STAGE_AUDIT_ADAPTER_CHECK.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print('passed10 conditions194 original audits;',sum(r['counterfactual_changed_rows'] for r in records),'counterfactual altered rows;',len(negative),'negative classes; no physics')
