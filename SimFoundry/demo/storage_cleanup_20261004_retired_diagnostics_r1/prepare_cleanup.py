from pathlib import Path
import json,hashlib,datetime
ROOT=Path('/home/user/Documents/zoo/sim/SimFoundry');W=ROOT/'demo/waist_enabled_20260929_r1';P=ROOT/'demo/storage_cleanup_20261004_retired_diagnostics_r1'
P.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
probe=json.loads(Path('/tmp/retired_early_diagnostics_probe_20261004.json').read_text())
names={'matched_expert_diagnosis_20260929_r1','rotated_variation_20260928_r1','rotated_offset12_20260928_r1','shared_preparation_variation_20260928_r1','relative_contact_diagnosis_20260929_r1'}
selected=[r for r in probe['candidates'] if Path(r['root']).name in names];assert len(selected)==5
files=[];retained={};evidence={};refs=[]
for row in selected:
 root=Path(row['root']);status=json.loads((root/'STATUS.json').read_text());assert status['stage'].startswith('complete_reviewed') and status['training_ready'] is False
 assert not row['direct_protected_files'];evidence[str(root)]=status
 for ref in row['references']:
  assert Path(ref)==W/'REAR_TRANSPORT_RETRY_ALL_DEMO_SNAPSHOT_INVENTORY.json'
  inv=json.loads(Path(ref).read_text());matches=[f['path'] for g in inv['groups'] for f in g['files'] if f['path'].startswith(str(root)+'/')]
  assert matches and all('/source_snapshot/' in p and not p.endswith('/raw.npz') for p in matches)
  refs.append(dict(reference=ref,matched_paths=matches,disposition='Only preserved source_snapshot files; no raw dependency.'))
 raw=set(row['files'])
 for p in root.rglob('*'):
  if not p.is_file() or p.is_symlink():continue
  if str(p) in raw:
   st=p.stat();assert p.name=='raw.npz' and st.st_nlink==1
   files.append(dict(path=str(p),bytes=st.st_size,sha256=sha(p),device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
  else:retained[str(p)]=sha(p)
assert len(files)==58
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_deleted',authorization='User authorized deletion of unrelated historical test/intermediate data. Five completed unadmitted legacy diagnostic runs; no current raw dependency.',roots=[r['root'] for r in selected],files=files,total_bytes=sum(f['bytes'] for f in files),retained_sha256=retained,evidence=evidence,reference_classification=refs,protected_sources=probe['protected_sources'],text_sources_scanned=probe['text_sources_scanned'],protected_owner_sha256={p:sha(p) for p in probe['owners']},scope='Only raw.npz in five completed legacy diagnostics. Preserve reports, traces, review images, source snapshots. Full RGB/raw replay will become unavailable. No current runs, admitted training data, models, or retained independent baselines removed.')
(P/'PLAN.json').write_text(json.dumps(plan,indent=2));(P/'REFERENCE_PROBE.json').write_bytes(Path('/tmp/retired_early_diagnostics_probe_20261004.json').read_bytes());(P/'prepare_cleanup.py').write_bytes(Path(__file__).read_bytes());(P/'probe_cleanup.py').write_bytes(Path('/tmp/probe_retired_early_diagnostics_20261004.py').read_bytes())
old=(ROOT/'demo/storage_cleanup_20261004_retired_relative10_evaluation_r1/apply_cleanup.py').read_text()
s=old.replace('storage_cleanup_20261004_retired_relative10_evaluation_r1','storage_cleanup_20261004_retired_diagnostics_r1')
a=s.index('for root in roots:\n');b=s.index('\nresult=dict(',a)
s=s[:a]+'''for root in roots:
 count=sum(Path(r['path']).is_relative_to(Path(root)) for r in plan['files'])
 with (Path(root)/'RAW_RGB_REMOVED_20261004.md').open('x') as f:f.write(f'按用户清理历史测试数据授权，本目录移除{count}个已结束、未准入训练的旧诊断raw.npz。保留所有其他文件，包括报告、轨迹、复核图片和source_snapshot；原审核结论不变。完整RGB及原始数组不可再重放，不得作为完整训练数据。清单与检查见demo/storage_cleanup_20261004_retired_diagnostics_r1/PLAN.json及RESULT.json。\\n')
''' +s[b:]
s=s.replace("preserved_research_baseline_stats=plan['reference_classification']['preserved_stats_path'],",'')
compile(s,str(P/'apply_cleanup.py'),'exec');(P/'apply_cleanup.py').write_text(s)
print(json.dumps(dict(prepared=True,files=len(files),GiB=plan['total_bytes']/1024**3,retained_files=len(retained))))
