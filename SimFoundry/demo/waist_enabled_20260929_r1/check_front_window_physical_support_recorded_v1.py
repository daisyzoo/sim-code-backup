"""Independent nominal FK check of recorded current physical/virtual supports.
Fixed recorded observations, not new dynamic rollout. FK is checked against
recorded physical support coordinates; no force or command is replaced.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_z_quarter_v1';C=W/'front_contact_window_candidate_v1';sys.path[:0]=[str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
from simfoundry.data.top_contact_bypass import support_vertex
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);sources={};rows=[]
for run in ['front_loaded_z_quarter_physical_r2','joint_transport_reserve_physical_r1']:
 for case,task,side,key in [(840023,'nudge_mailer_to_bin','left','mailer'),(840020,'push_box_to_bin','right','box')]:
  ep=W/run/f'case_{case}'/f'layout_{case}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());half=np.array(fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'])[:2]/2
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23]
  with np.load(ep/'parcel_orientation.npz') as z:ori=z[key]
  records=[]
  for r in fr['rows']:
   t=r['step'];T,_,_=guard.model.fk(side,q[t]);quat=Rotation.from_matrix(T[:3,:3]).as_quat();v=np.array(support_vertex(side,quat,ori[t]));physical=T[:3,3]+T[:3,:3]@v
   recorded=np.array(r['observed_physical_support_xyz']);virtual=np.array(r['observed_support_xyz']);R=Rotation.from_quat(ori[t]).as_matrix();target=np.array(r['observed_target']);margin=lambda p:float(min(half-abs((R.T@(p-target))[:2])))
   old=margin(recorded);new=margin(physical);vm=margin(virtual)
   records.append(dict(step=t,mode=r['mode'],physical_error_m=float(np.max(abs(physical-recorded))),physical_vertex_match=bool(np.allclose(v,r['physical_support_offset_local'],atol=1e-12,rtol=0)),recorded_margin_m=old,fk_margin_m=new,virtual_margin_m=vm,physical_vs_virtual_distance_m=float(np.linalg.norm(recorded-virtual)),eligibility_matches=(old>=.010)==(new>=.010),virtual_eligibility_differs=(old>=.010)!=(vm>=.010)))
  maxerror=max(r['physical_error_m'] for r in records);bad=[r for r in records if r['physical_error_m']>1e-4 or not r['eligibility_matches']]
  rows.append(dict(episode=str(ep.relative_to(W)),frames=len(records),max_physical_error_m=maxerror,vertex_mismatch_count=sum(not r['physical_vertex_match'] for r in records),eligibility_mismatch_count=sum(not r['eligibility_matches'] for r in records),virtual_eligibility_difference_count=sum(r['virtual_eligibility_differs'] for r in records),max_physical_virtual_distance_m=max(r['physical_vs_virtual_distance_m'] for r in records),bad=bad,records=records))
  print(json.dumps({k:v for k,v in rows[-1].items() if k not in ['records','bad']}),flush=True)
  for p in [ep/'raw.npz',ep/'frontal_bypass.json',ep/'parcel_orientation.npz']:sources[str(p)]=sha(p)
for p in [Path(__file__),S/'clearance_runtime.py',S/'articulated_hand_geometry.py',ROOT/'simfoundry/data/top_contact_bypass.py',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=all(not r['bad'] for r in rows),episodes=rows,source_sha256=sources,collector_modified=False,physics_verified=False,training_ready=False)
with (C/'PHYSICAL_SUPPORT_RECORDED_CHECK_V1.json').open('x') as f:json.dump(report,f,indent=2)
print('PASSED',report['passed'])
