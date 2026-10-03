"""Inventory rebuildable caches and script-created stale temporary fixtures.
No deletion here. Do not follow symlinks; protect any file bound by a report hash
or held open/mapped by a same-user process. Keep all models and project evidence.
"""
from pathlib import Path
import os,re,json,stat,time,datetime,hashlib,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prefixes={};now=time.time()
for p in W.glob('*.py'):
 for prefix in re.findall(r'mkdtemp\(prefix=[\'"]([^\'"]+)',p.read_text()):prefixes.setdefault(prefix,[]).append(str(p))
roots=[]
for p in Path('/tmp').iterdir():
 if p.is_symlink() or not p.is_dir() or p.stat().st_uid!=os.getuid() or now-p.stat().st_mtime<3600:continue
 matches=[k for k in prefixes if p.name.startswith(k)]
 if matches:roots.append(dict(path=str(p),kind='completed_project_temporary_fixture',generators=sorted(set(n for k in matches for n in prefixes[k]))))
 elif p.name.startswith('wp_pch_') and all(x.suffix=='.pch' and x.is_file() and not x.is_symlink() for x in p.iterdir()):roots.append(dict(path=str(p),kind='temporary_warp_precompiled_headers',generators=[]))
for p in ['/home/user/.nv/ComputeCache','/home/user/.cache/ov/shaders','/home/user/.cache/ov/DerivedDataCache','/home/user/.cache/warp/1.16.0']:
 root=Path(p)
 if root.is_dir() and not root.is_symlink():roots.append(dict(path=p,kind='rebuildable_compiled_cache',generators=[]))
root_prefixes=tuple(r['path']+'/' for r in roots);protected={};reports=[]
# Search JSON evidence in this project root and staged configurations. Nested
# physical-run records are untouched; their state/source hash maps never point
# at cache or temporary fixtures. Bound report references are checked recursively.
jsons=list(W.glob('*.json'))+[p for d in W.glob('staged_*') if d.is_dir() for p in d.glob('*.json')]
pattern=re.compile('|'.join(re.escape(p) for p in root_prefixes))
def visit(value,report):
 if isinstance(value,dict):
  for k,v in value.items():
   if isinstance(k,str) and k.startswith(root_prefixes) and isinstance(v,str) and re.fullmatch('[0-9a-f]{32,128}',v):protected.setdefault(k,[]).append(str(report))
  if any('sha256' in k for k in value):
   for k,v in value.items():
    if isinstance(v,str) and v.startswith(root_prefixes):protected.setdefault(v,[]).append(str(report))
  for v in value.values():visit(v,report)
 elif isinstance(value,list):
  for v in value:visit(v,report)
for p in jsons:
 text=p.read_text()
 if pattern.search(text):visit(json.loads(text),p);reports.append(dict(path=str(p),sha256=sha(p)))
opened=set();checked=[];unreadable=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  if proc.stat().st_uid!=os.getuid():continue
  for key in ['cwd','exe']:
   try:opened.add(os.readlink(proc/key).removesuffix(' (deleted)'))
   except FileNotFoundError:pass
  for fd in (proc/'fd').iterdir():
   try:opened.add(os.readlink(fd).removesuffix(' (deleted)'))
   except FileNotFoundError:pass
  for line in (proc/'maps').read_text().splitlines():
   parts=line.split(maxsplit=5)
   if len(parts)==6 and parts[5].startswith('/'):opened.add(parts[5].removesuffix(' (deleted)'))
  checked.append(int(proc.name))
 except FileNotFoundError:pass
 except PermissionError:unreadable.append(int(proc.name))
# Do not make the broad claim that all OS processes are inspectable; refuse to
# delete if a current-user process could not be checked.
protected_services=[]
for pid in unreadable:
 proc=Path('/proc')/str(pid);name=(proc/'comm').read_text().strip()
 assert name in ['(sd-pam)','ssh-agent'] and (proc/'fd').stat().st_uid==0,('unreadable cache-capable process',pid,name)
 protected_services.append(dict(pid=pid,comm=name,fd_owner_uid=0,reason='OS-protected authentication service, not a compiler, renderer or experiment process; FDs not inspected'))
files=[];skipped=[];groupbytes={}
for root in roots:
 for base,dirs,names in os.walk(root['path'],followlinks=False):
  dirs[:]=[d for d in dirs if not (Path(base)/d).is_symlink()]
  for name in names:
   p=Path(base)/name;s=p.lstat()
   if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.getuid() or s.st_nlink!=1:continue
   if str(p) in protected or str(p) in opened or any(o==root['path'] or o.startswith(str(p)+'/') for o in opened):skipped.append(dict(path=str(p),reason='hash_bound_or_process_reference'));continue
   if any(o==str(p.parent) for o in opened):skipped.append(dict(path=str(p),reason='process_working_directory'));continue
   if now-s.st_mtime<3600:continue
   files.append(dict(path=str(p),root=root['path'],kind=root['kind'],size=s.st_size,allocated=s.st_blocks*512,dev=s.st_dev,inode=s.st_ino,mode=s.st_mode,uid=s.st_uid,mtime_ns=s.st_mtime_ns,sha256=sha(p)))
   groupbytes[root['path']]=groupbytes.get(root['path'],0)+s.st_blocks*512
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,roots=roots,files=files,skipped=skipped,protected_hash_references=protected,reports_inspected=len(jsons),reports_with_matching_text=reports,checked_processes=checked,protected_authentication_service_exceptions=protected_services,free_bytes=shutil.disk_usage(W).free,estimated_reclaimable_bytes=sum(f['allocated'] for f in files),reclaimable_by_root=groupbytes,script_sha256=sha(__file__),deletion_performed=False)
p=W/'FRONT_Z_PRIORITY_DISPOSABLE_STORAGE_INVENTORY.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(files=len(files),estimated_gib=out['estimated_reclaimable_bytes']/1024**3,free_gib=out['free_bytes']/1024**3,projected_free_gib=(out['free_bytes']+out['estimated_reclaimable_bytes'])/1024**3,protected_files=len(protected),skipped=len(skipped),checked_processes=len(checked)),indent=2))
