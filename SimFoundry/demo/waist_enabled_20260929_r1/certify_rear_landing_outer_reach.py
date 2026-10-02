"""Necessary reach bound for hypothetical rear landings; not a transport plan.
Triangle inequality bounds every hand vertex from the shoulder pitch origin.
For continuous waist yaw, a grid distance minimum minus a Lipschitz allowance
is a lower bound. A positive distance-minus-chain-radius gap certifies only
this static landing region unreachable within the existing waist interval.
Non-positive results are inconclusive. No simulator or object state changes.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();g=ClearanceGuard(ROOT,S);src=W/'FRONT_ALTERNATIVE_REAR_LANDING_PROBE_V2.json';d=json.loads(src.read_text());assert d['status']=='complete'
def shoulder(side,yaw):
 m=g.model.base.copy()
 for name,origin,axis in g.model.chains[side]:
  m=m@origin
  if name==side+'_shoulder_pitch_joint':return m[:3,3].copy()
  if axis is not None:
   assert name=='waist_yaw_joint'
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*yaw).as_matrix();m=m@a
 raise AssertionError('missing shoulder')
rows=[]
for item in d['rows']:
 scene=item['planner']['scene'];side=scene['side'];chain=g.model.chains[side];idx=next(i for i,x in enumerate(chain) if x[0]==side+'_shoulder_pitch_joint');lengths=[float(np.linalg.norm(o[:3,3])) for _,o,_ in chain[idx+1:]];hand_radius=float(np.max(np.linalg.norm(g.model.vertices[side],axis=1)));radius=sum(lengths)+hand_radius
 # The only moving prefix is waist yaw; shoulder origin traces a circle.
 assert idx==1 and chain[0][0]=='waist_yaw_joint';arm_offset=chain[idx][1][:3,3];axis=chain[0][2];waist_circle_radius=float(np.linalg.norm(arm_offset-axis*np.dot(axis,arm_offset)))
 yaws=np.linspace(g.lower[0],g.upper[0],4097);spacing=float(yaws[1]-yaws[0]);allowance=waist_circle_radius*spacing/2
 points=np.array([shoulder(side,y) for y in yaws]);rot=Rotation.from_quat(scene['target_quat']).as_matrix();local=(points-scene['target_xyz'])@rot;core=np.array(scene['core_size']);bounds=[]
 for label,inset,zlo,zhi in [('original_planner',.012,.006,.007),('original_measured_handover',.010,.004,.010)]:
  lo=np.r_[-core[:2]/2+inset,core[2]/2+zlo];hi=np.r_[core[:2]/2-inset,core[2]/2+zhi];dist=np.linalg.norm(local-np.clip(local,lo,hi),axis=1);k=int(dist.argmin());lower=float(dist[k]-allowance);gap=lower-radius
  bounds.append(dict(scope=label,inset_m=inset,above_top_range_m=[zlo,zhi],sampled_minimum_distance_m=float(dist[k]),sampled_minimizer_waist_rad=float(yaws[k]),continuous_distance_lower_bound_m=lower,necessary_reach_gap_m=gap,certified_unreachable_in_region=bool(gap>1e-9),conclusion='necessary_bound_violated' if gap>1e-9 else 'inconclusive'))
 # Sanity-check the analytic chain bound with fixed reproducible joint samples.
 rng=np.random.default_rng(20261003);maximum=0.
 for q in rng.uniform(g.lower,g.upper,(100,11)):
  mat,_,_=g.model.fk(side,q);v=g.model.vertices[side]@mat[:3,:3].T+mat[:3,3];distance=float(np.linalg.norm(v-shoulder(side,q[0]),axis=1).max());assert distance<=radius+1e-12;maximum=max(maximum,distance)
 rows.append(dict(episode=item['episode'],point=item['point'],synthetic_target_xyz=scene['target_xyz'],triangle_link_lengths_m=lengths,hand_vertex_radius_m=hand_radius,shoulder_reach_outer_radius_m=radius,waist_interval_rad=[float(g.lower[0]),float(g.upper[0])],waist_grid_count=len(yaws),waist_circle_radius_m=waist_circle_radius,grid_lipschitz_allowance_m=allowance,sanity_fk_samples=100,sanity_max_observed_radius_m=maximum,bounds=bounds,physical_transport_verified=False))
sources={str(p):sha(p) for p in [Path(__file__),src,S/'articulated_hand_geometry.py',S/'clearance_runtime.py',S/'recontact_scene.py',S/'minimum_motion_lifecycle.py',ROOT/'simfoundry/calibration/sorting_station.py']};sources.update(g.model.source_sha256)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,simulation_started=False,training_ready=False)
dest=W/'REAR_LANDING_OUTER_REACH_CERTIFICATE.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps([dict(episode=r['episode'],point=r['point'],bounds=r['bounds']) for r in rows],indent=2))
