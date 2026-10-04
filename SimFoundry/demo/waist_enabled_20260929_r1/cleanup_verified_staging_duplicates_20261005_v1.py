"""Delete only fully byte-verified, unused temporary upload duplicates.
All retained checkpoint/model files and unrelated cache files stay intact.
"""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
W=Path(__file__).resolve().parent;D=W/'storage_duplicate_staging_20261005_r1';proof=D/'VERIFIED.json';d=json.loads(proof.read_text());assert d['all_identical'] and d['no_open_temporary_handles'] and len(d['rows'])==7
allowed=Path('/home/user/.local/share/wandb/artifacts/staging');dest=D/'CLEANUP.json';assert not dest.exists()
def st(p):
 s=p.stat();return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,links=s.st_nlink,allocated_bytes=s.st_blocks*512)
paths=[]
for r in d['rows']:
 a=Path(r['temporary_path']);b=Path(r['retained_model']);assert a.parent==allowed and a.name.startswith('tmp') and not a.is_symlink() and not b.is_symlink()
 assert r['byte_identical'] and r['compared_bytes']==r['bytes'] and r['temporary_sha256']==r['retained_sha256']
 assert st(a)==r['temporary_stat'] and st(b)==r['retained_stat'] and r['temporary_stat']['links']==1
 assert (r['temporary_stat']['device'],r['temporary_stat']['inode'])!=(r['retained_stat']['device'],r['retained_stat']['inode'])
 paths.append(str(a))
handles=subprocess.run(['lsof','-n','-P','--',*paths],capture_output=True,text=True);assert handles.returncode==1 and not handles.stdout.strip(),handles.stdout
(D/'OPEN_HANDLES_BEFORE_DELETE.txt').write_text(handles.stdout+'\n'+handles.stderr)
before=shutil.disk_usage(W).free;deleted=[]
for r in d['rows']:
 a=Path(r['temporary_path']);b=Path(r['retained_model']);assert st(a)==r['temporary_stat'] and st(b)==r['retained_stat'];a.unlink();assert not a.exists() and st(b)==r['retained_stat'];deleted.append(r['temporary_path'])
 (D/'DELETE_JOURNAL.json').write_text(json.dumps(dict(deleted=deleted,retained_models_unchanged=True),indent=2))
after=shutil.disk_usage(W).free
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,verified_report_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),deleted_paths=deleted,deleted_logical_bytes=sum(r['bytes'] for r in d['rows']),deleted_allocated_bytes=sum(r['temporary_stat']['allocated_bytes'] for r in d['rows']),free_before_bytes=before,free_after_bytes=after,observed_reclaimed_bytes=after-before,retained_models=[r['retained_model'] for r in d['rows']],retained_models_stats_unchanged=True,model_or_training_data_deleted=False,physical_launch_not_automatic=True)
dest.write_text(json.dumps(out,indent=2));print(json.dumps(dict(deleted_files=len(deleted),reclaimed_GiB=(after-before)/1024**3,free_GiB=after/1024**3,retained_models_unchanged=True),indent=2))
