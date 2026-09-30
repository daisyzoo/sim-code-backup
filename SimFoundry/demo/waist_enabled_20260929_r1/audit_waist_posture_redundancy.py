"""Static minimum-yaw feasibility to investigate recovering visual coverage."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
rng=np.random.default_rng(931);rows=[]
for target in [[.52,.30,.84],[.50,.30,.84],[.52,.30,.92],[.55,.23,.84]]:
 target=np.array(target)
 def residual(q):
  d=dict(zip(names,q));return np.r_[palm('left',d)-target,palm('right',d)-anchor,.001*q[0]]
 best=None
 for q in [initial,np.zeros(11),*rng.uniform(lo,hi,(5,11))]:
  fit=least_squares(residual,np.clip(q,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=300);v=float(np.linalg.norm(fit.fun))
  if best is None or v<best['weighted_residual']:best=dict(weighted_residual=v,waist_rad=float(fit.x[0]),both_palms_error_m=float(np.linalg.norm(fit.fun[:6])),q=fit.x.tolist())
 rows.append(dict(target=target.tolist(),best=best))
report=dict(rows=rows,scope='Offline multistart six palm-position constraints plus weak .001 waist-home cost. No collision, camera occlusion or dynamics. Found low-residual postures are existence candidates, not executable paths; nonzero residual does not prove infeasibility.',training_ready=False)
(root/'WAIST_POSTURE_REDUNDANCY_AUDIT.json').write_text(json.dumps(report,indent=2))
for r in rows:print(r['target'],r['best']['waist_rad'],r['best']['both_palms_error_m'])
