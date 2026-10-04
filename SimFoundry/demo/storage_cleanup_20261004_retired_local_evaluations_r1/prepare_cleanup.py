from pathlib import Path
import json,hashlib,datetime,shutil
ROOT=Path('/home/user/Documents/zoo/sim/SimFoundry');P=ROOT/'demo/storage_cleanup_20261004_retired_local_evaluations_r1';P.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();probe=json.loads(Path('/tmp/retired_local_evaluation_probe_20261004.json').read_text());rows=[r for r in probe['candidates'] if r['files']];assert len(rows)==7
files=[];retained={};evidence={}
for r in rows:
 assert not r['references'] and not r['direct_protected_files'];root=Path(r['root']);assert root.is_dir()
 if root.name=='spatial_baseline_heldout_20260928_r1':
  s=json.loads((root/'STATUS.json').read_text());assert s['stage']=='complete_reviewed' and s['total']==39 and s['numerical_passed']==0;evidence[str(root)]=s
 else:
  assert root.parent==ROOT/'demo/short_first_model40_20260929_r1/evaluation' and 'local320_seed' in root.name
  e=json.loads((root/'EVALUATION.json').read_text());assert len(e['rows'])==5 and sum(x['total'] for x in e['summary'])==5
  evidence[str(root)]=dict(numerically_completed_rows=5,visual_review_field=e['visual_review'],scope='Retired local320 policy evaluation only; not demonstrations/training data. Existing pending visual labels are preserved, not upgraded.')
 for p in root.rglob('*'):
  if not p.is_file() or p.is_symlink():continue
  if str(p) in r['files']:
   st=p.stat();assert p.name=='raw.npz' and st.st_nlink==1;files.append(dict(path=str(p),bytes=st.st_size,sha256=sha(p),device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
  else:retained[str(p)]=sha(p)
model=ROOT/'demo/short_first_model40_20260929_r1'
for p in model.iterdir():
 if p.is_file():retained[str(p)]=sha(p)
# All spatial39 and original160 raw arrays under this historical model remain intact.
protected_raws=[p for root in model.glob('evaluation/*') if root.is_dir() and ('spatial160' in root.name or 'original160' in root.name) for p in root.rglob('raw.npz')]
for p in protected_raws:retained[str(p)]=sha(p)
assert len(files)==69 and len(protected_raws)>0
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_deleted',authorization='User explicitly authorized deleting unrelated historical testing/intermediate data and checkpoints; only retired evaluation raw arrays selected here.',roots=[r['root'] for r in rows],files=files,total_bytes=sum(x['bytes'] for x in files),retained_sha256=retained,protected_spatial39_original160_raw_files=len(protected_raws),evidence=evidence,protected_sources=probe['protected_sources'],text_sources_scanned=probe['text_sources_scanned'],protected_owner_sha256={p:sha(p) for p in probe['owners']},scope='Preserve all reports/traces/contact sheets, original pending review labels, training sources, checkpoints and spatial39/original160 comparison raw arrays. Delete only39 old zero-pass baseline raw arrays and30 retired local320 model evaluation arrays; no training use. Full RGB replay of these69 will become unavailable.',deletions_performed=False,free_bytes_before=shutil.disk_usage(ROOT).free)
(P/'PLAN.json').write_text(json.dumps(plan,indent=2));(P/'REFERENCE_PROBE.json').write_bytes(Path('/tmp/retired_local_evaluation_probe_20261004.json').read_bytes());(P/'prepare_cleanup.py').write_bytes(Path(__file__).read_bytes());(P/'probe_cleanup.py').write_bytes(Path('/tmp/probe_retired_local_evaluations_20261004.py').read_bytes())
print(json.dumps(dict(prepared=True,files=len(files),GiB=plan['total_bytes']/1024**3,retained_files=len(retained),protected_spatial39_original160_raw_files=len(protected_raws),deletions_performed=False)))
