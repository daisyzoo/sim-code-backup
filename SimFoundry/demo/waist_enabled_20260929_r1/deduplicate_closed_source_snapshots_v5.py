"""Deduplicate byte-identical archived source snapshots in closed experiments.
Never links working source files, raw observations, reports, or active runs.
All archive paths and SHA256 content stay unchanged. Inode/mtime may change;
original metadata are recorded before mutation. Snapshots must stay immutable.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,stat,shutil
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory():
 seen={};rows=[];runs={};scanned=0
 for run in sorted(W.iterdir()):
  result=run/'RESULT.json'
  if not run.is_dir() or not result.is_file():continue
  result_data=json.loads(result.read_text())
  # Only terminal runs with an explicit completed inventory are candidates.
  audit=run/'AUDIT_STATUS.json'
  audit_complete=audit.is_file() and json.loads(audit.read_text()).get('status')=='complete'
  legacy_closed=bool(result_data.get('closed_at_utc') and result_data.get('status','').startswith('diagnostic_closed'))
  trial_closed=result_data.get('status')=='complete_trial_audited'
  if not (audit_complete or legacy_closed or trial_closed):continue
  live=False
  for proc in Path('/proc').iterdir():
   if not proc.name.isdigit():continue
   try:cmd=(proc/'cmdline').read_bytes().split(b'\0')
   except (FileNotFoundError,PermissionError,ProcessLookupError):continue
   if any(v.decode(errors='replace').startswith(str(run.resolve())+'/') or v.decode(errors='replace')==str(run.resolve()) for v in cmd):live=True;break
  if live:continue
  runs[str(result)]=sha(result)
  for provfile in sorted(run.glob('case_*/provenance.json')):
   prov=json.loads(provfile.read_text());root=provfile.parent
   entries={'source_snapshot/'+n:h for n,h in prov['source_sha256'].items()}
   for name in ['runtime_geometry_provenance.json','SUBSTEP_RUNTIME_BINDING.json']:
    manifest=root/name
    if not manifest.exists():continue
    for record in json.loads(manifest.read_text())['source_files'].values():
     rel=record['snapshot'];assert Path(rel).parts[0] in ['runtime_source','substep_runtime_sources']
     entries[rel]=record['sha256']
   for rel,h in sorted(entries.items()):
    rel=Path(rel);assert not rel.is_absolute() and '..' not in rel.parts
    p=root/rel
    if p.is_symlink() or not p.is_file():continue
    st=p.stat()
    if st.st_size<4096 or not stat.S_ISREG(st.st_mode):continue
    assert root.resolve() in p.resolve().parents
    assert sha(p)==h,(p,'archive hash mismatch');scanned+=1
    key=(h,st.st_size,st.st_mode,st.st_uid,st.st_gid,st.st_dev)
    if key not in seen:seen[key]=p;continue
    origin=seen[key];ost=origin.stat()
    if (ost.st_dev,ost.st_ino)==(st.st_dev,st.st_ino):continue
    rows.append(dict(path=str(p),canonical=str(origin),sha256=h,size=st.st_size,original_inode=st.st_ino,original_nlink=st.st_nlink,original_mtime_ns=st.st_mtime_ns,canonical_inode=ost.st_ino,estimated_free_bytes=st.st_blocks*512 if st.st_nlink==1 else 0))
 return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,closed_results_sha256=runs,scanned_large_files=scanned,estimated_free_bytes=sum(x['estimated_free_bytes'] for x in rows),free_bytes_before=shutil.disk_usage(W).free,training_ready=False)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args();folder=W/'closed_source_snapshot_dedup_r5'
 if not args.apply:
  folder.mkdir(exist_ok=False);plan=inventory()
  with (folder/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2)
  print(json.dumps(dict(candidates=len(plan['rows']),closed_runs=len(plan['closed_results_sha256']),estimated_free_gib=plan['estimated_free_bytes']/2**30,scanned=plan['scanned_large_files'])))
 else:
  plan=json.loads((folder/'PLAN.json').read_text());assert not (folder/'RESULT.json').exists()
  for p,h in plan['closed_results_sha256'].items():assert sha(p)==h
  completed=[]
  with (folder/'APPLIED.jsonl').open('x') as log:
   for row in plan['rows']:
    if shutil.disk_usage(W).free>=36*2**30:break
    p=Path(row['path']);origin=Path(row['canonical']);assert not p.is_symlink() and not origin.is_symlink()
    st=p.stat();ost=origin.stat();assert st.st_ino==row['original_inode'] and st.st_dev==ost.st_dev
    assert sha(p)==sha(origin)==row['sha256'] and st.st_size==ost.st_size==row['size']
    assert (st.st_mode,st.st_uid,st.st_gid)==(ost.st_mode,ost.st_uid,ost.st_gid)
    tmp=p.with_name(p.name+'.dedup-link-tmp');assert not tmp.exists();os.link(origin,tmp);assert sha(tmp)==row['sha256'];os.replace(tmp,p);assert p.stat().st_ino==origin.stat().st_ino and sha(p)==row['sha256']
    done=dict(row,new_inode=p.stat().st_ino,content_verified=True);log.write(json.dumps(done)+'\n');log.flush();os.fsync(log.fileno());completed.append(done)
  for row in completed:assert sha(row['path'])==row['sha256']==sha(row['canonical'])
  for p,h in plan['closed_results_sha256'].items():assert sha(p)==h
  report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,completed=len(completed),free_gib_after=shutil.disk_usage(W).free/2**30,observed_free_delta_gib=(shutil.disk_usage(W).free-plan['free_bytes_before'])/2**30,plan_sha256=sha(folder/'PLAN.json'),applied_manifest_sha256=sha(folder/'APPLIED.jsonl'),all_paths_retained=True,all_content_hashes_verified=True,working_sources_linked=False,active_runs_modified=False)
  with (folder/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
  print(json.dumps(report,indent=2))
