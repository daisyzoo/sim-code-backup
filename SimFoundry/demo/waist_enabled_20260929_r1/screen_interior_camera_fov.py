"""Counterfactual pinhole coverage from recorded poses; no synthetic RGB or camera change.
Projected collision-box coverage ignores occlusion and lens distortion. A wider
view at fixed640x480 reduces target pixel size; this does not prove model benefit.
"""
from pathlib import Path
import json,hashlib,datetime,math
import numpy as np
w=Path(__file__).resolve().parent;r=w/'recontact_interior_groups_r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=r/'OBSERVABILITY_AND_BOUTS_PARTIAL.json';data=json.loads(src.read_text());results=[]
for e in data['episodes']:
 target='box' if 'push_box' in e['episode'] else 'mailer';other='mailer' if target=='box' else 'box';ep=next(r.glob('case_*/'+e['episode']))
 v=json.loads((ep/'viewer_observer.json').read_text())['frames'];ks={f['pre_action_step']:np.array(f['policy_camera_intrinsics']) for f in v}
 with np.load(ep/'raw.npz') as z:height,width=z['rgb'].shape[2:]
 limit=np.array([width,height]);scales=[]
 for scale in [1.,.75,.6,.5,.4,.3]:
  rows=[]
  for f in e['camera_rows']:
   k=ks[f['step']];center=k[:2,2];entry=dict(step=f['step'])
   for obj in [target,other]:
    lo=center+scale*(np.array(f[obj]['bbox_min'])-center);hi=center+scale*(np.array(f[obj]['bbox_max'])-center)
    clipped=np.maximum(0,np.minimum(hi,limit)-np.maximum(lo,0));entry[obj]=dict(fraction=float(np.prod(clipped)/np.prod(hi-lo)),bbox_wh_pixels=(hi-lo).tolist())
   rows.append(entry)
  k=ks[rows[0]['step']];scales.append(dict(focal_scale=scale,horizontal_fov_deg=math.degrees(2*math.atan(width/(2*k[0,0]*scale))),vertical_fov_deg=math.degrees(2*math.atan(height/(2*k[1,1]*scale))),samples=len(rows),target_outside=sum(x[target]['fraction']==0 for x in rows),both_outside=sum(x[target]['fraction']==0 and x[other]['fraction']==0 for x in rows),target_at_least_half=sum(x[target]['fraction']>=.5 for x in rows),both_at_least_half=sum(min(x[target]['fraction'],x[other]['fraction'])>=.5 for x in rows),target_median_projected_bbox_wh_pixels=np.median([x[target]['bbox_wh_pixels'] for x in rows],axis=0).tolist()))
 result=dict(episode=e['episode'],counterfactual_scales=scales,source_sha256={'viewer_observer.json':sha(ep/'viewer_observer.json'),'raw.npz':sha(ep/'raw.npz')});results.append(result);print(json.dumps(result['counterfactual_scales']));print(e['episode'],flush=True)
(r/'CAMERA_FOV_SCREEN.json').write_text(json.dumps(dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256={src.name:sha(src)},script_sha256=sha(Path(__file__)),episodes=results,training_ready=False,physical_camera_changed=False),indent=2))
