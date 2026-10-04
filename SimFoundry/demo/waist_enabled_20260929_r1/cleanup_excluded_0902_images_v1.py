"""Remove excluded assist-era0902 image data only; preserve metadata and deletion hashes."""
from pathlib import Path
import datetime,hashlib,json,os,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];target=ROOT/'datasets/sorting_station_g1_23_unitree_0902';out=W/'excluded_0902_image_cleanup_r1';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert '不要训 / 不要混：`unitree_0902`' in (ROOT/'handoff.md').read_text()
# Current experimental protocols bind every required source/data by path.
checked=[]
for p in W.glob('*/PROTOCOL.json'):
 d=json.loads(p.read_text());mapping=d.get('frozen_files_sha256',{})
 assert not any(str(target) in k for k in mapping),p
 checked.append(dict(path=str(p),sha256=sha(p),frozen_paths=len(mapping)))
open_refs=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  cmd=(proc/'cmdline').read_bytes()
  if str(target).encode() in cmd:open_refs.append(str(proc))
  for fd in (proc/'fd').iterdir():
   try:
    if str(target) in os.readlink(fd):open_refs.append(str(fd))
   except (FileNotFoundError,PermissionError):pass
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
assert not open_refs,open_refs
files=sorted(target.rglob('*.jpg'));assert len(files)==38678
rows=[]
for p in files:
 assert not p.is_symlink() and p.is_file();s=p.stat();assert s.st_nlink==1
 rows.append(dict(path=str(p),bytes=s.st_size,allocated_bytes=s.st_blocks*512,inode=s.st_ino,sha256=sha(p)))
meta={str(p):sha(p) for p in target.rglob('*.json')};assert len(meta)==200
before=shutil.disk_usage(ROOT).free
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,authorization='Prior user requests to remove unrelated historical data and checkpoints; handoff explicitly excludes0902from training.',image_files=rows,metadata_sha256=meta,protocol_checks=checked,open_references=open_refs,free_before_bytes=before,planned_bytes=sum(r['allocated_bytes'] for r in rows),script_sha256=sha(Path(__file__)))
with (out/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2)
for row in rows:
 p=Path(row['path']);s=p.stat();assert s.st_ino==row['inode'] and s.st_nlink==1 and s.st_size==row['bytes'];assert sha(p)==row['sha256'];p.unlink()
for p,h in meta.items():assert sha(Path(p))==h
assert not list(target.rglob('*.jpg'))
after=shutil.disk_usage(ROOT).free
result=dict(completed=True,deleted_images=len(rows),metadata_files_preserved=len(meta),nominal_bytes=sum(r['bytes'] for r in rows),allocated_bytes=sum(r['allocated_bytes'] for r in rows),free_after_bytes=after,free_difference_bytes=after-before,plan_sha256=sha(out/'PLAN.json'),removed_dataset_is_incomplete_and_must_not_train=True)
with (out/'RESULT.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
