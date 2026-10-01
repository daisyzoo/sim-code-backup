from pathlib import Path
import sys,json,copy,hashlib,ast
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sys.path[:0]=[str(w),str(w/'staged_contact_bout_yaw'),str(w.parents[1])]
from audit_contact_bout_yaw_live import audit
from contact_bout_yaw import ContactBoutYaw,contact_bout_yaw_constraint
s=(w/'screen_rear_top_contact_reach.py').read_text();exec(compile(s.split("run=root/'current_lateral_profile_r1'")[0],'<validated_fk_jac>','exec'))
ep=w/'y_path_nearhalf_groups_r1/case_897003/layout_897003_nudge_mailer_to_bin';real=audit(ep);assert real['passed'] and real['active_frames']==0
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
rows=json.loads((ep/'coordination.json').read_text());ctrl={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};state=ContactBoutYaw()
for row in rows:
 t=row['step'];m,jl,jw=fk('left',q[t]);a=state.update(ctrl[t]['mode'],m[:3,:3]);record=contact_bout_yaw_constraint(m[:3,:3],jw,a) if a else None;row['contact_bout_yaw_tracking']={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in record.items()} if record else None
positive=audit(ep,rows_override=rows,enabled_override=True);assert positive['passed'],positive['errors'][:3]
mutations=[]
for kind in ['anchor','error','jacobian','missing','nonfinite','stale_release']:
 bad=copy.deepcopy(rows);i=next(i for i,r in enumerate(bad) if r['contact_bout_yaw_tracking'] is not None and r['step']%20==0);v=bad[i]['contact_bout_yaw_tracking']
 if kind=='anchor':v['target_heading_rad']+=.01
 elif kind=='error':v['error'][0]+=.001
 elif kind=='jacobian':v['jacobian'][0][0]+=.01
 elif kind=='missing':bad[i]['contact_bout_yaw_tracking']=None
 elif kind=='nonfinite':v['error'][0]=float('nan')
 elif kind=='stale_release':next(r for r in bad if ctrl[r['step']]['mode']=='initial_top_guard_lift')['contact_bout_yaw_tracking']=copy.deepcopy(v)
 r=audit(ep,rows_override=bad,enabled_override=True);assert not r['passed'],kind;mutations.append(dict(case=kind,rejected=True))
report=dict(passed=True,real_off_passed=True,synthetic_on_active_frames=positive['active_frames'],synthetic_on_max_jacobian_error=positive['max_jacobian_error'],negative_fixtures=mutations,scope='Real disabled trajectory and labelled counterfactual records generated from actual q/analytic Jacobians; no enabled physical trajectory yet.',training_ready=False)
(w/'staged_contact_bout_yaw/AUDITOR_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
