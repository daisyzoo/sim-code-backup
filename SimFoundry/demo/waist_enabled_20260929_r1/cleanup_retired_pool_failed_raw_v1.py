"""Remove only six retired20260928 failed raw trajectories, retaining evidence.
Prior user authorization covers obsolete intermediate test data. No successful
sample, current goal data, checkpoint, code, report, or review image is removed.
"""
from pathlib import Path
import json,hashlib,datetime,shutil,os
W=Path(__file__).resolve().parent;ROOT=W.parents[1];OLD=ROOT/'demo/spatial_candidate_pool72_20260928_r1';D=W/'retired_pool_failed_raw_cleanup_r1';assert not D.exists();D.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
state=json.loads((OLD/'STATUS.json').read_text());assert state['stage']=='numeric_complete_group_selection_and_visual_review_required' and state['training_ready'] is False
for q in sorted(OLD.glob('case_*/layout_*/quality.json')):
 d=json.loads(q.read_text());p=q.parent/'raw.npz'
 if d.get('passed') is not False or not p.exists():continue
 assert not p.is_symlink() and p.stat().st_nlink==1
 images=[f for f in q.parent.glob('*.jpg') if f.is_file()];assert images,'Missing retained images'
 rows.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,quality_report=str(q),quality_sha256=sha(q),reasons=d.get('reasons'),retained_images={str(i):sha(i) for i in images}))
assert len(rows)==6
paths={r['path'] for r in rows};dependencies=[]
# Active/current-run protocols and launch configuration are authoritative input maps.
for run in ['front_corridor_lateral_physical_r1','front_box_trailing_physical_r2','front_loaded_z_quarter_physical_r2','rear_early_edge_physical_r1']:
 p=W/run/'PROTOCOL.json';d=json.loads(p.read_text());assert not paths.intersection(d['frozen_files_sha256']);dependencies.append(dict(path=str(p),sha256=sha(p)))
p=W/'front_contact_window_physical_preparation_r1/CONFIGURATION_CHECK.json';d=json.loads(p.read_text());assert not paths.intersection(d['source_sha256']);dependencies.append(dict(path=str(p),sha256=sha(p)))
refs=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  cmd=(proc/'cmdline').read_bytes().split(b'\0');cwd=(proc/'cwd').resolve()
  if any(v.decode(errors='replace').startswith(str(OLD)) for v in cmd) or cwd.is_relative_to(OLD):refs.append(proc.name)
  for fd in (proc/'fd').iterdir():
   try:
    if str(fd.resolve()) in paths:refs.append(proc.name)
   except (OSError,RuntimeError):pass
 except (OSError,RuntimeError):pass
assert not refs,refs
before=shutil.disk_usage(W).free;plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,dependency_maps_checked=dependencies,live_references=[],bytes=sum(r['bytes'] for r in rows))
with (D/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2)
for r in rows:
 p=Path(r['path']);assert sha(p)==r['sha256'];q=Path(r['quality_report']);assert sha(q)==r['quality_sha256'] and json.loads(q.read_text())['passed'] is False
 for f,h in r['retained_images'].items():assert sha(Path(f))==h
 p.unlink()
for r in rows:
 assert not Path(r['path']).exists();assert sha(Path(r['quality_report']))==r['quality_sha256']
 for f,h in r['retained_images'].items():assert sha(Path(f))==h
for r in dependencies:assert sha(Path(r['path']))==r['sha256']
after=shutil.disk_usage(W).free;out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),removed_files=len(rows),removed_logical_gib=plan['bytes']/2**30,observed_free_delta_gib=(after-before)/2**30,free_gib_after=after/2**30,all_failure_reports_and_images_retained=True,current_data_and_checkpoints_unchanged=True,original_failed_raw_no_longer_replayable=True,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'PLAN.json']})
with (D/'RESULT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
