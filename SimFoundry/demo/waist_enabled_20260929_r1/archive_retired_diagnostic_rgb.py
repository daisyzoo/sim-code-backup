"""User-authorized historical RGB slimming; retain exact nonRGB and reviews.
Never touches current dependencies, converted-data sources, models or raw datasets.
"""
from pathlib import Path
import collections,datetime,hashlib,json,os,re,shutil,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];SIM=ROOT.parent;OUT=W/'retired_rgb_archive_20261002_r1';ACTIVE=W/'instant_guard_groups_r1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def identity(p):
 s=p.stat();return dict(size=s.st_size,mtime_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev,links=s.st_nlink,allocated=s.st_blocks*512)
def open_paths():
 used=set()
 for proc in Path('/proc').glob('[0-9]*'):
  try:
   for fd in (proc/'fd').iterdir():
    try:used.add(os.readlink(fd).removesuffix(' (deleted)'))
    except OSError:pass
  except OSError:pass
  try:
   for row in (proc/'maps').read_text().splitlines():
    v=row.split(maxsplit=5)
    if len(v)==6 and v[5].startswith('/'):used.add(v[5])
  except OSError:pass
 return used

def plan():
 OUT.mkdir();protocol=json.loads((ACTIVE/'PROTOCOL.json').read_text());frozen=protocol['frozen_files_sha256'];protected_groups=set();protected_files=set(map(str,map(Path,frozen)))
 for f in map(Path,frozen):
  assert sha(f)==frozen[str(f)],f
  if f.suffix in {'.py','.json','.md','.yaml','.txt'}:
   protected_groups.update(g.decode() for g in re.findall(rb'[a-zA-Z0-9_]+_groups_r[0-9]+',f.read_bytes()))
 # Exact raw paths declared by all converted paired datasets remain intact.
 for p in (SIM/'lerobot').glob('*/meta/paired_provenance.json'):
  d=json.loads(p.read_text())
  for row in d.get('records',[]):
   x=Path(row['path']);protected_files.add(str((x if x.is_absolute() else SIM/x).resolve()))
 protected_ids={(Path(p).stat().st_dev,Path(p).stat().st_ino) for p in protected_files if Path(p).is_file()}
 used=open_paths();rows=[];retained=[];runs=[]
 for root in sorted(W.glob('*_groups_r[12]')):
  if root.name in protected_groups or not (root/'RESULT.json').exists() or not (root/'STATUS.json').exists():continue
  result=json.loads((root/'RESULT.json').read_text());state=json.loads((root/'STATUS.json').read_text())
  reviewed=str(result.get('visual_review','')).startswith('completed') or result.get('actual_review_complete') is True
  if not reviewed or not state.get('updated_at_utc','').startswith(('2026-09-29','2026-09-30')) or (Path('/proc')/str(state.get('pid'))).exists():continue
  records={r['episode']:r for r in result.get('rows',[])};groups=collections.defaultdict(list)
  for raw in root.glob('case_*/layout_*/raw.npz'):
   if raw.is_symlink() or 'wait_no_package' in raw.parent.name or raw.parent.name not in records:continue
   q=json.loads((raw.parent/'quality.json').read_text());row=records[raw.parent.name];ok=q['passed'] and row.get('pose',{}).get('search_success',True)
   task='box' if 'push_box' in raw.parent.name else 'mailer';groups[(task,ok)].append(raw)
  keep=set()
  for (task,ok),paths in groups.items():
   # Retain the least-progress failure and the largest-progress success.
   key=lambda p:json.loads((p.parent/'quality.json').read_text())['metrics'].get('target_final_progress_m',0)
   keep.add((max if ok else min)(paths,key=key))
  root_rows=[]
  for raw in [p for paths in groups.values() for p in paths]:
   if raw in keep:retained.append(dict(path=str(raw),identity=identity(raw)));continue
   if str(raw.resolve()) in protected_files or (raw.stat().st_dev,raw.stat().st_ino) in protected_ids or str(raw) in used or raw.stat().st_nlink!=1:continue
   row=records[raw.parent.name];review=row.get('actual_review',row);sheet=raw.parent/'REVIEW_EVEN.jpg'
   if not review.get('raw_sha256') or not review.get('review_sheet_sha256') or not sheet.exists():continue
   assert sha(sheet)==review['review_sheet_sha256']
   assert not (raw.parent/'archived_state_actions.npz').exists()
   root_rows.append(dict(path=str(raw),identity=identity(raw),expected_raw_sha256=review['raw_sha256'],review_sheet_sha256=review['review_sheet_sha256'],result_path=str(root/'RESULT.json'),result_sha256=sha(root/'RESULT.json')))
  if root_rows:runs.append(str(root));rows.extend(root_rows)
 total=sum(r['identity']['allocated'] for r in rows)
 manifest=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason=__doc__,files=rows,retained_representative_raw=retained,runs=runs,active_protocol_sha256=sha(ACTIVE/'PROTOCOL.json'),protected_groups=sorted(protected_groups),protected_files=sorted(protected_files),expected_reclaim_bytes=total,free_before=shutil.disk_usage(W).free)
 (OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(dict(files=len(rows),runs=len(runs),kept_representatives=len(retained),expected_GiB=total/2**30,manifest=str(OUT/'MANIFEST.json')),indent=2))

