"""Isolate measured-state bounds from unchanged command/prediction bounds."""
from pathlib import Path
import ast,hashlib,json
w=Path(__file__).resolve().parent;src=w/'staged_region_causal_xy_diagnostics/contact_patch_approach.py';dst=w/'staged_measured_bounds_probe';dst.mkdir(exist_ok=False)
s=src.read_text();old='command_change_damping=False, response_centered_xy_objective=False):';assert s.count(old)==1
s=s.replace(old,'command_change_damping=False, response_centered_xy_objective=False, measured_lower=None, measured_upper=None):')
needle='    if np.any(q<lower-1e-6) or np.any(q>upper+1e-6):raise ValueError('
assert s.count(needle)==1
validation='''    state_lower, state_upper = lower, upper
    if measured_lower is not None or measured_upper is not None:
        if measured_lower is None or measured_upper is None:
            raise ValueError('Both measured-state bounds required')
        state_lower, state_upper = np.asarray(measured_lower,dtype=float), np.asarray(measured_upper,dtype=float)
        if state_lower.shape!=(11,) or state_upper.shape!=(11,) or not np.isfinite(state_lower).all() or not np.isfinite(state_upper).all():
            raise ValueError('Invalid measured-state bounds')
        if np.any(state_lower>=state_upper) or np.any(state_lower>lower) or np.any(state_upper<upper):
            raise ValueError('Measured-state domain must contain the command domain')
    in_command_bounds=bool(np.all(q>=lower-1e-6) and np.all(q<=upper+1e-6))
'''
s=s.replace(needle,validation+'    if np.any(q<state_lower-1e-6) or np.any(q>state_upper+1e-6):raise ValueError(')
# Diagnostic must identify the actual failing domain, retaining planning bounds.
old='lower=lower.tolist(),upper=upper.tolist(),violating_indices=np.flatnonzero((q<lower-1e-6)|(q>upper+1e-6)).tolist()';assert s.count(old)==1
s=s.replace(old,'lower=state_lower.tolist(),upper=state_upper.tolist(),command_lower=lower.tolist(),command_upper=upper.tolist(),violating_indices=np.flatnonzero((q<state_lower-1e-6)|(q>state_upper+1e-6)).tolist()')
old='if .003<=height<=.005 and inactive_error<.002 and interior:return';assert s.count(old)==1
s=s.replace(old,'if .003<=height<=.005 and inactive_error<.002 and interior and in_command_bounds:return')
p=dst/src.name;p.write_text(s);ast.parse(s);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(dst/'PREPARATION.json').write_text(json.dumps(dict(parent_source_sha256=sha(src),candidate_sha256=sha(p),collector_wired=False,physical_started=False,training_ready=False,scope='Optional explicit measured domain; default same command domain. Nominal and affine command bounds, slew, geometry, goals unchanged. Measured-q handover still requires original planning bounds. Not tested/installed at preparation.'),indent=2));print(dst)
