from pathlib import Path
import os,json,hashlib,datetime,shutil,subprocess
ROOT=Path('/home/user/Documents/zoo/sim');W=ROOT/'SimFoundry/demo/waist_enabled_20260929_r1';OUT=W/'unused_video_base_checkpoint_cleanup_r1'
TARGET=ROOT/'nvidia/SimFoundry/deps/void-model/CogVideoX-Fun-V1.5-5b-InP/transformer/diffusion_pytorch_model.safetensors'
META=TARGET.parents[1]/'.cache/huggingface/download/transformer/diffusion_pytorch_model.safetensors.metadata'
revision,expected,*_=META.read_text().splitlines();assert revision=='85e5c23b6e864261d86dd9f26cd1cd96621d811e';assert expected=='e47e12ca6f33d29acd39bfc1bf0f45593dec27f6a38fa2722b35e814e812dabe'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
assert TARGET.is_file() and not TARGET.is_symlink();st=TARGET.stat();assert st.st_size==11142305104 and st.st_nlink==1
frozen={}
for name in ['front_box_recenter_physical_r2','front_inactive_clearance_physical_r1']:frozen.update(json.loads((W/name/'PROTOCOL.json').read_text())['frozen_files_sha256'])
assert str(TARGET) not in frozen and all(not p.startswith(str(TARGET.parent)+'/') for p in frozen)
# Verify no sorting-source references to the upstream optional video model.
references=[]
for root in [ROOT/'SimFoundry/simfoundry',ROOT/'SimFoundry/scripts']:
 for p in root.rglob('*'):
  if p.suffix not in ['.py','.json','.yaml','.yml','.toml','.sh'] or not p.is_file():continue
  if any(x in p.read_bytes() for x in [b'CogVideoX-Fun-V1.5-5b-InP',b'void-model',b'void_pass1',b'void_pass2']):references.append(str(p))
assert not references,references
# Protect the current latest training checkpoints and all sorting model weights.
protected={};links={}
for p in (ROOT/'lerobot/outputs').rglob('*'):
 if p.is_symlink() and p.name=='last':assert p.exists();links[str(p)]=str(p.resolve())
 if p.is_file() and not p.is_symlink() and p.name in ['model.safetensors','optimizer_state.safetensors']:
  s=p.stat();protected[str(p)]=dict(inode=s.st_ino,size=s.st_size,mtime_ns=s.st_mtime_ns)
def no_readers():
 busy=[];checked=0;uid=os.getuid()
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   if proc.stat().st_uid!=uid:continue
   checked+=1
   for fd in (proc/'fd').iterdir():
    try:
     q=fd.stat()
     if (q.st_dev,q.st_ino)==(st.st_dev,st.st_ino):busy.append([int(proc.name),'fd',str(fd)])
    except FileNotFoundError:pass
   if str(TARGET) in (proc/'maps').read_text():busy.append([int(proc.name),'maps'])
  except PermissionError:
   # Desktop PAM helper and ssh-agent hide /proc descriptors. Neither is a
   # Python/model process; independently require zero GPU compute processes.
   assert (proc/'comm').read_text().strip() in ['(sd-pam)','ssh-agent']
  except (FileNotFoundError,ProcessLookupError):continue
 assert not busy,busy
 return checked
checked=no_readers();gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True,capture_output=True,check=True);assert not gpu.stdout.strip()
actual=sha(TARGET);assert actual==expected
OUT.mkdir(exist_ok=False)
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),path=str(TARGET),bytes=st.st_size,inode=st.st_ino,nlink=st.st_nlink,sha256=actual,expected_hf_lfs_sha256=expected,hf_repository='alibaba-pai/CogVideoX-Fun-V1.5-5b-InP',hf_revision=revision,hf_filename='transformer/diffusion_pytorch_model.safetensors',reason='Optional upstream video background reconstruction base transformer; no current sorting pipeline references or userspace process readers. User authorized unrelated checkpoint cleanup.',descriptor_visibility_exceptions=['(sd-pam)','ssh-agent'],current_uid_processes_checked=checked,free_before_gib=shutil.disk_usage(ROOT).free/2**30,protected_models=protected,last_links=links,sorting_source_references=[],active_frozen_source_count=len(frozen),restore_argv=['hf','download','alibaba-pai/CogVideoX-Fun-V1.5-5b-InP','transformer/diffusion_pytorch_model.safetensors','--revision',revision,'--local-dir',str(TARGET.parents[1])])
(OUT/'PLAN.json').write_text(json.dumps(plan,indent=2));(OUT/'RESTORE.md').write_text('# Optional video model restoration\n\nOnly the unused upstream video base transformer was removed. Sorting policy weights and data are retained. The standard downloader uses config.json as its marker and may skip this missing weight; restore this exact file explicitly:\n\n```bash\nhf download alibaba-pai/CogVideoX-Fun-V1.5-5b-InP transformer/diffusion_pytorch_model.safetensors --revision '+revision+' --local-dir '+str(TARGET.parents[1])+'\n```\n\nExpected SHA256: `'+expected+'`.\n')
assert TARGET.stat().st_ino==st.st_ino and TARGET.stat().st_size==st.st_size;checked=no_readers();TARGET.unlink();assert not TARGET.exists()
for p,a in protected.items():
 b=Path(p).stat();assert (b.st_ino,b.st_size,b.st_mtime_ns)==(a['inode'],a['size'],a['mtime_ns'])
for p,t in links.items():assert Path(p).exists() and str(Path(p).resolve())==t
result=dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deleted_files=1,deleted_bytes=st.st_size,deleted_sha256=actual,current_uid_processes_checked=checked,free_after_gib=shutil.disk_usage(ROOT).free/2**30,observed_free_delta_gib=shutil.disk_usage(ROOT).free/2**30-plan['free_before_gib'],protected_model_files_unchanged=len(protected),last_links_preserved=len(links),sorting_data_deleted=False,sorting_weights_deleted=False,plan_sha256=sha(OUT/'PLAN.json'),restore_instructions=str(OUT/'RESTORE.md'))
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
