"""Close only the isolated camera diagnostic; both original task failures retained."""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;R=W/'window_native_camera_probe_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[]
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
s=read(R/'STATUS.json');assert s['status']=='diagnostic_terminal' and s['raw_episodes_saved']==2 and not s['native_crash_observed'];assert not Path('/proc/625326').exists() and not Path('/proc/625446').exists();case=R/'case_840023';cs=read(case/'STATUS.json');assert cs['status']=='blocked_quality_or_runtime' and cs['error'].startswith('Quality gate failed.')
protocol=read(R/'PROTOCOL.json')
for p,h in protocol['frozen_files_sha256'].items():assert sha(p)==h,p
for ep in sorted(case.glob('layout_*')):
 if not ep.is_dir():continue
 quality=read(ep/'quality.json');window=read(ep/'front_contact_window.json');assert quality['passed'] is False and quality['frames']==320
 with np.load(ep/'raw.npz',allow_pickle=False) as z:
  rgb=z['rgb'];assert rgb.shape==(320,3,480,640) and rgb.dtype==np.uint8;assert np.isfinite(z['q']).all() and np.isfinite(z['action']).all();state0=float(abs(z['q'][0,12:23]).max());action0=float(abs(z['action'][0,12:23]).max());assert max(state0,action0)<1e-4;means=rgb.mean(axis=(1,2,3));assert means.min()>0
 with np.load(ep/'trace.npz',allow_pickle=False) as z:
  other='box' if 'nudge_mailer' in ep.name else 'mailer';nt=float(np.linalg.norm(z[other][:,:2]-z[other][0,:2],axis=1).max())
 notes=('Observed12 actual policy-camera samples: left hand approaches/contacts bag; box remains visible except left-edge crop in later views; bag remains on table and approaches bottom crop. No task-success claim from these samples.' if 'nudge_mailer' in ep.name else 'Observed12 actual policy-camera samples: right hand contacts/repositions above box; target remains visible, bag becomes partially cropped with camera turn. Full target-zone success is not shown.')
 rows.append(dict(episode=ep.name,frames=320,original_quality_passed=False,reasons=quality['reasons'],saved_target_progress_m=quality['metrics']['target_final_progress_m'],recomputed_non_target_max_xy_m=nt,first_upper11_state_max=state0,first_upper11_action_max=action0,all320_rgb_frames_present=True,rgb_frame_mean_min=float(means.min()),sampled_policy_frames=np.linspace(0,319,12).astype(int).tolist(),actual_visual_review='completed_actual_view_of_saved12sample_contact_sheet',visual_notes=notes,window_selected=window['selected_front'],window_intervals=len(window['rows']),training_ready=False))
 for p in [ep/'raw.npz',ep/'trace.npz',ep/'contact_sheet.jpg']:sources[str(p)]=sha(p)
log=R/'window_stream_audit.log';assert 'AssertionError' in log.read_text();sources[str(log)]=sha(log);sources[str(Path(__file__))]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,camera_probe_complete=True,native_crash_reproduced=False,native_crash_fixed_proven=False,collector_returncode=s['collector_returncode'],case_task_status=cs,rows=rows,original_task_passed=0,original_task_total=2,original_full_profile_window_audit='Rejected320frame settings at original1200frame source-profile binding; log preserved. No full-audit pass claimed.',full_experiment_complete=False,quarantined=True,training_ready=False,source_sha256=sources)
with (R/'RESULT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(camera_probe_complete=True,native_crash_reproduced=False,task_passed=0,task_total=2,rows=rows),indent=2))
