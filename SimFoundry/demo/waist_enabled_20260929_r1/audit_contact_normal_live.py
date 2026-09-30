"""Independent URDF finite-difference audit of optional recorded top normal task."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
src=(root/'audit_terminal_reach.py').read_text()
exec(compile(src.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
p=Path(sys.argv[1]).resolve()
args=json.loads((p.parent/'provenance.json').read_text())['args']
enabled=args.get('expert_top_contact_normal_hold',False)
with np.load(p/'raw.npz') as z:q=z['q'][:,12:23].copy()
control={r['step']:r for r in json.loads((p/'expert_control.json').read_text())}
rows=json.loads((p/'coordination.json').read_text())
top=json.loads((p/'frontal_bypass.json').read_text())['rows'] if (p/'frontal_bypass.json').exists() else []
topsteps={r['step'] for r in top}
side='right' if 'push_box' in p.name else 'left'
def rotation(v):
    r=np.eye(3)
    for name,origin,axis in chains[side]:
        r=r@origin[:3,:3]
        if axis is not None:r=r@Rotation.from_rotvec(axis*(v[names.index(name)] if name in names else 0.)).as_matrix()
    return r
def normal(v):return rotation(v).T@np.array([0.,0.,1.])
anchor=None;errors=[];records=[];jac_errors=[]
assert [r['step'] for r in rows]==list(range(1,len(q)))
for row in rows:
    t=row['step'];mode=control[t]['mode'];current=normal(q[t])
    if enabled and t in topsteps and anchor is None and mode in ('top_press','top_push'):anchor=current.copy()
    expected=enabled and t in topsteps and anchor is not None and mode in ('top_lift','top_cross','top_descend','top_press','top_push')
    actual=row.get('contact_normal_tracking')
    if (actual is not None)!=bool(expected):errors.append([t,'activation']);continue
    if actual is None:continue
    if not all(np.isfinite(np.asarray(actual[k],dtype=float)).all() for k in ('current_local_up','target_local_up','error','jacobian','angle_error_rad','weight_m')):
        errors.append([t,'nonfinite_normal_record']);continue
    angle=float(np.arccos(np.clip(current@anchor,-1,1)))
    gap=max(float(np.max(abs(current-actual['current_local_up']))),float(np.max(abs(anchor-actual['target_local_up']))))
    correction=.15*np.clip(.72*(anchor-current),-.1,.1)
    # Isaac float32-derived rotations can have tiny non-unit column lengths.
    # acos(dot(u,u)) then reports a small angle even when u is its own anchor.
    # Vectors/correction remain independently checked above; verify the logged
    # raw-angle formula exactly, and report the independent URDF angle separately.
    logged_current=np.asarray(actual['current_local_up']);logged_anchor=np.asarray(actual['target_local_up'])
    raw_angle=float(np.arccos(np.clip(logged_current@logged_anchor,-1,1)))
    angle_formula_error=abs(raw_angle-actual['angle_error_rad'])
    if gap>2e-6 or np.max(abs(correction-actual['error']))>2e-6 or angle_formula_error>1e-9 or actual['weight_m']!=.15:errors.append([t,'normal_or_error'])
    records.append(dict(step=t,mode=mode,angle_error_rad=angle,normal_record_error=gap,logged_raw_angle_rad=actual['angle_error_rad'],raw_angle_formula_error_rad=angle_formula_error,logged_current_norm=float(np.linalg.norm(logged_current)),logged_anchor_norm=float(np.linalg.norm(logged_anchor))))
    if t%20==0:
        fd=np.empty((3,11));eps=1e-6
        for j in range(11):
            delta=np.zeros(11);delta[j]=eps
            fd[:,j]=.15*(normal(q[t]+delta)-normal(q[t]-delta))/(2*eps)
        error=float(np.max(abs(fd-actual['jacobian'])));jac_errors.append(dict(step=t,max_error=error))
        if error>2e-6:errors.append([t,'jacobian'])
summary=dict(enabled=enabled,checked_frames=len(rows),active_frames=len(records),jacobian_samples=len(jac_errors),max_jacobian_error=max((r['max_error'] for r in jac_errors),default=None),max_normal_error_deg=float(np.degrees(max((r['angle_error_rad'] for r in records),default=0))),recording_and_mapping_passed=not errors)
files=['raw.npz','expert_control.json','coordination.json'];files+=['frontal_bypass.json'] if top else []
out=dict(auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),summary=summary,errors=errors,records=records,jacobians=jac_errors,source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in files},scope='Independent URDF rotation and finite differences, actual lifecycle/anchor and recorded constraint checked without importing control helper. Angular residual is reported, not a new original task gate. No proof of force/COP stability, collision freedom, visibility or model quality.',training_ready=False)
(p/'CONTACT_NORMAL_LIVE_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
assert not errors,errors[:10]
