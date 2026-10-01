"""Independent auditor must detect corrupted X commands, anchors and transitions."""
from pathlib import Path
import copy,json,hashlib
import numpy as np
from audit_region_x_follow_live import reconstruct
w=Path(__file__).resolve().parent
rows=[dict(step=t,mode=m,target_xyz=[x,0.,.79],push_x_anchor_m=a) for t,m,x,a in [(0,'top_press',.5,None),(1,'top_push',.5,.5),(2,'top_push',.502,.5),(3,'top_push',.504,.5),(4,'top_lift',.51,.5),(5,'top_press',.52,.5),(6,'top_push',.52,.52)]]
target=np.array([[1.,0.,.77],[1.,0.,.77],[1.004,0.,.77],[1.007,0.,.77],[1.01,0.,.77],[1.015,0.,.77],[1.015,0.,.77]])
r,e=reconstruct(rows,target,-1);assert len(r)==4 and not e
checks=[]
for kind in ['wrong_command','wrong_anchor','wrong_target','missing_previous','unconfirmed_push','stale_recontact_anchor']:
 rr=copy.deepcopy(rows);tr=target.copy()
 if kind=='wrong_command':rr[2]['target_xyz'][0]+=.001
 elif kind=='wrong_anchor':rr[2]['push_x_anchor_m']+=.005
 elif kind=='wrong_target':tr[2,0]-=.010
 elif kind=='missing_previous':rr=rr[1:]
 elif kind=='unconfirmed_push':rr[0]['mode']='top_descend'
 else:rr[6]['push_x_anchor_m']=.5
 _,errors=reconstruct(rr,tr,-1);assert errors,kind;checks.append(kind)
out=dict(passed=True,valid_bouts=2,valid_push_frames=4,corruptions_rejected=checks,scope='Synthetic log fixtures only; independent audit integrity, not physical execution.',auditor_sha256=hashlib.sha256((w/'audit_region_x_follow_live.py').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(w/'staged_region_contact_x_follow/X_FOLLOW_AUDITOR_CHECK.json').write_text(json.dumps(out,indent=2));print(out)
