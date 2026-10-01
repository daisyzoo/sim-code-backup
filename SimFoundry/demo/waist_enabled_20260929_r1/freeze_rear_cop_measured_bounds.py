"""Verify and freeze the combined candidate; never launch physics."""
from pathlib import Path
import ast,json,hashlib
w=Path(__file__).resolve().parent;stage=w/'staged_rear_cop_measured_bounds';parent=w/'staged_region_measured_bounds';old=w/'staged_rear_cop_centering';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((parent/'MANIFEST.json').read_text());unchanged=[]
for n,h in m['source_sha256'].items():
 assert sha(parent/n)==h
 if n!='collect_paired_sorting.py':assert sha(stage/n)==h;unchanged.append(n)
for n in ['rear_cop_centering.py','rear_cop_route.py']:assert sha(stage/n)==sha(old/n)
checks=['PRELAUNCH_AND_SOURCE_CHECK.json','COLLECTOR_WIRING_CHECK.json','MEASURED_BOUNDS_WIRING_CHECK.json','BOUNDARY_WIRING_CHECK.json','LIFECYCLE_CHECK.json','AUDITOR_CHECK.json']
for n in checks:
 d=json.loads((stage/n).read_text());assert d.get('passed',d.get('default_off_and_enabled_cli',False))
 for field in ['source_sha256','candidate_source_sha256']:
  for path,h in d.get(field,{}).items():
   base=Path(d['episode']) if n=='BOUNDARY_WIRING_CHECK.json' and field=='source_sha256' else stage
   p=Path(path) if Path(path).is_absolute() else base/path
   assert sha(p)==h,(n,path)
 assert d.get('checker_sha256') is None or any(sha(p)==d['checker_sha256'] for p in w.glob('check_rear_cop_measured*.py'))
pre=json.loads((stage/checks[0]).read_text());life=json.loads((stage/'LIFECYCLE_CHECK.json').read_text());aud=json.loads((stage/'AUDITOR_CHECK.json').read_text());assert pre['actual_snapshot_writer_files']==55 and life['total_default_exact_frames']==9592 and len(aud['rows'])==8
for row in aud['rows']:
 ep=w/row['run']/('case_'+row['episode'].split('_')[1])/row['episode']
 for n,h in row['source_sha256'].items():assert sha(ep/n)==h
newaudit=w/'audit_rear_cop_measured_bounds_live.py';oldaudit=w/'audit_rear_cop_centering_live.py'
get=lambda p:next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='reconstruct')
assert ast.dump(get(newaudit))==ast.dump(get(oldaudit));assert "w/'audit_region_measured_bounds_live.py'" in newaudit.read_text();assert "'MEASURED_BOUNDS_LIVE_AUDIT.json'" in newaudit.read_text();assert aud['auditor_sha256']==sha(newaudit) and aud['helper_sha256']==sha(stage/'rear_cop_centering.py')
oldchecks={}
for n in ['CHECK.json','LIFECYCLE_CHECK.json']:
 p=old/n;d=json.loads(p.read_text());assert d['passed'];oldchecks[str(p.resolve())]=sha(p)
report=dict(passed=True,unchanged_parent_helpers=unchanged,unchanged_cop_helpers=['rear_cop_centering.py','rear_cop_route.py'],rear_reconstruction_AST_unchanged=True,measured_audit_required_before_rear_audit=True,old_unchanged_helper_checks_inherited=oldchecks,source_sha256={n:sha(stage/n) for n in [*m['source_sha256'],'rear_cop_centering.py','rear_cop_route.py']},auditor_sha256=sha(newaudit),measured_auditor_sha256=sha(w/'audit_region_measured_bounds_live.py'),physical_started=False,training_ready=False)
assert not (stage/'MANIFEST.json').exists();(stage/'COMPOSITION_CHECK.json').write_text(json.dumps(report,indent=2));checks.append('COMPOSITION_CHECK.json')
manifest=dict(source_sha256=report['source_sha256'],checks_sha256={n:sha(stage/n) for n in checks},parent_manifest_sha256=sha(parent/'MANIFEST.json'),auditor_sha256=sha(newaudit),measured_auditor_sha256=report['measured_auditor_sha256'],collector_wired=True,physical_started=False,training_ready=False,scope='Measured-bounds parent plus one rear-COP flag. Eight parent helpers and two prior COP helpers byte-identical. New composition CLI,55archives,8selection34packet fixtures,28action fixtures16negative,3boundary fixtures18negative,8stream9592default frames896one-step overrides3guards,8stream independent896synthetic overrides238corruptions. No new physics, success, or data admission. Release-margin candidate excluded.')
(stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print('candidate_frozen',sha(stage/'MANIFEST.json'),'CLI negatives',len(pre['negative_cli_rejected']))
