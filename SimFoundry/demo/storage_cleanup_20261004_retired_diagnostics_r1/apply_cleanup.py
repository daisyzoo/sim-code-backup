from pathlib import Path
import json,hashlib,os,datetime,shutil
P=Path('/home/user/Documents/zoo/sim/SimFoundry/demo/storage_cleanup_20261004_retired_diagnostics_r1');plan=json.loads((P/'PLAN.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not (P/'RESULT.json').exists();roots=plan['roots']
for p,h in plan['protected_owner_sha256'].items():assert sha(p)==h,p
for p,h in plan['retained_sha256'].items():assert sha(p)==h,p
for r in plan['files']:
 p=Path(r['path']);s=p.stat();assert p.name=='raw.npz' and not p.is_symlink() and any(p.is_relative_to(Path(x)) for x in roots);assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(r['device'],r['inode'],r['bytes'],r['mtime_ns']);assert s.st_nlink==1 and sha(p)==r['sha256']
hits=[];denied=[];helpers=[];checked=0;fd_denied=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 cmd='';owned=False
 try:
  owned=proc.stat().st_uid==os.getuid();cmd=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');cwd=os.readlink(proc/'cwd');fds=list((proc/'fd').iterdir());checked+=1
 except (FileNotFoundError,ProcessLookupError):continue
 except PermissionError:
  if owned:
   comm=(proc/'comm').read_text().strip();exe=(proc/'cmdline').read_bytes().split(b'\0')[0].decode()
   if (comm,exe) in [('(sd-pam)','(sd-pam)'),('ssh-agent','/usr/bin/ssh-agent')] and not any(r in cmd for r in roots):helpers.append(dict(pid=int(proc.name),comm=comm,executable=exe,reason='Protected login/auth daemon; descriptors unavailable, no target-path command.'))
   else:denied.append(int(proc.name))
  continue
 if any(r in cmd or cwd.startswith(r) for r in roots):hits.append(dict(pid=int(proc.name),kind='command_or_cwd'))
 for fd in fds:
  try:link=os.readlink(fd)
  except (FileNotFoundError,ProcessLookupError):continue
  except PermissionError:
   if owned:fd_denied.append(dict(pid=int(proc.name),fd=fd.name))
   continue
  if any(link.startswith(r+'/') for r in roots):hits.append(dict(pid=int(proc.name),kind='open_file'))
assert not hits and not denied and not fd_denied,(hits,denied,fd_denied)
before=shutil.disk_usage(P).free
for r in plan['files']:Path(r['path']).unlink()
for p,h in plan['retained_sha256'].items():assert sha(p)==h,p
assert all(not Path(r['path']).exists() for r in plan['files'])
for root in roots:
 count=sum(Path(r['path']).is_relative_to(Path(root)) for r in plan['files'])
 with (Path(root)/'RAW_RGB_REMOVED_20261004.md').open('x') as f:f.write(f'按用户清理历史测试数据授权，本目录移除{count}个已结束、未准入训练的旧诊断raw.npz。保留所有其他文件，包括报告、轨迹、复核图片和source_snapshot；原审核结论不变。完整RGB及原始数组不可再重放，不得作为完整训练数据。清单与检查见demo/storage_cleanup_20261004_retired_diagnostics_r1/PLAN.json及RESULT.json。\n')

result=dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),deleted_files=len(plan['files']),deleted_bytes=plan['total_bytes'],retained_files_verified=len(plan['retained_sha256']),processes_checked=checked,process_conflicts=hits,current_user_unexplained_unreadable=denied,current_user_fd_unreadable=fd_denied,known_protected_system_helpers=helpers,free_bytes_before=before,free_bytes_after=shutil.disk_usage(P).free,models_and_training_sources_unchanged=True,original_raw_replay_unavailable_for_deleted_evaluations=True,existing_review_statuses_preserved=True,goal_complete=False)
(P/'apply_cleanup.py').write_bytes(Path(__file__).read_bytes())
with (P/'RESULT.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
