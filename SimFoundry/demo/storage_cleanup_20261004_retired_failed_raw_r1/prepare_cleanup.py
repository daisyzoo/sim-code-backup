from pathlib import Path
import json,hashlib,datetime,os,shutil
ROOT=Path('/home/user/Documents/zoo/sim/SimFoundry');W=ROOT/'demo/waist_enabled_20260929_r1';P=ROOT/'demo/storage_cleanup_20261004_retired_failed_raw_r1';P.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();probe=json.loads(Path('/tmp/retired_sorting_raw_probe.json').read_text());names=['natural_coverage24_20260929_r1','approach_geometry_20260928_r1','natural_layout_feasibility_20260928_r1'];selected=[];retained={};statuses={}
for n in names:
 row=next(r for r in probe['candidates'] if Path(r['root']).name==n);assert not row['references'] and not row['direct_protected_files'];root=Path(row['root']);status=json.loads((root/'STATUS.json').read_text());assert status['training_ready'] is False and status['stage'] in ['complete_reviewed_no_complete_passing_group','complete_reviewed_quality_failed'];statuses[n]=status
 for f in root.rglob('*'):
  if not f.is_file() or f.is_symlink():continue
  st=f.stat()
  if f.name=='raw.npz':
   assert str(f) in row['files'] and st.st_nlink==1
   selected.append(dict(path=str(f),bytes=st.st_size,sha256=sha(f),device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
  else:retained[str(f)]=sha(f)
assert len(selected)==52
roots=[str(ROOT/'demo'/n) for n in names];hits=[];checked=0;denied=0
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  cmd=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');cwd=os.readlink(proc/'cwd');fds=list((proc/'fd').iterdir());checked+=1
 except (FileNotFoundError,ProcessLookupError):continue
 except PermissionError:denied+=1;continue
 # Command scan checks only exact roots; the preparing script filename contains none.
 if any(r in cmd or cwd.startswith(r) for r in roots):hits.append(dict(pid=int(proc.name),kind='command_or_cwd'))
 for fd in fds:
  try:link=os.readlink(fd)
  except (FileNotFoundError,PermissionError):continue
  if any(link.startswith(r+'/') for r in roots):hits.append(dict(pid=int(proc.name),kind='open_file',path=link))
assert not hits,hits
proof=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_deleted',authorization='User previously requested deletion of unrelated historical/intermediate data to free storage.',scope='Only52raw.npz from3completed reviewed failed non-admitted retired pre-waist diagnostics. All traces, quality/control records, layouts and images retained. No current/pending sources, checkpoint or admitted datasets.',files=selected,total_bytes=sum(r['bytes'] for r in selected),retained_sha256=retained,statuses=statuses,protected_source_count=probe['protected_sources'],text_source_count=probe['text_sources_scanned'],protected_owner_sha256={p:sha(p) for p in probe['owners']},probe_sha256=sha('/tmp/retired_sorting_raw_probe.json'),process_scan=dict(checked=checked,permission_denied=denied,hits=hits),free_bytes_before=shutil.disk_usage(ROOT).free,deletions_performed=False,goal_complete=False)
(P/'PLAN.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));(P/'REFERENCE_PROBE.json').write_bytes(Path('/tmp/retired_sorting_raw_probe.json').read_bytes());(P/'prepare_cleanup.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(dict(files=len(selected),bytes=proof['total_bytes'],retained=len(retained),process_scan=proof['process_scan'],plan=str(P/'PLAN.json'))))
