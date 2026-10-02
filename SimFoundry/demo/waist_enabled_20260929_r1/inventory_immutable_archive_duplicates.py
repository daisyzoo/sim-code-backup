"""Read-only SHA inventory; only archived source snapshots, never working code."""
from pathlib import Path
import hashlib,json,collections,datetime,os
W=Path(__file__).resolve().parent
rows=json.loads(Path('/tmp/substep_archive_dedup_candidates.json').read_text());groups=collections.defaultdict(list)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
for row in rows:
 p=Path(row['path']);assert p.is_relative_to(W) and ('source_snapshot' in p.parts or 'runtime_source' in p.parts) and not p.is_symlink()
 s=p.stat();assert (s.st_dev,s.st_ino,s.st_size)==(row['device'],row['inode'],row['size'])
 h=sha(p);row.update(sha256=h,mode=s.st_mode,uid=s.st_uid,gid=s.st_gid,blocks=s.st_blocks,mtime_ns=s.st_mtime_ns)
 groups[(s.st_dev,h,s.st_size,s.st_mode,s.st_uid,s.st_gid)].append(row)
out=[];free=0
for key,items in groups.items():
 inodes={x['inode'] for x in items}
 if len(inodes)<2:continue
 items.sort(key=lambda x:x['path']);out.append(dict(sha256=key[1],size=key[2],canonical=items[0]['path'],files=items))
 canonical_inode=items[0]['inode']
 for inode in inodes-{canonical_inode}:
  group=[x for x in items if x['inode']==inode]
  if len(group)==group[0]['nlink']:free+=group[0]['blocks']*512
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,groups=out,estimated_reclaimable_bytes=free,content_hashes_verified=True,mutations_performed=False)
p=W/'IMMUTABLE_ARCHIVE_DEDUP_INVENTORY.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print('SHA_VERIFIED',len(out),'duplicate groups','estimated reclaimable GiB',free/1024**3)
