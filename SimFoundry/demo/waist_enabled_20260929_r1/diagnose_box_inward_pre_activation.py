"""Compare same-layout runs before first actually overridden inward command.
Different trajectories before activation prevent attributing the complete score
change solely to the new constraint. This does not identify the numerical cause,
prove stochasticity, or substitute a repeated identical-source physical control.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;r=w/'box_inward_groups_r1';old=w/'box_entry_lift_groups_r1';cases=[old/'case_840001',r/'case_840001'];eps=[c/'layout_840001_push_box_to_bin' for c in cases];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sources=[Path(__file__)];comp={}
coords=json.loads((eps[1]/'coordination.json').read_text());active=[c['step'] for c in coords if c.get('joint_edge_refinement',{}).get('override')];assert active and len(active)==53;first=min(active)
for name in ['runtime_randomization.json','runtime_configuration.json','explicit_layout.json']:
 values=[json.loads((c/name).read_text()) for c in cases];assert values[0]==values[1],name;comp[name]='identical';sources.extend(c/name for c in cases)
with np.load(cases[0]/'runtime_collision_arrays.npz') as a,np.load(cases[1]/'runtime_collision_arrays.npz') as b:
 assert set(a.files)==set(b.files)
 for k in a.files:
  assert a[k].dtype==b[k].dtype and np.array_equal(a[k],b[k],equal_nan=a[k].dtype.kind in 'fc'),k
 comp['runtime_collision_arrays.npz']=dict(identical=True,arrays=len(a.files))
sources.extend(c/'runtime_collision_arrays.npz' for c in cases)
args=[json.loads((c/'provenance.json').read_text())['args'] for c in cases]
a=json.loads(json.dumps(args[0]).replace(str(old),str(r)));b=args[1].copy();assert b.pop('rear_box_inward_correction') is True;assert a==b,'additional argument differences'
rows=[]
for key,file,upper in [('q','raw.npz',True),('action','raw.npz',True),('q','raw.npz',False),('box','trace.npz',False),('mailer','trace.npz',False)]:
 with np.load(eps[0]/file) as a,np.load(eps[1]/file) as b:
  x=a[key].astype(float);y=b[key].astype(float)
 assert x.shape==y.shape and len(x)==1200
 if upper:x=x[:,12:23];y=y[:,12:23]
 assert np.array_equal(x[0],y[0]);delta=np.max(abs(x-y),axis=1)
 rows.append(dict(key=key,upper11_only=upper,first_different_frame_by_tolerance={str(t):int(np.flatnonzero(delta>t)[0]) if (delta>t).any() else None for t in [0.,1e-8,1e-7,1e-6,1e-4,1e-3]},max_difference_before_first_override=float(max(delta[:first])),difference_at_first_override=float(delta[first])))
for ep in eps:sources.extend(ep/n for n in ['raw.npz','trace.npz','coordination.json','quality.json'])
sources.extend(c/'provenance.json' for c in cases);sources.extend([old/'PROTOCOL.json',r/'PROTOCOL.json'])
assert all(x['first_different_frame_by_tolerance']['1e-06']<first for x in rows if x['key'] in ['q','action','box'])
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,first_inward_override=first,total_inward_overrides=len(active),same_declared_inputs=comp,only_new_argument='rear_box_inward_correction',comparisons=rows,pre_activation_divergence=True,score_difference_is_not_clean_single_factor_causal_estimate=True,source_sha256={str(p):sha(p) for p in sources},training_ready=False)
(r/'PRE_ACTIVATION_COMPARISON.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'},indent=2))