def apply():
 m=json.loads((OUT/'MANIFEST.json').read_text());assert sha(ACTIVE/'PROTOCOL.json')==m['active_protocol_sha256'];used=open_paths()
 for row in m['files']:
  p=Path(row['path']);assert identity(p)==row['identity'] and str(p) not in used
 for r in m['retained_representative_raw']:assert identity(Path(r['path']))==r['identity']
 journal=OUT/'ARCHIVED.jsonl'
 with journal.open('x') as log:
  for i,row in enumerate(m['files']):
   p=Path(row['path']);assert identity(p)==row['identity'];assert sha(p)==row['expected_raw_sha256'];assert sha(row['result_path'])==row['result_sha256']
   archive=p.parent/'archived_state_actions.npz';assert not archive.exists()
   with np.load(p,allow_pickle=False) as z:
    assert 'rgb' in z.files;arrays={k:z[k] for k in z.files if k!='rgb'}
   np.savez_compressed(archive,**arrays)
   with np.load(archive,allow_pickle=False) as z:
    assert set(z.files)==set(arrays)
    for k,value in arrays.items():assert z[k].dtype==value.dtype and z[k].shape==value.shape and z[k].tobytes()==value.tobytes(),k
   rec=dict(raw_path=str(p),raw_sha256=row['expected_raw_sha256'],retained_arrays=list(arrays),archive_sha256=sha(archive),review_sheet_sha256=row['review_sheet_sha256'],rgb_removed=True,training_ready=False,note='Historical complete RGB removed by user-authorized slimming; all nonRGB arrays byte-verified, original actual review sheets/external images/results retained. This archive is not a complete replayable or trainable episode.')
   (p.parent/'RAW_ARCHIVED.json').write_text(json.dumps(rec,indent=2))
   assert identity(p)==row['identity'] and str(p) not in open_paths();p.unlink();log.write(json.dumps(rec)+'\n');log.flush()
   if (i+1)%10==0:print('archived',i+1,'/',len(m['files']),flush=True)
 for root in map(Path,m['runs']):
  (root/'RAW_RGB_PRUNED.md').write_text('Historical diagnostic RGB was slimmed on2026-10-02 under the user cleanup instruction. All nonRGB arrays were preserved and byte-verified in archived_state_actions.npz; existing actual review sheets, external frames, results and source archives remain. Each available task/pass-fail category retains a complete representative raw. Pruned episodes are NOT complete training data and old full-raw hashes cannot now be revalidated. See ../retired_rgb_archive_20261002_r1/MANIFEST.json and ARCHIVED.jsonl.\n')
 for r in m['retained_representative_raw']:assert identity(Path(r['path']))==r['identity']
 for p in m['protected_files']:assert Path(p).exists(),p
 active=json.loads((ACTIVE/'PROTOCOL.json').read_text())
 for p,h in active['frozen_files_sha256'].items():assert sha(p)==h,p
 result=dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),archived_raw_count=len(m['files']),historical_runs=len(m['runs']),non_rgb_byte_verified=True,retained_representative_count=len(m['retained_representative_raw']),all_current_frozen_sources_unchanged=True,model_and_dataset_files_deleted=0,free_before_GiB=m['free_before']/2**30,free_after_GiB=shutil.disk_usage(W).free/2**30,reclaimed_file_allocated_GiB=sum(r['identity']['allocated'] for r in m['files'])/2**30,scope='Historical RGB removal is irreversible; exact nonRGB and sampled images retained, original complete RGB no longer available. Free delta includes concurrent current-run writes.')
 (OUT/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':globals()[sys.argv[1]]()
