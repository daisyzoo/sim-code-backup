"""Actual rotated collision-box XY footprints versus broad X corridor entry.
Exact convex-polygon separation for observed projected boxes. A 3mm signed-Y
translation sweep is a geometric probe only, not a prediction of physical motion.
The 20mm planning margin is unchanged; all quality gates and failed labels stay.
"""
from pathlib import Path
import itertools,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;B=W/'fresh_closed_peak_trials_r1';source=W/'REAR_RECOVERY_TRIGGER_SPECIFICITY.json';dest=W/'REAR_PROJECTED_CLEARANCE_FINDINGS.json';assert not dest.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hull(points):
 pts=sorted(set(map(tuple,np.asarray(points,float))))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 chains=[]
 for seq in [pts,pts[::-1]]:
  chain=[]
  for p in seq:
   while len(chain)>=2 and cross(chain[-2],chain[-1],p)<=0:chain.pop()
   chain.append(p)
  chains.append(chain)
 return np.asarray(chains[0][:-1]+chains[1][:-1],float)
def separation(a,b):
 ea=np.roll(a,-1,axis=0)-a;eb=np.roll(b,-1,axis=0)-b;edges=np.concatenate([ea,eb]);axes=np.stack([-edges[:,1],edges[:,0]],axis=1);axes/=np.linalg.norm(axes,axis=1)[:,None]
 aa=a@axes.T;bb=b@axes.T;gap=np.maximum(aa.min(0)-bb.max(0),bb.min(0)-aa.max(0))
 if gap.max()<=0:return 0.
 def points_segments(x,y):
  e=np.roll(y,-1,axis=0)-y;d=x[:,None,:]-y[None,:,:];t=np.clip(np.sum(d*e[None,:,:],axis=-1)/np.sum(e*e,axis=-1),0,1);return np.linalg.norm(d-t[:,:,None]*e[None,:,:],axis=-1).min()
 return float(min(points_segments(a,b),points_segments(b,a)))
# Independent analytical squares validate separated/overlap/diagonal/contact cases.
a=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
for shift,expected in [([2.,0.],1.),([2.,2.],2**.5),([.5,.5],0.),([1.,0.],0.)]:assert abs(separation(a,a+shift)-expected)<1e-12
sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};signs=np.array(list(itertools.product([-1.,1.],repeat=3)));rows=[];sources={str(source):sha(source)}
for old in json.loads(source.read_text())['rows']:
 if not old['rear_selected']:continue
 ep=next(B.glob('case_*/'+old['episode']));key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1
 with np.load(ep/'trace.npz') as z:xyz={k:z[k].astype(float) for k in sizes}
 with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
 n=len(xyz[key]);min_all=float('inf');first_close=None;first_swept=None;original_first=None;trigger_set=set(old['all_trigger_steps']);close_count=0;swept_count=0;entry_rows=[]
 for t in range(n):
  polys={k:hull((signs*sizes[k]/2)@rot[k][t].T+xyz[k][t]) for k in []}
  polys={k:hull(((signs*sizes[k]/2)@rot[k][t].T+xyz[k][t])[:,:2]) for k in sizes}
  gap=separation(polys[key],polys[other]);min_all=min(min_all,gap)
  if t not in trigger_set:continue
  swept=hull(np.concatenate([polys[key],polys[key]+[0,direction*.003]]));sgap=separation(swept,polys[other])
  record=dict(step=t,observed_projected_clearance_mm=gap*1000,geometric_3mm_y_swept_clearance_mm=sgap*1000,non_target_control_tick_xy_mm=float(np.linalg.norm(xyz[other][t,:2]-xyz[other][0,:2])*1000))
  if original_first is None:original_first=record
  if gap<.020:
   close_count+=1
   if first_close is None:first_close=record
  if sgap<.020:
   swept_count+=1
   if first_swept is None:first_swept=record
  entry_rows.append(record)
 dis=np.linalg.norm(xyz[other][:,:2]-xyz[other][0,:2],axis=1);moved=np.flatnonzero(dis>.0005)
 rows.append(dict(episode=ep.name,original_quality_passed=old['original_quality_passed'],original_trigger_count=old['trigger_count'],at_original_first_trigger=original_first,observed_close_count=close_count,swept_close_count=swept_count,first_observed_close=first_close,first_swept_close=first_swept,minimum_projected_clearance_mm=min_all*1000,first_other_displacement_over_half_mm=int(moved[0]) if len(moved) else None,other_control_tick_peak_mm=float(dis.max()*1000),entry_rows=entry_rows))
 for name in ['trace.npz','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
summary=dict(episodes=len(rows),original_trigger_episodes=sum(r['original_trigger_count']>0 for r in rows),observed_close_trigger_episodes=sum(r['observed_close_count']>0 for r in rows),swept_close_trigger_episodes=sum(r['swept_close_count']>0 for r in rows),successful_quality_with_swept_close=sum(r['original_quality_passed'] and r['swept_close_count']>0 for r in rows))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=rows,source_sha256=sources,analyzer_sha256=sha(__file__),physics=False,training_ready=False,limitations=['No hand/arm collision or substep clearance is proved by object XY footprints.','Swept probe holds current orientation and assumes translation; real rotation/force remain unmodelled.','Historical observations after any changed trigger cannot be reused as a rollout.'])
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(summary));print(json.dumps([{k:v for k,v in r.items() if k!='entry_rows'} for r in rows],indent=2))
