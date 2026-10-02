"""Actual first complete rearbox, with explicitly incomplete whole-run status."""
from pathlib import Path
import json,hashlib,datetime,shutil
W=Path(__file__).resolve().parent;R=W/'instant_guard_groups_r1';ep=R/'case_840001/layout_840001_push_box_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();files=[]
def read(p):files.append(p);return json.loads(p.read_text())
n=read(ep/'INSTANT_GUARD_NUMERIC_REVIEW.json');v=read(ep/'ACTUAL_REVIEW_BINDING.json');pressure=read(ep/'PRESSURE_STREAM_DIAGNOSIS.json');h=read(ep/'INSTANT_GUARD_LOAD_HISTORY.json');effect=read(ep/'INSTANT_GUARD_WAYPOINT_EFFECT.json');cam=read(ep/'CAMERA_FRUSTUM_DIAGNOSIS.json');updates=read(ep/'peak_load_updates.json');read(R/'INITIAL_SOURCE_BINDING.json')
assert n['frames']==1200 and not n['original_task_and_pose_passed'] and n['initial11_q_max_abs']==n['initial11_action_max_abs']==n['assist_frames']==0
assert v['actual_sampled_visual_review']=='completed' and pressure['pressure_verification']['passed'];assert effect['summary']=={'changed_height_waypoint':99,'original_outer_guard_cleared_bias':3}
u={e['action_step']:e for e in updates['rows']};exits=[]
for x in h['exit_events']:
    t=x['controller_step'];e=u[t];load=x['substeps']['vertical_load_n']
    exits.append(dict(step=t,reason=x['reason'],preceding_peak_n=max(load),preceding_final_n=load[-1],preceding_final_tilt_rad=x['substeps']['final_target_tilt_rad'],filtered_n=e['after']['filtered_n'],pressure_boundary_bias_m=e['after']['bias_m']))
assert len(exits)==7 and sum(x['preceding_final_n']>=5. for x in exits)==5
launch=read(R/'LAUNCH.json');status=read(R/'STATUS.json');live={}
for kind,pid in {'runner':launch['processes']['runner']['pid'],'watcher':launch['processes']['watcher']['pid'],'collector':status['collector_pid']}.items():
    cmd=Path(f'/proc/{pid}/cmdline').read_bytes();assert cmd;live[kind]=dict(pid=pid,cmdline=cmd.decode().replace('\0',' ').strip())
protocol=read(R/'PROTOCOL.json')
for p,digest in protocol['frozen_files_sha256'].items():assert sha(p)==digest
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,goal_turn='progress',goal_status='active',first_rearbox=dict(task_passed=False,frames=1200,progress_mm=n['progress_mm'],reference_progress_mm=n['baseline']['progress_mm'],final10_signed_y_min_mm=n['final10_signed_y_min_mm'],non_target_max_xy_mm=n['non_target_max_xy_mm'],tilt_exits=n['tilt_exit_count'],peak_vertical_load_n=h['summary']['max_peak_vertical_load_n'],pressure_updates=pressure['pressure_verification']['pressure_updates'],additional_final_holds=pressure['pressure_verification']['additional_final_holds'],waypoint_effect=effect['summary'],tilt_exit_context=exits,first_differences=pressure['first_differences'],first_additional_final_hold_step=min(pressure['additional_final_hold_steps']),camera_top_push=cam['top_push']),whole_run_closed=False,qualified_training_groups=0,conversions=0,new_models=0,training_ready=False,live_processes=live,disk_free_gib=shutil.disk_usage(W).free/1024**3,source_sha256={str(p):sha(p) for p in files if p.name!='STATUS.json'},limitations=['First failed1200-frame trajectory only; remaining7push2wait and all native audits still required.','Pressure hold changes actual commanded height but does not reduce observed tilt exits here.','Command/state/object differences precede first final-load hold, so +8.718mm is not a causal gain estimate.','Five of seven tilt exits follow final load>=5N; final-load condition is not sufficient to prevent tilt.','Original camera visibility risk unchanged;438/438 top_push targetOBB excluded geometrically.'])
f=R/'FIRST_REAR_BOX_FINDINGS.json';assert not f.exists();f.write_text(json.dumps(out,indent=2));print(json.dumps({k:out[k] for k in ['created_at_utc','goal_turn','whole_run_closed','qualified_training_groups','disk_free_gib']},indent=2))
