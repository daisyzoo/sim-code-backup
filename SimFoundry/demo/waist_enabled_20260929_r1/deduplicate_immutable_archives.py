"""Share identical immutable archive bytes via hardlinks; retain every pathname.
Never links live working source to archives. Every replacement is hash-verified.
"""
from pathlib import Path
import os,json,hashlib,datetime,shutil
W=Path(__file__).resolve().parent;inventory=W/'IMMUTABLE_ARCHIVE_DEDUP_INVENTORY.json';data=json.loads(inventory.read_text());out=W/'IMMUTABLE_ARCHIVE_DEDUP_RESULT.json';assert not out.exists()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
def archived(p):
 assert p.is_relative_to(W) and ('source_snapshot' in p.parts or 'runtime_source' in p.parts) and p.is_file() and not p.is_symlink()
before=shutil.disk_usage(W).free;records=[]
log=W/'IMMUTABLE_ARCHIVE_DEDUP_OPERATIONS.jsonl';assert not log.exists()
with log.open('x') as stream:
 for g in data['groups']:
  canonical=Path(g['canonical']);archived(canonical);assert sha(canonical)==g['sha256']
  for row in g['files']:
   p=Path(row['path']);archived(p);s=p.stat();assert s.st_size==g['size'] and sha(p)==g['sha256']
   if s.st_ino==canonical.stat().st_ino:continue
   assert s.st_dev==canonical.stat().st_dev and (s.st_mode,s.st_uid,s.st_gid)==(row['mode'],row['uid'],row['gid'])
   temporary=p.with_name(p.name+'.dedup-link-tmp');assert not temporary.exists()
   os.link(canonical,temporary)
   assert sha(temporary)==g['sha256'];os.replace(temporary,p)
   assert p.stat().st_ino==canonical.stat().st_ino and sha(p)==g['sha256']
   record=dict(path=str(p),canonical=str(canonical),sha256=g['sha256'],bytes=g['size'],old_inode=s.st_ino,new_inode=p.stat().st_ino)
   stream.write(json.dumps(record)+'\n');stream.flush();records.append(record)
 # Verify all requested archive names including already-linked files.
 for g in data['groups']:
  for row in g['files']:assert sha(Path(row['path']))==g['sha256']
after=shutil.disk_usage(W).free
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,replacements=len(records),duplicate_groups=len(data['groups']),free_bytes_before=before,free_bytes_after=after,observed_free_delta_bytes=after-before,estimated_reclaimable_bytes=data['estimated_reclaimable_bytes'],all_paths_and_content_hashes_preserved=True,live_working_files_linked=False,inventory_sha256=sha(inventory),operations_sha256=sha(log),script_sha256=sha(Path(__file__)),note='Hardlinked archive files remain immutable. To edit a future copy, copy bytes to a new inode first; do not edit an archived snapshot in place.')
out.write_text(json.dumps(report,indent=2));print('ARCHIVE_CONTENT_PRESERVED',len(records),'replacements','free_delta_GiB',(after-before)/1024**3,'available_GiB',after/1024**3)
