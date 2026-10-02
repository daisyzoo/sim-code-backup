"""Version original full file/control audits for explicit entry-lift provenance.
No old source edits. A build is not successful validation or permission to run.
"""
from pathlib import Path
import json,ast
w=Path(__file__).resolve().parent
mapping={v:v.replace('box_center','box_entry').replace('BOX_CENTER','BOX_ENTRY') for v in json.loads((w/'BOX_CENTER_AUDIT_VERSION_MAP.json').read_text()).values()}
mapping['staged_box_center_preference']='staged_box_entry_lift'
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 # Old map has a plural alias but original actual output uses singular INPUT.
 return s.replace('BOX_CENTER_','BOX_ENTRY_')
for a,b in mapping.items():
 if not (w/(a+'.py')).exists() or a in ['audit_box_center_plan','audit_box_center_events']:continue
 s=rename((w/(a+'.py')).read_text())
 if a=='audit_box_center_source_contract':
  s=s.replace(" assert args.get('rear_box_center_preference') is True,", " assert args.get('rear_box_entry_lift') is True,'entry-lift option missing'\n assert args.get('rear_box_center_preference') is True,")
  s=s.replace("'box_center_preference_plan.py'];bound={}","'box_center_preference_plan.py','box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py'];bound={}")
  s=s.replace(" assert meta.get('rear_box_center_preference') is True,", " assert meta.get('rear_box_entry_lift') is True,'raw entry-lift option missing'\n assert meta.get('rear_box_center_preference') is True,")
  needle='  else:assert center is None'
  s=s.replace(needle,needle+"\n  expected_entry=dict(enabled=True,side='right',original_entry_height_m=.84,nominal_lift_height_m=.845,measured_ready_frames=3,maximum_lift_ticks=40,combined_maximum_ticks=240,measured_unloaded_required=True,phase_boundary_guards=True,training_ready=False)\n  entry=plan.get('unloaded_recontact_pose',{}).get('entry_lift')\n  if enabled:\n   assert entry==expected_entry and all(type(entry[k]) is type(v) for k,v in expected_entry.items())\n  else:assert entry is None")
 if a=='box_center_step_contract':
  s=s.replace(" assert args.get('rear_box_center_preference') is True", " assert args.get('rear_box_entry_lift') is True and meta.get('rear_box_entry_lift') is True\n assert args.get('rear_box_center_preference') is True")
 if a=='audit_box_center_pose_live':
  s=s.replace('from audit_box_entry_events import EventAudit','from audit_box_entry_events import EventAudit\nfrom audit_box_entry_plan import verify_entry_plan')
  s=s.replace("        if raw.get('planning') is not None:assert", "        if raw.get('entry_lift_phase') is not None:\n            assert side=='right' and raw['kind']=='command' and raw['entry_lift_phase'] in ('lift_command','lift_ready')\n            continue\n        if raw.get('planning') is not None:assert")
  s=s.replace("            if event:assert event['kind']=='unchanged'", """            if event:assert event['kind']=='unchanged'
            if event and 'rejected_entry_lift_attempt' in event:
                rejected=event['rejected_entry_lift_attempt'];ctx=event['context']
                assert side=='right' and event['reason']=='initial_hand_below_unloaded_planning_height'
                assert rejected['kind']=='unchanged' and rejected['reason']=='no_verified_entry_lift' and rejected['context']==ctx
                scene=dict(side=side,target_xyz=xyz[t].tolist(),target_quat=quat[t].tolist(),core_size=core,other_xyz=oxyz[t].tolist(),other_quat=oquat[t].tolist(),other_size=[.15,.145,.04])
                assert ctx['step']==t and ctx['scene']==scene and ctx['selected'] is True and ctx['guard_stop'] is False and ctx['parent_mode'] in ('top_cross','top_descend') and ctx['recontacts']==f['recontacts']>0
                near(ctx['current'],q[t],1e-7);near(ctx['previous_q'],q[t-1],1e-7);near(ctx['previous_command'],u[t-1],0)
                assert observed[t][0]==ctx['observed_load_n']==0 and observed[t][1]==ctx['filtered_load_n'] and 0<=observed[t][1]<=.05
                assert verify_entry_plan(audit.lift.geometry_audit,rejected['planning'],current=q[t],scene=scene,step=t)['accepted'] is False""")
  s=s.replace("'box_center_preference_plan.py','elbow_torso_hulls.json'", "'box_center_preference_plan.py','box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py','elbow_torso_hulls.json'")
  s=s.replace("'audit_box_entry_plan.py','audit_box_center_preference_plan.py'", "'audit_box_entry_plan.py','audit_box_entry_lift_events.py','audit_box_center_events.py','audit_box_center_plan.py','audit_box_center_preference_plan.py'")
  s=s.replace("assert meta['minimum_motion_recontact'] is True", "assert meta['rear_box_entry_lift'] is True and meta['minimum_motion_recontact'] is True")
 p=w/(b+'.py');assert not p.exists(),p;ast.parse(s);p.write_text(s)
p=w/'audit_box_entry_events.py';assert not p.exists();p.write_text('"""Explicit independent entry-lift and original-center event dispatcher."""\nfrom audit_box_entry_lift_events import EventAudit\n')
for a,b in {'box_center_run_contract':'box_entry_run_contract','run_box_center_groups':'run_box_entry_groups','watch_box_center_audits':'watch_box_entry_audits','close_box_center_groups':'close_box_entry_groups'}.items():
 s=rename((w/(a+'.py')).read_text()).replace('box_center_run_contract','box_entry_run_contract')
 s=s.replace("assert prov['args']['rear_box_center_preference'] is True", "assert prov['args']['rear_box_entry_lift'] is True and prov['args']['rear_box_center_preference'] is True")
 s=s.replace("assert meta['rear_box_center_preference'] is True", "assert meta['rear_box_entry_lift'] is True and meta['rear_box_center_preference'] is True")
 p=w/(b+'.py');assert not p.exists(),p;ast.parse(s);p.write_text(s)
(w/'BOX_ENTRY_AUDIT_VERSION_MAP.json').write_text(json.dumps(mapping,indent=2));print('prepared audits and drivers; no freeze or launch')
