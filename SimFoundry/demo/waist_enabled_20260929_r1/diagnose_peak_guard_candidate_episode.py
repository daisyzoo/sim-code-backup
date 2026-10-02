from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w))
from audit_peak_guard_pressure import verify_stream
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=Path(sys.argv[1]).resolve();old=w/'substep_reference03_groups_r1'/ep.parent.name/ep.name
h=json.loads((ep/'PEAK_GUARD_LOAD_HISTORY.json').read_text());p=json.loads((ep/'peak_load_updates.json').read_text());f=json.loads((ep/'frontal_bypass.json').read_text());loads={x['action_step']:x['vertical_load_n'] for x in h['rows']}
v=verify_stream(p,f,loads,frames=1200,wait=False)
held=[x['action_step'] for x in v['records'] if x['held_negative_increment']]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Actual complete candidate: independent pressure stream and baseline divergence diagnosis, not full native audit closure or success.',pressure_verification=v,held_steps=held,first_differences={},training_ready=False)
for name,keys in [('raw.npz',['q','action']),('trace.npz',['box','mailer'])]:
 with np.load(ep/name) as a,np.load(old/name) as b:
  for key in keys:
   aa=a[key][:,12:23] if key in ['q','action'] else a[key];bb=b[key][:,12:23] if key in ['q','action'] else b[key]
   d=np.max(abs(aa.astype(float)-bb.astype(float)),axis=1)
   out['first_differences'][key]={str(t):int(np.flatnonzero(d>t)[0]) if np.any(d>t) else None for t in [1e-7,1e-5,1e-3]}
out['held_events']=[x for x in p['rows'] if x['action_step'] in held]
out['source_sha256']={str(z):sha(z) for z in [ep/'peak_load_updates.json',ep/'frontal_bypass.json',ep/'PEAK_GUARD_LOAD_HISTORY.json',ep/'raw.npz',ep/'trace.npz',old/'raw.npz',old/'trace.npz',w/'audit_peak_guard_pressure.py',w/'audit_peak_load_update_math.py',Path(__file__)]}
dest=ep/'PRESSURE_STREAM_DIAGNOSIS.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2))
print(json.dumps(dict(pressure_passed=v['passed'],pressure_updates=v['pressure_updates'],control_frames=v['control_frames'],held_steps=held,first_differences=out['first_differences']),indent=2))
