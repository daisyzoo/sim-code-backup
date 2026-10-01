"""Same nominal condition, new front-only flag absent on this rear route.
Quantify first differences; does not assign them to a particular simulator cause.
"""
from pathlib import Path
import json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;old=w/'self_clearance_groups_r1/case_840001';new=w/'front_direction_recontact_groups_r1/case_840001';name='layout_840001_push_box_to_bin';a=old/name;b=new/name;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();report={}
for case in [old,new]:
 plan=json.loads((case/name/'frontal_bypass.json').read_text())['plan'];assert not plan.get('front_route_selected') and not plan.get('front_direction_recontact')
argsa=json.loads((old/'provenance.json').read_text())['args'];argsb=json.loads((new/'provenance.json').read_text())['args'];argdiff={k:[argsa.get(k),argsb.get(k)] for k in set(argsa)|set(argsb) if argsa.get(k)!=argsb.get(k)}
with np.load(a/'raw.npz') as aa,np.load(b/'raw.npz') as bb:
 for key in ['q','action']:
  x=aa[key][:,12:23].astype(float);y=bb[key][:,12:23].astype(float);d=np.max(abs(x-y),axis=1);report[key]=dict(first_nonidentical=int(np.flatnonzero(d>0)[0]) if np.any(d>0) else None,first_above_rad={str(t):int(np.flatnonzero(d>t)[0]) if np.any(d>t) else None for t in [1e-7,1e-6,1e-4,.001,.01]},maximum_difference_rad=float(d.max()))
with np.load(a/'trace.npz') as aa,np.load(b/'trace.npz') as bb:
 for key in ['box','mailer','palm_left','palm_right']:
  d=np.linalg.norm(aa[key]-bb[key],axis=1);report[key]=dict(first_above_m={str(t):int(np.flatnonzero(d>t)[0]) if np.any(d>t) else None for t in [1e-7,1e-6,1e-4,.001,.01]},maximum_difference_m=float(d.max()),final_difference_m=float(d[-1]))
ra=json.loads((a/'frontal_bypass.json').read_text())['rows'];rb=json.loads((b/'frontal_bypass.json').read_text())['rows'];assert len(ra)==len(rb)==1199;mode_diff=[dict(step=x['step'],parent=x['mode'],new=y['mode']) for x,y in zip(ra,rb) if x['mode']!=y['mode']]
report['first_mode_difference']=mode_diff[0] if mode_diff else None;report['mode_differences']=len(mode_diff);report['argument_differences']=argdiff
pa=json.loads((old/'provenance.json').read_text())['source_sha256'];pb=json.loads((new/'provenance.json').read_text())['source_sha256'];common=[k for k in pa if k in pb];report['common_source_differences']=[k for k in common if pa[k]!=pb[k]];assert not report['common_source_differences']
report.update(scope=__doc__,source_sha256={str(p):sha(p) for p in [a/'raw.npz',b/'raw.npz',a/'trace.npz',b/'trace.npz',old/'runtime_configuration.json',new/'runtime_configuration.json',old/'runtime_randomization.json',new/'runtime_randomization.json',Path(__file__)]},training_ready=False)
(new.parent/'UNCHANGED_REAR_REPEATABILITY.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256']},indent=2))
