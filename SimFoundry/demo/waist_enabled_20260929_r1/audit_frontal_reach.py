"""Static multi-start reach diagnosis; candidate poses must not be executed directly."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
rng=np.random.default_rng(932);rows=[]
for side,task in [('left','nudge_mailer_to_bin'),('right','push_box_to_bin')]:
 ep=root/'frontal_bypass_smoke_r1/case_62000'/f'layout_62000_{task}'
 with np.load(ep/'raw.npz') as z:initial=z['q'][-1,12:23].copy()
 j=json.loads((ep/'frontal_bypass.json').read_text());anchor=np.array(j['plan']['inactive_anchor_override']['xyz']);other='right' if side=='left' else 'left'
 y=j['plan']['initial_target_xyz'][1]
 for target in [[.54,y,.81],[.54,y,.84],[.54,y,.88],[.54,y*.5,.81]]:
  target=np.array(target)
  def residual(q):
   d=dict(zip(names,q));return np.r_[palm(side,d)-target,palm(other,d)-anchor]
  best=None
  for q in [initial,np.zeros(11),*rng.uniform(lo,hi,(4,11))]:
   fit=least_squares(residual,np.clip(q,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=200);v=float(np.linalg.norm(fit.fun))
   if best is None or v<best['error_m']:best=dict(error_m=v,active_error_m=float(np.linalg.norm(fit.fun[:3])),waist_rad=float(fit.x[0]),q=fit.x.tolist())
  rows.append(dict(side=side,target=target.tolist(),best=best));print(side,target,best['error_m'],flush=True)
(root/'FRONTAL_REACH_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Static position-only bounded multistart FK; no dynamics/orientation/collision feasibility guarantee. Residual does not prove global impossibility. Do not directly execute joint solutions.',training_ready=False),indent=2))
