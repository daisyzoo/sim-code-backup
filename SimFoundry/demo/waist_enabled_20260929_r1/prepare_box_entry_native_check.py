"""Prepare explicit synthetic full-file test covering early and late two-phase recovery."""
from pathlib import Path
w=Path(__file__).resolve().parent;s=(w/'check_box_center_native_files.py').read_text()
s=s.replace('audit_box_center_pose_live','audit_box_entry_pose_live').replace('audit_box_center_source_contract','audit_box_entry_source_contract').replace('audit_box_center_events','audit_box_entry_events').replace('audit_box_center_plan','audit_box_entry_plan').replace('box_center_step_contract','box_entry_step_contract').replace("stage=w/'staged_box_center_preference'","stage=w/'staged_box_entry_lift'")
start="fixture=stage/'LIFECYCLE_CHECK.json';raw_fixture=json.loads(fixture.read_text());assert raw_fixture['passed'];data={'rows':[]}"
end="assert len(data['rows'])==4"
i=s.index(start);j=s.index(end,i)+len(end)
s=s[:i]+"""fixture=w/'BOX_ENTRY_LIFT_COMBINED_CHECK.json';raw_fixture=json.loads(fixture.read_text());assert raw_fixture['complete'] and raw_fixture['all_completed_within_budget'];data={'rows':[]}
guarded=json.loads((w/'BOX_ENTRY_LIFT_GUARDED_CHECK.json').read_text());assert guarded['complete'] and guarded['passed']
for report in [raw_fixture,guarded]:
 for path,digest in report['source_sha256'].items():assert sha(path)==digest,path
selection=[('box_center_groups_r1',522),('box_center_groups_r1',983),('rear_box_rate_groups_r1',706),('rear_box_rate_groups_r1',1151)]
for row in raw_fixture['rows']:
 if (row['run'],row['start_step']) not in selection:continue
 data['rows'].append(dict(episode='layout_840001_push_box_to_bin',step=row['start_step'],plants=[dict(trace=row['trace'])]))
assert len(data['rows'])==4"""+s[j:]
s=s.replace("prefix='box_center_native_files_'","prefix='box_entry_native_files_'")
s=s.replace("'rear_cop_route.py','box_center_preference_plan.py']","'rear_cop_route.py','box_center_preference_plan.py','box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py']")
s=s.replace("['rear_box_center_preference','rear_slow_drag'","['rear_box_entry_lift','rear_box_center_preference','rear_slow_drag'")
s=s.replace('dict(rear_box_center_preference=True','dict(rear_box_entry_lift=True,rear_box_center_preference=True')
s=s.replace("   assert shift==0 and 'box_center_preference_pose' in event['planning']","   assert shift==0\n   assert ('lift' in event['planning']) if event.get('entry_lift_phase') else ('box_center_preference_pose' in event['planning'])")
needle=" plan['unloaded_recontact_pose']['box_center_preference']=dict(enabled=True,center_weight_per_m2=400.,parent='same_observation_minimum_motion',side='right',original_fallback=True,original_constraints_unchanged=True)"
assert needle in s;s=s.replace(needle,needle+"\n plan['unloaded_recontact_pose']['entry_lift']=dict(enabled=True,side='right',original_entry_height_m=.84,nominal_lift_height_m=.845,measured_ready_frames=3,maximum_lift_ticks=40,combined_maximum_ticks=240,measured_unloaded_required=True,phase_boundary_guards=True,training_ready=False)")
needle="mutations=[";s=s.replace(needle,needle+"\n ('frontal_bypass.json','missing_entry_metadata',lambda d:d['plan']['unloaded_recontact_pose'].pop('entry_lift')),\n ('frontal_bypass.json','extended_recovery_budget',lambda d:d['plan']['unloaded_recontact_pose']['entry_lift'].__setitem__('combined_maximum_ticks',280)),\n ('recontact_pose.json','missing_entry_phase',lambda d:d['rows'][0].pop('entry_lift_phase')),\n ('recontact_pose.json','early_lift_ready',lambda d:d['rows'][0].__setitem__('entry_lift_phase','lift_ready')),\n ('recontact_pose.json','unlogged_lift_normal_capture',lambda d:d['rows'][0].__setitem__('captured_normal_local_up',[0,0,1])),")
s=s.replace("w/'audit_box_entry_plan.py',w/'audit_box_center_preference_plan.py'","w/'audit_box_entry_plan.py',w/'audit_box_entry_lift_events.py',w/'audit_box_center_events.py',w/'audit_box_center_plan.py',w/'BOX_ENTRY_LIFT_GUARDED_CHECK.json',w/'audit_box_center_preference_plan.py'")
p=w/'check_box_entry_native_files.py';assert not p.exists();compile(s,str(p),'exec');p.write_text(s);print('prepared4native two-phase fixtures;21negative cases; no physical launch')
