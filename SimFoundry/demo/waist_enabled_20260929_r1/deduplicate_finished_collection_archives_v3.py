"""Lossless deduplication only of provenance-bound, completed-collection archives.
CPU audits may still read these immutable archives. No working stage, trajectory,
report or checkpoint is linked or removed. Preserve every path and content hash.
Archived sources must never subsequently be modified in place.
"""
from pathlib import Path
import json,hashlib,os,stat,datetime,shutil,sys
W=Path(__file__).resolve().parent;D=W/'finished_collection_archive_dedup_r3';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());names=['front_box_material_physical_r1','front_box_recenter_physical_r2','rear_waypoint_physical_r2','front_drive_1mm_physical_r1','front_projection_physical_r1']
def validate_runs():
 bound={}
 for name in names:
  run=W/name;s=read(run/'STATUS.json');p=read(run/'PROTOCOL.json');v=read(run/'NUMERIC_VISUAL_SUMMARY.json');assert s['status']=='collection_complete_audits_visual_pending' and s['completed_conditions']==10 and v['actual_reviews']==10
  proc=Path('/proc')/str(p['producer_pid']);assert not proc.exists() or (proc/'stat').read_text().rsplit(')',1)[1].split()[0]=='Z'
  for c in read(run/'COLLECTION_EXECUTION.json'):
   for f,h in c['source_sha256'].items():assert sha(Path(f))==h
  for f in ['STATUS.json','PROTOCOL.json','NUMERIC_VISUAL_SUMMARY.json','COLLECTION_EXECUTION.json']:bound[str(run/f)]=sha(run/f)
 return bound
if '--apply' not in sys.argv:
 assert not D.exists();D.mkdir();bound=validate_runs();seen={};rows=[];checked=0
 for name in names:
  for p in sorted((W/name).glob('case_*/provenance.json')):
   case=p.parent;entries={'source_snapshot/'+k:h for k,h in read(p)['source_sha256'].items()}
   for n in ['runtime_geometry_provenance.json','SUBSTEP_RUNTIME_BINDING.json']:
    m=case/n
    if m.exists():
     for r in read(m)['source_files'].values():
      assert Path(r['snapshot']).parts[0] in ['runtime_source','substep_runtime_sources'];entries[r['snapshot']]=r['sha256']
   for rel,h in sorted(entries.items()):
    f=case/rel;assert '..' not in Path(rel).parts and not Path(rel).is_absolute() and not f.is_symlink();st=f.stat();assert stat.S_ISREG(st.st_mode);assert sha(f)==h
    if st.st_size<4096:continue
    checked+=1;key=(h,st.st_size,st.st_mode,st.st_uid,st.st_gid,st.st_dev);origin=seen.setdefault(key,f);ost=origin.stat()
    if ost.st_ino==st.st_ino:continue
    rows.append(dict(path=str(f),canonical=str(origin),sha256=h,size=st.st_size,original_inode=st.st_ino,original_nlink=st.st_nlink,original_mtime_ns=st.st_mtime_ns,estimated_free_bytes=st.st_blocks*512 if st.st_nlink==1 else 0))
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,completed_collection_files_sha256=bound,files_checked=checked,estimated_free_gib=sum(x['estimated_free_bytes'] for x in rows)/2**30,free_gib_before=shutil.disk_usage(W).free/2**30)
 with (D/'PLAN.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:v for k,v in out.items() if k not in ['rows','completed_collection_files_sha256','scope']}))
else:
 plan=read(D/'PLAN.json');assert not (D/'RESULT.json').exists();assert validate_runs()==plan['completed_collection_files_sha256'];paths={Path(r[k]).resolve() for r in plan['rows'] for k in ['path','canonical']};writers=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   for fd in (proc/'fd').iterdir():
    try:
     target=fd.resolve()
     if target not in paths:continue
     fields=dict(line.split(':',1) for line in (proc/'fdinfo'/fd.name).read_text().splitlines() if ':' in line);flags=int(fields['flags'].strip(),8)
     if flags&os.O_ACCMODE in [os.O_WRONLY,os.O_RDWR]:writers.append([proc.name,str(target)])
    except (OSError,RuntimeError):pass
  except OSError:pass
 assert not writers,writers;before=shutil.disk_usage(W).free;done=[]
 with (D/'APPLIED.jsonl').open('x') as log:
  for r in plan['rows']:
   p=Path(r['path']);origin=Path(r['canonical']);st=p.stat();ost=origin.stat();assert st.st_ino==r['original_inode'] and st.st_dev==ost.st_dev and not p.is_symlink() and not origin.is_symlink();assert sha(p)==sha(origin)==r['sha256'];assert (st.st_mode,st.st_uid,st.st_gid)==(ost.st_mode,ost.st_uid,ost.st_gid)
   tmp=p.with_name(p.name+'.dedup-finished-tmp');assert not tmp.exists();os.link(origin,tmp);assert sha(tmp)==r['sha256'];os.replace(tmp,p);assert p.stat().st_ino==origin.stat().st_ino;done.append(r);log.write(json.dumps(r)+'\n');log.flush()
  os.fsync(log.fileno())
 for r in done:assert sha(Path(r['path']))==sha(Path(r['canonical']))==r['sha256']
 assert validate_runs()==plan['completed_collection_files_sha256'];after=shutil.disk_usage(W).free
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,archival_files_relinked=len(done),all_original_paths_and_hashes_preserved=True,working_stages_or_data_or_checkpoints_modified=False,active_collection_count=0,writable_archive_fds_found=0,observed_free_delta_gib=(after-before)/2**30,free_gib_after=after/2**30,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'PLAN.json',D/'APPLIED.jsonl']},training_ready=False)
 with (D/'RESULT.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']}))
