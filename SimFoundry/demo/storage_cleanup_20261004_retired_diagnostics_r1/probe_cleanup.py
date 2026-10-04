from pathlib import Path
import json,datetime
ROOT=Path('/home/user/Documents/zoo/sim/SimFoundry');W=ROOT/'demo/waist_enabled_20260929_r1'
old=json.loads(Path('/tmp/retired_rejected_raw_probe_20261004.json').read_text());owners=[Path(x) for x in old['owners']]
owners += [W/'front_box_trailing_physical_r2/PROTOCOL.json',W/'front_loaded_z_quarter_physical_preparation_r2/LAUNCH_QUEUE_PLAN.json',W/'front_box_trailing_physical_r1/PROTOCOL.json',W/'front_loaded_z_quarter_physical_preparation_r1/CONFIGURATION_CHECK.json',W/'front_loaded_z_quarter_physical_preparation_r1/LAUNCH_QUEUE_PLAN.json',W/'front_loaded_z_quarter_physical_preparation_r1/READINESS_CONTINUATION_PLAN.json']
protected=set()
def walk(d):
 if isinstance(d,dict):
  for k,v in d.items():
   if k.startswith('/') and Path(k).is_file():protected.add(k)
   walk(v)
 elif isinstance(d,list):
  for v in d:walk(v)
 elif isinstance(d,str) and d.startswith('/') and Path(d).is_file():protected.add(d)
for p in owners:walk(json.loads(p.read_text()));protected.add(str(p))
texts={p for p in protected if Path(p).suffix in {'.py','.json','.md','.sh','.yaml','.toml'} and Path(p).stat().st_size<20*1024**2}
texts.update(str(p) for ext in ['*.py','*.json'] for p in W.glob(ext))
owners += [W/'rear_early_edge_physical_preparation_r1/PLAN.json',W/'rear_early_edge_preparation_r1/STAGE_PREPARATION.json',W/'rear_early_edge_preparation_r1/AUDIT_FAMILY_PREPARATION.json']
for p in owners[-3:]:walk(json.loads(p.read_text()));protected.add(str(p))
texts.update(str(p) for p in protected if Path(p).suffix in {'.py','.json','.md','.sh','.yaml','.toml'} and Path(p).stat().st_size<20*1024**2)
candidates=[ROOT/'demo'/n for n in ['paired_zero_pilot32_20260924_r1','paired_zero_push24_release_20260924_r1','matched_expert_diagnosis_20260929_r1','rotated_variation_20260928_r1','rotated_offset12_20260928_r1','distance_offset_20260928_r1','shared_preparation_variation_20260928_r1','push_recovery_feasibility_20260928_r1','relative_contact_diagnosis_20260929_r1']]
rows=[]
for root in candidates:
 fs=list(root.rglob('raw.npz'));rows.append(dict(root=str(root),files=[str(p) for p in fs],bytes=sum(p.stat().st_size for p in fs),direct_protected_files=[str(p) for p in fs if str(p) in protected],references=[]))
for t in sorted(texts):
 try:data=Path(t).read_text()
 except (UnicodeDecodeError,FileNotFoundError):continue
 for r in rows:
  root=Path(r['root']);needles=[str(root),str(root.relative_to(ROOT)),root.name]
  if any(x in data for x in needles):r['references'].append(t)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),owners=[str(p) for p in owners],protected_sources=len(protected),text_sources_scanned=len(texts),candidates=rows,deletions_performed=False)
Path('/tmp/retired_early_diagnostics_probe_20261004.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(protected=len(protected),texts=len(texts),candidates=[dict(root=r['root'],files=len(r['files']),GiB=r['bytes']/1024**3,protected=len(r['direct_protected_files']),reference_count=len(r['references']),reference_examples=r['references'][:4]) for r in rows]),indent=2))
