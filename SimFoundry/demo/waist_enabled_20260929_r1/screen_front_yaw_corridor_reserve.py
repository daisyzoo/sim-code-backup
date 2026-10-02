"""Original front corridor under free target yaw, keeping current tilt and obstacle pose.
Geometric screen only: a negative width does not prove no orientation-controlled path.
No quality change, no layout rejection, no route/controller mutation or physics.
"""
from pathlib import Path
import json,hashlib,datetime,itertools,math
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;B=W/'fresh_closed_peak_trials_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rows=[]
for ep in sorted(B.glob('case_*/layout_*')):
 f=ep/'frontal_bypass.json'
 if not f.exists():continue
 d=json.loads(f.read_text());plan=d['plan']
 if not plan.get('front_route_selected'):continue
 task='box' if 'push_box_to_bin' in ep.name else 'mailer';other='mailer' if task=='box' else 'box';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
 with np.load(ep/'trace.npz') as z:target=z[task].copy();obstacle=z[other].copy()
 with np.load(ep/'parcel_orientation.npz') as z:tq=z[task].copy();oq=z[other].copy()
 def geometry(t):
  vertices=np.array(list(itertools.product(*[[-v/2,v/2] for v in sizes[task]])))@Rotation.from_quat(tq[t]).as_matrix().T
  actual_rad=float(np.max(abs(vertices[:,0])));yaw_radius=float(np.max(np.linalg.norm(vertices[:,:2],axis=1)))
  other_radius=float(abs(Rotation.from_quat(oq[t]).as_matrix()[0])@(sizes[other]/2))
  table=target[t,0]-actual_rad-.28
  current_width=obstacle[t,0]-other_radius-2*actual_rad-.012-.285
  yaw_width=obstacle[t,0]-other_radius-2*yaw_radius-.012-.285
  return dict(step=t,actual_target_x_radius_mm=actual_rad*1000,target_yaw_envelope_radius_mm=yaw_radius*1000,actual_front_table_clearance_mm=table*1000,current_center_interval_width_mm=current_width*1000,all_yaw_center_interval_width_mm=yaw_width*1000)
 first_stop=next((r for r in d['rows'] if r.get('route_stop_reason')),None)
 quality=json.loads((ep/'quality.json').read_text());samples=[geometry(0)]
 if first_stop:samples.append(dict(geometry(first_stop['step']),reason=first_stop['route_stop_reason']))
 rows.append(dict(episode=ep.name,original_numeric_quality_passed=quality['passed'],samples=samples,source_sha256={str(ep/n):sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json','quality.json']}))
assert rows
# Analytic flat rectangle radius sanity check.
assert math.isclose(float(np.linalg.norm(np.array([[.1,.1],[-.1,.1],[.1,-.1],[-.1,-.1]]),axis=1).max()),.1414213562373095,abs_tol=1e-12)
summary=dict(front_selected=len(rows),negative_yaw_width_initial=sum(r['samples'][0]['all_yaw_center_interval_width_mm']<0 for r in rows),original_success_with_negative_yaw_width=sum(r['original_numeric_quality_passed'] and r['samples'][0]['all_yaw_center_interval_width_mm']<0 for r in rows),original_failure_with_negative_yaw_width=sum(not r['original_numeric_quality_passed'] and r['samples'][0]['all_yaw_center_interval_width_mm']<0 for r in rows))
summary={k:int(v) for k,v in summary.items()}
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=rows,training_ready=False,script_sha256=sha(__file__));dest=W/'FRONT_YAW_CORRIDOR_RESERVE_SCREEN.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps(summary));print([(r['episode'],r['original_numeric_quality_passed'],r['samples'][0]['all_yaw_center_interval_width_mm']) for r in rows])
