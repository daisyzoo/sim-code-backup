"""Matched complete front-bag lasttick traction; not a continuous friction proof.
No altered material, command, quality gate or admission. Force ratios use recorded
contact frames and friction, and retain all push samples, including absent load.
"""
from pathlib import Path
import collections,datetime,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'front_effective_height_physical_r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
sources={str(Path(__file__)):sha(Path(__file__))};versions=[]
def stats(xs):
 return None if not xs else dict(n=len(xs),mean=float(np.mean(xs)),median=float(np.median(xs)),p90=float(np.quantile(xs,.9)),max=float(max(xs)))
for run in ['front_corridor_lateral_physical_r1','front_loaded_z_quarter_physical_r2','front_effective_height_physical_r1']:
 ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';quality=read(ep/'quality.json');assert quality['frames']==1200
 fr=read(ep/'frontal_bypass.json');packets={p['after_action_step']:p for p in read(ep/'solved_contact_forces.json')['rows']}
 with np.load(ep/'trace.npz') as z:xyz=z['mailer'].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['mailer']).as_matrix()
 records=[];mus=collections.Counter()
 for row in fr['rows']:
  t=row['step']
  if row['mode']!='top_push':continue
  p=packets[t-1];assert p['solver_force_buffer_unchanged'];np.testing.assert_allclose(p['post_action_pose']['mailer'],xyz[t],rtol=0,atol=1e-6)
  groups={k:dict(force=np.zeros(3),normal=0.,weighted_l1=0.,contacts=0) for k in ['hand','table','other']}
  for c in p['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/mailer/' in s]
   if len(slots)!=1:continue
   k='hand' if any('left_wrist' in s for s in c['shapes']) else 'table' if any('/table/' in s for s in c['shapes']) else 'other'
   f=np.array(c['force_torque_contact']);mu=np.array(c['friction']);basis=np.array(c['contact_frame']);world=np.array(c['force_world_N']);np.testing.assert_allclose(f[:3]@basis,world,rtol=0,atol=1e-5)
   g=groups[k];g['force']+=(1 if slots[0]==1 else -1)*world;g['contacts']+=1
   if f[0]>.05 and min(mu[:2])>0:
    g['normal']+=float(f[0]);g['weighted_l1']+=float(abs(f[1])/mu[0]+abs(f[2])/mu[1]);mus[(k,tuple(float(v) for v in mu[:2]))]+=1
  record=dict(step=t,target_tilt_rad=float(np.arccos(np.clip(rot[t,2,2],-1,1))),groups={k:dict(force_world_n=g['force'].tolist(),contact_normal_n=g['normal'],normal_weighted_l1_ratio=g['weighted_l1']/g['normal'] if g['normal'] else None,contacts=g['contacts']) for k,g in groups.items()});records.append(record)
 loaded=[r for r in records if r['groups']['hand']['contact_normal_n']>=.3]
 summary={k:dict(normal_n=stats([r['groups'][k]['contact_normal_n'] for r in loaded]),l1_ratio=stats([r['groups'][k]['normal_weighted_l1_ratio'] for r in loaded if r['groups'][k]['normal_weighted_l1_ratio'] is not None]),ratio_above_098=sum((r['groups'][k]['normal_weighted_l1_ratio'] or 0)>.98 for r in loaded)) for k in groups}
 versions.append(dict(run=run,progress_mm=quality['metrics']['target_final_progress_m']*1000,quality_passed=quality['passed'],push_frames=len(records),loaded_lasttick_frames=len(loaded),summary=summary,recorded_mu=[dict(kind=k,mu=list(mu),contacts=n) for (k,mu),n in mus.items()],records=records))
 for name in ['frontal_bypass.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz','quality.json']:sources[str(ep/name)]=sha(ep/name)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,versions=versions,source_sha256=sources,training_ready=False,limitations=['Lasttick measurements do not prove continuous sliding or integrated force balance.','L1 translational utilization omits rotational friction allocation.','No mass, static force balance, or future contact assumption used to declare mechanical impossibility.','Full-height older run also failed; do not infer that merely increasing downpressure will solve current full task.'])
encoded=json.dumps(report,indent=2)
with (R/'FRONT_BAG_TRACTION_COMPARISON_V1.json').open('x') as f:f.write(encoded)
print(json.dumps([{k:v for k,v in x.items() if k!='records'} for x in versions]))
