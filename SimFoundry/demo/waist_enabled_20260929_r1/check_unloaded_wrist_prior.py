"""Guard and unchanged-component checks for the uninstalled wrist preference."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;stage=w/'staged_unloaded_wrist_prior_probe';sys.path.insert(0,str(stage))
from unloaded_wrist_prior import wrist_prior
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();q=np.zeros(11);q[5]=-.7;q[10]=1.4;prior=np.zeros(11);prior[0]=.003;cfg=dict(enabled=True,selected=True,side='right',mode='top_cross',recontacts=1,observed_load_n=0.,filtered_load_n=.01,min_hand_z_m=.85);checks=[]
for side,wi in [('left',5),('right',10)]:
 out,meta=wrist_prior(q,prior,**dict(cfg,side=side));assert meta['eligible'] and out[wi]==np.clip(-.15*q[wi],-.04,.04) and np.array_equal(np.delete(out,wi),np.delete(prior,wi));checks.append(dict(case=side,passed=True))
for key,value in [('enabled',False),('selected',False),('mode','top_push'),('mode','top_press'),('mode','top_descend'),('mode','top_release'),('mode','rear_push'),('mode','wait_no_package'),('recontacts',0),('observed_load_n',.001),('observed_load_n',-1.),('filtered_load_n',.05001),('filtered_load_n',-.001),('min_hand_z_m',.839999)]:
 out,meta=wrist_prior(q,prior,**dict(cfg,**{key:value}));assert not meta['eligible'] and np.array_equal(out,prior);checks.append(dict(case=f'{key}={value}',passed=True))
for key,value in [('enabled',1),('selected',1),('side','both'),('recontacts',-1),('filtered_load_n',float('nan'))]:
 rejected=False
 try:wrist_prior(q,prior,**dict(cfg,**{key:value}))
 except ValueError:rejected=True
 assert rejected;checks.append(dict(case=f'invalid_{key}',passed=True))
assert prior[5]==prior[10]==0
report=dict(passed=True,checks=checks,scope=__doc__,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'unloaded_wrist_prior.py']},collector_integrated=False,training_ready=False)
(stage/'GUARD_CHECK.json').write_text(json.dumps(report,indent=2));print('passed',len(checks),'cases')
