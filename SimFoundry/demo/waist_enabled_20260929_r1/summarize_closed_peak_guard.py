"""Summarize a closed full diagnostic and explicitly separate the next candidate."""
from pathlib import Path
import json,hashlib,datetime,shutil
W=Path(__file__).resolve().parent;R=W/'peak_guard_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=[]
def read(p):
    p=Path(p);files.append(p);return json.loads(p.read_text())
result=read(R/'RESULT.json');assert result['status']=='diagnostic_closed_not_training_admission'
assert len(result['rows'])==10 and all(x['all_audits_passed'] for x in result['rows'])
assert read(R/'PRESSURE_SETTING_BINDING.json')['passed']
for f in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
    d=read(R/f);assert not Path(f"/proc/{d['pid']}/cmdline").exists()
first=read(W/'INSTANT_LOAD_BIAS_GUARD_CHECK.json');first_rows={r['episode']:r for r in first['rows']}
rows=[];audits=dict(primary=0,observer=0,pressure=0,controls=0,additional=0)
for row in result['rows']:
    ep=R/f"case_{row['layout_id']}"/row['episode'];n=read(ep/'PEAK_GUARD_NUMERIC_REVIEW.json');v=read(ep/'ACTUAL_REVIEW_BINDING.json')
    out={k:n[k] for k in ['episode','frames','quality_passed','initial11_q_max_abs','initial11_action_max_abs','assist_frames']}
    assert out['initial11_q_max_abs']==out['initial11_action_max_abs']==out['assist_frames']==0
    for kind,name in [('primary','PRIMARY_AUDIT_EXECUTION.json'),('observer','OBSERVATION_AUDIT_EXECUTION.json'),('pressure','PRESSURE_AUDIT_EXECUTION.json')]:
        d=read(ep/name);assert d['completed'] and all(x['returncode']==0 for x in d['rows']);audits[kind]+=len(d['rows'])
    if row['wait']:
        assert v['actual_visual_review']=='completed_actual_view_8RGB';out.update(all11_action_max_abs=n['all11_action_max_abs'],waist_max_abs_rad=n['waist_max_abs_rad'])
    else:
        assert v['actual_sampled_visual_review']=='completed'
        out.update({k:n[k] for k in ['progress_mm','final10_signed_y_min_mm','non_target_max_xy_mm','tilt_exit_count','lost_contact_exit_count']})
        d=read(ep/'PRESSURE_STREAM_DIAGNOSIS.json');assert d['pressure_verification']['passed'];out['actual_peak_guard_holds']=len(d['held_steps']);out['pressure_updates']=d['pressure_verification']['pressure_updates']
        cam=read(ep/'CAMERA_FRUSTUM_DIAGNOSIS.json');out['camera_top_push_projection']=cam['top_push'];out['actual_camera_samples']=cam['runtime_camera_pose_samples_checked']
    if ep.name in first_rows:
        d=first_rows[ep.name];out.update(candidate_one_step_input_events=d['events_checked'],candidate_additional_holds=d['additional_holds'])
    else:
        d=read(ep/'INSTANT_LOAD_ONE_STEP_SCREEN.json');assert d['passed'];out.update(candidate_one_step_input_events=d['actual_input_events'],candidate_additional_holds=d['additional_holds'])
    rows.append(out)
for kind,name in [('controls','CONTROL_EVIDENCE_EXECUTION.json'),('additional','ADDITIONAL_AUDIT_EXECUTION.json')]:
    d=read(R/name);assert d['stage']=='complete' and all(x['returncode']==0 for x in d['rows']);audits[kind]=len(d['rows'])
assert audits==dict(primary=36,observer=10,pressure=10,controls=80,additional=56)
for name in ['INSTANT_LOAD_BIAS_GUARD_CHECK.json','INSTANT_LOAD_CONTROL_ADAPTER_CHECK.json','INSTANT_LOAD_UPDATE_MATH_CHECK.json','INSTANT_GUARD_PRESSURE_STREAM_CHECK.json','staged_instant_load_guard/PREPARATION.json','staged_instant_load_guard/PRELAUNCH_CHECK.json']:
    d=read(W/name)
    for p,h in d.get('source_sha256',{}).items():assert sha(p)==h,p
assert sum(x['candidate_one_step_input_events'] for x in rows)==9390
assert sum(x['candidate_additional_holds'] for x in rows)==165
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,previous_goal_turn='progress',goal_status='active',push_passed=result['push_passed'],wait_passed=result['waits_passed'],audit_counts=audits,actual_visual_reviews=10,rows=rows,qualified_training_groups=0,conversions=0,new_models=0,training_ready=False,next_candidate=dict(stage_prepared=True,physical_launched=False,cli_checks=16,stream_checks=16,synthetic_event_math_checks=21,synthetic_events_at_recorded_prestates=6992,independent_one_step_real_input_events=9390,additional_final_holds=165),disk_free_gib=shutil.disk_usage(W).free/1024**3,limitations=['7/8 equals reference, no demonstrated task improvement.','Rearbox still fails original gates; no diagnostic group is admitted to training.','Original camera target-crop/out-of-view risks remain; no camera change or new visibility hard gate.','One-step candidate outputs do not accumulate counterfactual state or prove physics gains.','New candidate full source contract/native audit adaptation/protocol/storage/freeze remain before physical launch.'],source_sha256={str(p):sha(p) for p in dict.fromkeys(files+[Path(__file__)])})
p=R/'FULL10_CLOSED_FINDINGS.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['rows','source_sha256']},indent=2))
