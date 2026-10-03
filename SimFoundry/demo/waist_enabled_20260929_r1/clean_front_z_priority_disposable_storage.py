"""Remove only inventoried, unreferenced rebuildable cache/temporary bytes.
Retain all model checkpoints, original data, source snapshots, reports and hashed
fixture inputs. Never follow links or recursively remove a source directory.
"""
from pathlib import Path
import os,json,stat,hashlib,datetime,shutil,subprocess
W=Path(__file__).resolve().parent;ROOT=W.parents[1];I=W/'FRONT_Z_PRIORITY_DISPOSABLE_STORAGE_INVENTORY.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();plan=json.loads(I.read_text());out=W/'FRONT_Z_PRIORITY_DISPOSABLE_STORAGE_CLEANUP.json';log=W/'FRONT_Z_PRIORITY_DISPOSABLE_STORAGE_DELETIONS.jsonl';assert not out.exists() and not log.exists()
assert plan['deletion_performed'] is False and plan['estimated_reclaimable_bytes']/1024**3>2.3
assert not subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip()
for r in plan['reports_with_matching_text']:assert sha(r['path'])==r['sha256']
opened=set();exceptions=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  if p.stat().st_uid!=os.getuid():continue
  for target in [p/'cwd',p/'exe',*(p/'fd').iterdir()]:
   try:opened.add(os.readlink(target).removesuffix(' (deleted)'))
   except FileNotFoundError:pass
  for line in (p/'maps').read_text().splitlines():
   fields=line.split(maxsplit=5)
   if len(fields)==6 and fields[5].startswith('/'):opened.add(fields[5].removesuffix(' (deleted)'))
 except FileNotFoundError:pass
 except PermissionError:
  comm=(p/'comm').read_text().strip();assert comm in ['(sd-pam)','ssh-agent'] and (p/'fd').stat().st_uid==0
  exceptions.append(dict(pid=int(p.name),comm=comm,scope='OS-protected authentication service, not inspected'))
retained={}
for p in (ROOT.parent/'lerobot/outputs').rglob('*.safetensors'):
 if p.is_file():s=p.stat();retained[str(p)]=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
for row in plan['files']:
 p=Path(row['path']);root=Path(row['root']);assert not root.is_symlink() and root in [Path(r['path']) for r in plan['roots']]
 assert p.is_relative_to(root) and not p.is_symlink() and not p.is_relative_to(ROOT)
 for parent in p.parents:
  if parent==root.parent:break
  assert not parent.is_symlink()
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_uid,s.st_mode)==tuple(row[k] for k in ['dev','inode','size','mtime_ns','uid','mode'])
 assert str(p) not in opened and str(root) not in opened and str(p.parent) not in opened and str(p) not in plan['protected_hash_references']
 assert sha(p)==row['sha256']
before=shutil.disk_usage(W).free
with log.open('x') as f:
 for row in plan['files']:
  p=Path(row['path']);s=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)==(row['dev'],row['inode'],row['size'],row['mtime_ns'],1)
  p.unlink();f.write(json.dumps(row)+'\n');f.flush()
for p,identity in retained.items():
 s=Path(p).stat();assert [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]==identity
for p in plan['protected_hash_references']:assert Path(p).exists(),p
# Validate the still-authoritative complete prior frozen source set.
protocol=json.loads((W/'front_projection_physical_r1/PROTOCOL.json').read_text())
for p,h in protocol['frozen_files_sha256'].items():assert sha(p)==h,p
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,status='complete',inventory_sha256=sha(I),deletions_sha256=sha(log),script_sha256=sha(__file__),files_removed=len(plan['files']),free_bytes_before=before,free_bytes_after=shutil.disk_usage(W).free,estimated_removed_bytes=plan['estimated_reclaimable_bytes'],all_model_state_files_retained=len(retained),protected_reference_paths_retained=len(plan['protected_hash_references']),frozen_sources_unchanged=len(protocol['frozen_files_sha256']),authentication_process_visibility_exceptions=exceptions,original_data_and_models_deleted=False)
result['observed_free_delta_bytes']=result['free_bytes_after']-before
with out.open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(status='complete',files_removed=result['files_removed'],observed_free_delta_gib=result['observed_free_delta_bytes']/1024**3,free_gib=result['free_bytes_after']/1024**3,model_state_files_unchanged=len(retained),frozen_sources_unchanged=result['frozen_sources_unchanged']),indent=2))
