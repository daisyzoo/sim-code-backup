"""Explicit source version for final-load candidate; original numeric audits unchanged."""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rename(s):
    return (s.replace('audit_peak_guard','audit_instant_guard').replace('peak_guard_audit_context','instant_guard_audit_context').replace('verify_peak_guard_source','verify_instant_guard_source').replace('peak_guard_source_binding','instant_guard_source_binding').replace('staged_peak_load_guard','staged_instant_load_guard').replace('PEAK_GUARD_','INSTANT_GUARD_'))
rows=[]
for src in sorted(W.glob('audit_peak_guard*.py'))+[W/'peak_guard_audit_context.py']:
    if src.name=='audit_peak_guard_pressure.py':continue # Explicitly changed independent pressure mathematics.
    dst=W/rename(src.name);assert not dst.exists();text=rename(src.read_text());ast.parse(text);dst.write_text(text)
    rows.append(dict(parent=str(src),parent_sha256=sha(src),new=str(dst),new_sha256=sha(dst),numeric_math_unchanged=True,source_module_versioned=True))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,rows=rows,explicit_pressure_audit_separate=True,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'instant_guard_source_binding.py']},physical_validation=False,training_ready=False)
p=W/'INSTANT_GUARD_AUDIT_VERSION_CHECK.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print('VERSIONED',len(rows),'audit/context modules, original numeric math unchanged')
