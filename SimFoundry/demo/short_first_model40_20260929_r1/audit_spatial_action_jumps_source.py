from pathlib import Path
import numpy as np,json,hashlib
r=Path('SimFoundry/demo/short_first_model40_20260929_r1');rows=[]
for seed,lids in [(0,range(58000,58006)),(1,range(58000,58003))]:
 for lid in lids:
  root=r/f'evaluation/new_spatial160_seed{seed}/layout_{lid}';assert json.loads((root/'STATUS.json').read_text())['status']=='evaluation_complete'
  for p in sorted(root.glob('layout_*/raw.npz')):
   with np.load(p) as d:
    a=d['action'];q=d['q'];assert len(a)==160
    # Absolute raw23 action, matching original quality gate.
    delta=np.abs(np.diff(a,axis=0)); t,j=np.unravel_index(delta.argmax(),delta.shape);t+=1
    bad=np.where(delta.max(axis=1)>.08)[0]+1
    boundary=np.arange(1,len(a))%10==0
    track=np.abs(a[:,12:23]-q[:,12:23])
   quality=json.loads((p.parent/'quality.json').read_text());assert abs(float(delta.max())-quality['metrics']['max_action_step_rad'])<1e-6
   rows.append(dict(seed=seed,layout=lid,task=p.parent.name.split('_',2)[2],raw_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),max_jump_rad=float(delta.max()),max_jump_frame=int(t),max_jump_joint_raw23=int(j),max_at_h10_boundary=bool(t%10==0),violation_frames=bad.tolist(),violation_boundary_frames=[int(x) for x in bad if x%10==0],max_boundary_jump_rad=float(delta[boundary].max()),max_within_chunk_jump_rad=float(delta[~boundary].max()),arm_waist_tracking_abs_p95_rad=float(np.quantile(track,.95)),passed=quality['passed']))
viol=[x for x in rows if x['violation_frames']];out=dict(scope='Completed spatial seed0 layouts58000-58005 and seed1 layouts58000-58002 only; jump index is arrival frame; no smoothing/action cap applied',rows=rows,episodes=len(rows),violating_episodes=len(viol),violation_frames=sum(len(x['violation_frames']) for x in viol),boundary_violation_frames=sum(len(x['violation_boundary_frames']) for x in viol),limitations=['Chunk-boundary association does not prove normalization, label or sampler defect.','Raw action jumps need not equal actual joint motion. Tracking statistic is descriptive, not a contact or reachability gate.'],goal_complete=False)
p=r/'SPATIAL_FIRST18_ACTION_JUMPS.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2));print(json.dumps(viol,indent=2))
