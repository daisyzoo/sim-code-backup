"""Compare new diagonal core-edge distance to independent bounded ray LP.
Default direction=None must exactly preserve the existing axis-edge governor.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import linprog
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;stage=w/'staged_front_diagonal_entry_probe';sys.path[:0]=[str(stage),str(w/'staged_front_direction_recontact')]
from front_edge_speed_direction import edge_speed as candidate
from front_edge_speed import edge_speed as parent
rng=np.random.default_rng(427);rows=[]
for i in range(120):
 size=rng.uniform([.08,.07,.03],[.16,.15,.05]);point=np.r_[rng.uniform(-.55,.55,2)*size[:2],size[2]/2];rot=Rotation.from_euler('xyz',[*rng.uniform(-.03,.03,2),rng.uniform(-np.pi,np.pi)]).as_matrix();v=rng.normal(size=2);v/=np.linalg.norm(v);kw=dict(enabled=True,mode='top_push',nominal_step_m=.002,normal_load_n=4.,cop_local=point,object_rotation=rot,core_size=size,axis=i%2,sign=1 if i%3 else -1)
 assert candidate(**kw)==parent(**kw)
 out=candidate(**kw,world_direction_xy=v);ray=(rot.T@np.r_[v,0.])[:2];half=size[:2]/2
 if np.all(abs(point[:2])<=half):
  fit=linprog([-1.],A_ub=np.r_[ray,-ray][:,None],b_ub=np.r_[half-point[:2],half+point[:2]],bounds=[(0,None)],method='highs');assert fit.success;distance=fit.x[0]
 else:distance=0.
 assert abs(out['forward_core_distance_m']-distance)<1e-9
 expected=.001+.001*min(1.,distance/.010);assert abs(out['drive_step_m']-expected)<1e-12
 rows.append(dict(case=i,distance_m=float(distance),step_m=out['drive_step_m'],default_direction_exact=True))
for invalid in [[0,0],[1,2,3],[float('nan'),0]]:
 try:candidate(**kw,world_direction_xy=invalid)
 except ValueError:pass
 else:raise AssertionError('Invalid direction accepted')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();out=dict(passed=True,scope=__doc__,random_lp_cases=120,invalid_direction_cases=3,rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'front_edge_speed_direction.py',w/'staged_front_direction_recontact/front_edge_speed.py']},physical_validation=False,training_ready=False);(stage/'EDGE_DIRECTION_CHECK.json').write_text(json.dumps(out,indent=2));print('passed120independentLP/default-axis checks and3invalid directions')
