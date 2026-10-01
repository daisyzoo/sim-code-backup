"""Independent URDF/lifecycle/finite-difference audit of contact-bout heading."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
src=(root/'audit_terminal_reach.py').read_text();exec(compile(src.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))

def audit(p, *, rows_override=None, enabled_override=None):
 p=Path(p);args=json.loads((p.parent/'provenance.json').read_text())['args'];enabled=args.get('expert_top_contact_bout_yaw_hold',False) if enabled_override is None else enabled_override
 with np.load(p/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
 ctrl={r['step']:r for r in json.loads((p/'expert_control.json').read_text())};rows=json.loads((p/'coordination.json').read_text()) if rows_override is None else rows_override;top=json.loads((p/'frontal_bypass.json').read_text())['rows'];topsteps={r['step'] for r in top};side='right' if 'push_box' in p.name else 'left'
 def rotation(v):
  r=np.eye(3)
  for name,origin,axis in chains[side]:
   r=r@origin[:3,:3]
   if axis is not None:r=r@Rotation.from_rotvec(axis*(v[names.index(name)] if name in names else 0.)).as_matrix()
  return r
 def heading(v,axis):
  r=rotation(v);return math.atan2(r[1,axis],r[0,axis])
 wrap=lambda x:math.atan2(math.sin(x),math.cos(x))
 assert [r['step'] for r in rows]==list(range(1,len(q)))
 axis=None;anchor=None;errors=[];records=[];jac_errors=[]
 for row in rows:
  t=row['step'];expected=bool(enabled and t in topsteps and ctrl[t]['mode']=='top_push');actual=row.get('contact_bout_yaw_tracking')
  if not expected:axis=anchor=None
  elif axis is None:
   r=rotation(q[t]);axis=int(np.argmax(np.sum(r[:2,:]**2,axis=0)));anchor=heading(q[t],axis)
  if (actual is not None)!=expected:errors.append([t,'activation']);continue
  if actual is None:continue
  if type(actual.get('axis')) is not int or actual['axis']!=axis:errors.append([t,'axis']);continue
  try:finite=all(np.isfinite(np.asarray(actual[k],float)).all() for k in ['target_heading_rad','current_heading_rad','heading_error_rad','horizontal_axis_norm_sq','weight_m','error','jacobian'])
  except (ValueError,KeyError,TypeError):finite=False
  if not finite:errors.append([t,'nonfinite_or_missing']);continue
  current=heading(q[t],axis);delta=wrap(anchor-current);r=rotation(q[t]);den=float(np.sum(r[:2,axis]**2));correction=.15*np.clip(.72*delta,-.1,.1)
  if np.asarray(actual['jacobian']).shape!=(1,11) or np.asarray(actual['error']).shape!=(1,):errors.append([t,'shape']);continue
  gap=max(abs(wrap(actual['target_heading_rad']-anchor)),abs(wrap(actual['current_heading_rad']-current)),abs(wrap(actual['heading_error_rad']-delta)),abs(den-actual['horizontal_axis_norm_sq']),abs(correction-actual['error'][0]))
  if gap>2e-6 or actual['weight_m']!=.15:errors.append([t,'anchor_heading_or_error'])
  records.append(dict(step=t,error_rad=delta,mapping_error=gap))
  if t%20==0:
   eps=1e-6;fd=[]
   for j in range(11):
    d=np.zeros(11);d[j]=eps;fd.append(.15*wrap(heading(q[t]+d,axis)-heading(q[t]-d,axis))/(2*eps))
   err=float(np.max(abs(np.asarray(fd)-actual['jacobian'][0])));jac_errors.append(dict(step=t,error=err))
   if err>2e-6:errors.append([t,'jacobian'])
 return dict(passed=not errors,enabled=bool(enabled),checked_frames=len(rows),active_frames=len(records),jacobian_samples=len(jac_errors),max_jacobian_error=max((r['error'] for r in jac_errors),default=None),max_abs_heading_error_rad=max((abs(r['error_rad']) for r in records),default=None),errors=errors,records=records,source_sha256={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['raw.npz','coordination.json','expert_control.json','frontal_bypass.json']},scope='Independent URDF rotation/lifecycle/finite differences; no control-helper import. Heading residual is diagnostic, not an extra task gate or proof of contact quality. Overrides are for explicitly labelled fixture tests only.',training_ready=False)

if __name__=='__main__':
 p=Path(sys.argv[1]);r=audit(p);r['auditor_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();(p/'CONTACT_BOUT_YAW_LIVE_AUDIT.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['records','source_sha256']},indent=2));assert r['passed'],r['errors'][:10]
