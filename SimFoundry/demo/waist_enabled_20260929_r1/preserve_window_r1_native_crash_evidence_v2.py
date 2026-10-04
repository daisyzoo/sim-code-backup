"""Preserve terminal native crash evidence without changing the failed run or restarting it."""
from pathlib import Path
import json, hashlib, datetime, shutil
W=Path(__file__).resolve().parent; R=W/'front_contact_window_physical_r1'; C=R/'case_840023'; D=R/'NATIVE_CRASH_EVIDENCE_V2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
status=json.loads((R/'STATUS.json').read_text()); assert status['status']=='runtime_or_audit_failed' and status['completed_conditions']==2
assert not Path('/proc/605996').exists() and not Path('/proc/613652').exists()
log=R/'case_840023.log'; content=log.read_text(); assert 'libomni.syntheticdata.plugin.so' in content and 'exit code 139' in content
trace=Path('/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/isaacsim/kit/data/Kit/IsaacLab/3.0/06137085-b25a-463d-b6519fb9-d74fbc22.py.txt')
assert '_post_process_graph_tick' in trace.read_text(); assert not list(C.glob('layout_*/raw.npz'))
progress=json.loads((C/'progress.json').read_text()); assert progress['step']==90
views=sorted((C/'viewer_layout_840023_push_box_to_bin').glob('*.jpg')); assert views
sources=[(log,'terminal_case_log.txt'),(trace,'native_python_trace.txt'),(C/'progress.json','last_progress.json'),(C/'progress.jpg','last_progress.jpg'),(C/'STATUS.json','stale_case_status.json'),(R/'STATUS.json','terminal_producer_status.json'),(R/'COLLECTION_EXECUTION.json','collection_execution.json'),(views[-1],'last_retained_viewer.jpg')]
assert not D.exists(); D.mkdir()
for p,n in sources: shutil.copy2(p,D/n)
originals=[R/'PROTOCOL.json',C/'provenance.json',C/'SUBSTEP_RUNTIME_BINDING.json',C/'runtime_configuration.json',Path(__file__),*views]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='terminal_native_camera_crash',producer_status=status,producer_pid_absent=605996,collector_pid_absent=613652,exit_code_from_native_log=139,last_progress_step=90,last_retained_viewer_frame=views[-1].name,planned_conditions=10,complete_conditions=2,attempted_incomplete_condition='layout_840023_push_box_to_bin',unexecuted_conditions=7,episode_raw_saved=False,case_status_is_stale=True,crash_stack_component='libomni.syntheticdata.plugin.so / SyntheticData._post_process_graph_tick / graph.evaluate during camera update',root_cause_proven=False,free_gib=shutil.disk_usage(W).free/2**30,source_sha256={str(p):sha(p) for p in originals+[D/n for _,n in sources]},prior_capture_v1_failed_before_copy='KeyError collector_pid after producer became terminal; empty V1 folder preserved',original_failed_run_preserved=True,signals_sent=False,restarted=False,training_ready=False,training_admissions_added=0)
with (R/'NATIVE_CRASH_DIAGNOSIS_V2.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'},indent=2))
