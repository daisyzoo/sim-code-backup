from pathlib import Path
import os,json,hashlib,datetime,shutil
p=Path('/home/user/Documents/zoo/sim/SimFoundry/demo/storage_cleanup_20261004_retired_zero_pass_raw_r1');plan=json.loads((p/'PLAN.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not (p/'RESULT.json').exists();roots=[str(p.parent/n) for n in plan['statuses']]
for f,h in plan['protected_owner_sha256'].items():assert sha(f)==h
for f,h in plan['retained_sha256'].items():assert sha(f)==h
for r in plan['files']:
 f=Path(r['path']);s=f.stat();assert f.name=='raw.npz' and not f.is_symlink() and any(f.is_relative_to(root) for root in map(Path,roots));assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(r['device'],r['inode'],r['bytes'],r['mtime_ns']);assert s.st_nlink==1 and sha(f)==r['sha256']
hits=[];owned_denied=[];system_helpers=[];checked=0
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  owned=proc.stat().st_uid==os.getuid();raw=(proc/'cmdline').read_bytes();cmd=raw.replace(b'\0',b' ').decode(errors='replace');cwd=os.readlink(proc/'cwd');fds=list((proc/'fd').iterdir());checked+=1
 except (FileNotFoundError,ProcessLookupError):continue
 except PermissionError:
  if owned:
   comm=(proc/'comm').read_text().strip();exe=(proc/'cmdline').read_bytes().split(b'\0')[0].decode()
   if (comm,exe) in [('(sd-pam)','(sd-pam)'),('ssh-agent','/usr/bin/ssh-agent')] and not any(r in cmd for r in roots):system_helpers.append(dict(pid=int(proc.name),comm=comm,executable=exe,reason='Protected login/authentication daemon, not a simulation or data job. Descriptor inspection unavailable; no target-path command reference.'))
   else:owned_denied.append(int(proc.name))
  continue
 if any(r in cmd or cwd.startswith(r) for r in roots):hits.append((proc.name,'command/cwd'))
 for fd in fds:
  try:link=os.readlink(fd)
  except (FileNotFoundError,PermissionError):continue
  if any(link.startswith(r+'/') for r in roots):hits.append((proc.name,'fd'))
assert not hits and not owned_denied,(hits,owned_denied)
before=shutil.disk_usage(p).free
for r in plan['files']:Path(r['path']).unlink()
for f,h in plan['retained_sha256'].items():assert sha(f)==h
assert not any(Path(r['path']).exists() for r in plan['files'])
for root in roots:
 with (Path(root)/'RAW_RGB_REMOVED_20261004.md').open('x') as f:f.write('按用户清理历史无关中间数据的授权，移除了本目录已关闭且未入库诊断的 raw.npz。其余文件及既有数值报告、复核图片保留；当前运行与排队实验的5860来源及5708文本来源扫描未引用本目录，未发现采集/训练/审核进程占用。原始数组与完整RGB不能再完整复核或重放，不得将本目录作为完整训练样本入库。删除清单、原SHA256、保留文件校验及进程扫描限制见 ../storage_cleanup_20261004_retired_zero_pass_raw_r1/PLAN.json 与 RESULT.json。\n')
result=dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(p/'PLAN.json'),deleted_files=len(plan['files']),deleted_bytes=sum(r['bytes'] for r in plan['files']),retained_files_verified=len(plan['retained_sha256']),free_bytes_before=before,free_bytes_after=shutil.disk_usage(p).free,current_user_processes_unexplained_unreadable=owned_denied,known_protected_system_helpers=system_helpers,processes_checked=checked,process_conflicts=hits,known_descriptor_limitations_documented=True,original_raw_replay_unavailable=True,models_and_admitted_datasets_unchanged=True,goal_complete=False)
with (p/'RESULT.json').open('x') as f:json.dump(result,f,indent=2)
(p/'apply_cleanup.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
