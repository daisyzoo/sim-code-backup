"""Original stability checks with independently verified margin confirmation formula.
No old failures overwritten. New native source and complete trace checks required.
"""
from pathlib import Path
import sys,json,hashlib
from audit_terminal_margin_contact_stability_supplement import audit_files
from audit_rear_trailing_r1_v1_stage_release import verify_files
from rear_trailing_stage_source_binding_v1 import verify_observation_binding

def audit(ep):
 ep=Path(ep).resolve();source=verify_observation_binding(ep);release=verify_files(ep,enabled=True);assert not release['wait'];out=audit_files(ep,margin_enabled=True);out.update(source_binding=source,independent_release_audit=release,auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),arithmetic_source_sha256=hashlib.sha256((Path(__file__).parent/'audit_terminal_margin_contact_stability_supplement.py').read_bytes()).hexdigest());return out
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=audit(ep);(ep/'REAR_TRAILING_R1_V1_STAGE_STABILITY_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:out[k] for k in ['control_checks_passed','errors','release']}));sys.exit(0 if out['control_checks_passed'] else 1)
