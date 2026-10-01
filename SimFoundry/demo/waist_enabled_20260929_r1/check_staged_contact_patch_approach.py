"""Causal near-support vertex-set QP; no physical commands or source installation."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
sys.path.insert(0,str(w/'staged_contact_patch_approach'))
from contact_patch_approach import contact_patch_step
from articulated_hand_geometry import ArticulatedHandGeometry
model=ArticulatedHandGeometry(repo/"third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf",repo/"assets/robots/g1_hand_support_vertices.json")
s=(w/'screen_rear_top_contact_reach.py').read_text();exec(compile(s.split("run=root/'current_lateral_profile_r1'")[0],'<checked FK and Jacobians>','exec'))
buffer=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
assert 0<=buffer<=.001
start_mode=sys.argv[2] if len(sys.argv)>2 else "terminal"
assert start_mode in ("terminal","first_eligible")
support_band=float(sys.argv[3]) if len(sys.argv)>3 else .0001
assert 0<support_band<=.002
cases=[w/'contact_bout_yaw_groups_r1/case_898001/layout_898001_push_box_to_bin',w/'fresh_diagonal_02_trial_v2_r1/case_840004/layout_840004_nudge_mailer_to_bin'];results=[]
extra_case=Path(sys.argv[4]).resolve() if len(sys.argv)>4 else None
if extra_case is not None:cases=[extra_case]
for ep in cases:
 side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);other_size=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'raw.npz') as z:allq=z['q'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:alltr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:allori={k:z[k] for k in z.files}
 coords=json.loads((ep/'coordination.json').read_text());by_step={x['step']:x for x in coords};verts=np.array(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);half=size[:2]/2-.01;t=len(allq)-1
 if start_mode=='first_eligible':
  eligible=None
  for event in json.loads((ep/'frontal_bypass.json').read_text())['rows']:
   i=event['step']
   if event['mode'] not in ('top_cross','top_descend') or by_step[i]['contact_normal_tracking'] is not None:continue
   mat,_,_=fk(side,allq[i]);rot=Rotation.from_quat(allori[key][i]).as_matrix();ref=projected_support_reference(verts,mat[:3,:3],rot[:,2]);point=mat[:3,3]+mat[:3,:3]@ref['lowest_vertex_local'];loc=rot.T@(point-alltr[key][i])
   if np.all(abs(loc[:2])<=half) and loc[2]>=size[2]/2+.004:eligible=i;break
  if eligible is None:raise RuntimeError('No causal precontact activation frame for '+ep.name)
  t=eligible
 q0=allq[t];tr={k:v[t] for k,v in alltr.items()};ori={k:v[t] for k,v in allori.items()};coord=by_step[t];assert coord['contact_normal_tracking'] is None;anchor=np.array(coord['inactive_anchor']);rotation=Rotation.from_quat(ori[key]).as_matrix();normal=rotation[:,2]
 def geometry(q):
  return model.scene_geometry(side,q,target_xyz=tr[key],target_quat=ori[key],other_xyz=tr[other],other_quat=ori[other],other_size=other_size)
 for check_side in ['left','right']:
  for qcheck in [q0,np.zeros(11)]:
   for a,b in zip(model.fk(check_side,qcheck),fk(check_side,qcheck)):assert np.max(abs(a-b))<1e-10
 m,_,_=fk(side,q0);fk_error=float(np.linalg.norm(m[:3,3]+m[:3,:3]@np.array([.20,0,.007])-tr['palm_'+side]));assert fk_error<.0001
 q=q0.copy();history=[]
 for k in range(600):
  row=contact_patch_step(q,geometry,lower=lo,upper=hi,step_limits=limits,damping=damping,target_size=size,inactive_anchor=anchor,band_m=support_band,planning_buffer_m=buffer)
  row.update(step=k,q=q.tolist());history.append(row)
  if row['reached'] or not row['accepted'] or row['reason']=='stagnation':break
  q=np.array(row['next_q'])
 result=dict(episode=ep.name,actual_frame=t,actual_fk_error_m=fk_error,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),steps=len(history),geometric_approach_reached=history[-1]['reached'],stop=history[-1]['reason'],min_hand_other_gap_m=min(x['hand_other_gap_m'] for x in history),final=history[-1],history=history);results.append(result);print(json.dumps({k:v for k,v in result.items() if k not in ('history','final')}),flush=True)
report=dict(start_mode=start_mode,band_m=support_band,rows=results,helper_sha256=hashlib.sha256((w/'staged_contact_patch_approach/contact_patch_approach.py').read_bytes()).hexdigest(),geometry_helper_sha256=hashlib.sha256((w/'staged_contact_patch_approach/articulated_hand_geometry.py').read_bytes()).hexdigest(),geometry_source_sha256=model.source_sha256,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual staged helper run through measured-state URDF FK with original bounds; no physical commands or simulator source change. Fixed parcels/ideal tracking, not real contact, force, whole-arm collision or sorting success.',training_ready=False)
if start_mode=='first_eligible' and extra_case is None:
 previous=json.loads((w/'CAUSAL_CONTACT_PATCH_BAND100UM_FIRST_ELIGIBLE_SCREEN.json').read_text());errors=[]
 for a,b in zip(results,previous['rows']):
  assert a['episode']==b['episode'] and a['actual_frame']==b['actual_frame'] and a['steps']==b['steps'] and a['geometric_approach_reached']==b['geometric_approach_reached'];error=float(np.max(abs(np.array(a['final']['q'])-np.array(b['final']['q']))));assert error<1e-8;errors.append(error)
 report['independent_probe_matching_final_q_max_error_rad']=max(errors)
(w/'staged_contact_patch_approach'/('ACTUAL_HELPER_'+start_mode.upper()+('_'+extra_case.name if extra_case else '')+'.json')).write_text(json.dumps(report,indent=2))
