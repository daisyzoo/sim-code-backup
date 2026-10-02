"""Version source bindings only, keeping every original numeric audit expression."""
from pathlib import Path
import json,hashlib,ast,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(W.glob('audit_box_inward*.py'))+[W/'box_inward_audit_context.py']
def rename(s):return s.replace('audit_box_inward','audit_substep').replace('box_inward_audit_context','substep_audit_context').replace('verify_box_inward_source','verify_substep_source').replace('staged_box_inward_correction','staged_substep_observer').replace('BOX_INWARD_','SUBSTEP_')
rows=[]
for src in files:
 dst=W/rename(src.name);assert not dst.exists();text=rename(src.read_text())
 if src.name=='audit_box_inward_source_contract.py':
  anchor='def verify_substep_source(ep):\n';assert text.count(anchor)==1
  addition=' from substep_source_binding import verify_observation_binding\n verify_observation_binding(ep)\n'
  text=text.replace(anchor,anchor+addition)
  assert ast.dump(ast.parse(text.replace(addition,'')))==ast.dump(ast.parse(rename(src.read_text())))
 else:assert ast.dump(ast.parse(text))==ast.dump(ast.parse(rename(src.read_text())))
 dst.write_text(text);rows.append(dict(parent=str(src),parent_sha256=sha(src),new=str(dst),new_sha256=sha(dst),numeric_math_unchanged=True,added_observer_binding=src.name=='audit_box_inward_source_contract.py'))
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'substep_source_binding.py']},physical_validation=False,training_ready=False)
p=W/'SUBSTEP_AUDIT_VERSION_CHECK.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print('PASS',len(rows),'versioned audits; numeric math unchanged; no launch')
