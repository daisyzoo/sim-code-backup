"""Join existing geometric camera projection with measured task progress/phases.
No new visibility quality gate; no occlusion/segmentation claim.
"""
from pathlib import Path
from collections import Counter
import sys,json,hashlib
import numpy as np
run=Path(sys.argv[1]).resolve();camera_path=run/'CAMERA_VISIBILITY_AUDIT.json';camera=json.loads(camera_path.read_text());results=[]
for item in camera['results']:
 ep=Path(item['episode']);name=ep.name;key='box' if 'push_box' in name else 'mailer';direction=-1 if key=='box' else 1
 quality=json.loads((ep/'quality.json').read_text());control=json.loads((ep/'expert_control.json').read_text());modes={r['step']:r['mode'] for r in control};visibility=item['rows']
 with np.load(ep/'trace.npz') as z:target=z[key].astype(float)
 n=len(target);assert len(visibility)==n and len(control)==n
 progress=direction*(target[:,1]-target[0,1]);in_zone=direction*target[:,1]>=.20;position_met=in_zone&(progress>=.15);met=np.flatnonzero(position_met);release=next((r['step'] for r in control if r['mode'] in ('top_release','goal_release')),n)
 blind=[r['frame'] for r in visibility if not r['bbox_intersects_image']];blind_before=[t for t in blind if t<release];blind_push=[t for t in blind if modes[t]=='top_push'];push=[t for t in range(n) if modes[t]=='top_push'];first=blind[0] if blind else None
 rows=dict(episode=name,task_passed=quality['passed'],first_position_threshold_frame=int(met[0]) if len(met) else None,first_release_frame=release if release<n else None,first_bbox_outside_frame=first,first_bbox_outside_progress_m=float(progress[first]) if first is not None else None,first_bbox_outside_y_m=float(target[first,1]) if first is not None else None,blind_before_release_frames=len(blind_before),blind_before_release_mode_counts=dict(Counter(modes[t] for t in blind_before)),top_push_frames=len(push),blind_top_push_frames=len(blind_push),blind_top_push_fraction=len(blind_push)/len(push) if push else None,blind_top_push_before_position_threshold_frames=sum(not position_met[t] for t in blind_push),raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest())
 results.append(rows)
report=dict(rows=results,camera_audit_sha256=hashlib.sha256(camera_path.read_bytes()).hexdigest(),scope='Existing calibrated oriented-box projection joined to measured pre-action state and expert modes. First position threshold is not stable task success or release. Bbox outside is geometry-only and must be checked against actual RGB samples; intersections do not prove unobscured target. No visibility threshold added, no dataset admission or removal of difficult samples.',training_ready=False)
(run/'VISIBILITY_DURING_WORK.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
