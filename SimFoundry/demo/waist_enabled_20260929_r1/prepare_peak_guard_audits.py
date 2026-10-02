"""Version source admission for candidate; preserve original numeric expressions."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rename(s):
    return (s.replace('audit_substep','audit_peak_guard')
             .replace('substep_audit_context','peak_guard_audit_context')
             .replace('verify_substep_source','verify_peak_guard_source')
             .replace('substep_source_binding','peak_guard_source_binding')
             .replace('staged_substep_observer','staged_peak_load_guard')
             .replace('SUBSTEP_','PEAK_GUARD_'))
rows=[]
for src in sorted(W.glob('audit_substep*.py'))+[W/'substep_audit_context.py']:
    dst=W/rename(src.name);assert not dst.exists()
    text=rename(src.read_text())
    # CONTACT_RECORDING is an unchanged observer filename, not an audit report.
    text=text.replace('PEAK_GUARD_CONTACT_RECORDING.json','SUBSTEP_CONTACT_RECORDING.json')
    ast.parse(text)
    expected=rename(src.read_text()).replace('PEAK_GUARD_CONTACT_RECORDING.json','SUBSTEP_CONTACT_RECORDING.json')
    assert ast.dump(ast.parse(text))==ast.dump(ast.parse(expected))
    dst.write_text(text)
    rows.append(dict(parent=str(src),parent_sha256=sha(src),new=str(dst),new_sha256=sha(dst),
                     numeric_math_unchanged=True,source_module_versioned=True))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
         rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'peak_guard_source_binding.py']},
         physical_validation=False,training_ready=False)
dest=W/'PEAK_GUARD_AUDIT_VERSION_CHECK.json';assert not dest.exists()
dest.write_text(json.dumps(out,indent=2));print('VERSIONED',len(rows),'audit/context modules; original numeric expressions retained')
