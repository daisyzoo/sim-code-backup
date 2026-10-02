"""Hypothetical rear-route landing feasibility, not parcel transport or a rollout.
Use the first recorded unloaded top-cross robot pose, original bounds and planner.
Parcel translation to a proposed rear corner/goal exists ONLY in this CPU geometry
fixture. No simulator/object state is written. Feasible landing alone proves no
loaded path, live handover, dynamics, visibility or training eligibility.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from recontact_plan import plan
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);independent=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');inputs=json.loads((W/'FRONT_YAW_CORRIDOR_ALTERNATIVES.json').read_text());records=[];out=W/'FRONT_ALTERNATIVE_REAR_LANDING_PROBE.json';assert not out.exists()
source={str(p):sha(p) for p in [Path(__file__),W/'FRONT_YAW_CORRIDOR_ALTERNATIVES.json',S/'recontact_scene.py',S/'recontact_plan.py',S/'recontact_plan_original.py',S/'recontact_plan_deeper.py',S/'minimum_motion_recontact.py',S/'clearance_runtime.py',S/'articulated_hand_geometry.py',W/'audit_self_clearance_task_optimality.py']}
def save(status,**kwargs):
 tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=records,source_sha256=source,simulation_started=False,collector_integrated=False,training_ready=False,**kwargs),indent=2));tmp.replace(out)
try:
 save('running')
 for item in inputs['rows']:
  ep=W/'fresh_closed_peak_trials_r1'/('case_'+item['episode'].split('_')[1])/item['episode'];d=json.loads((ep/'frontal_bypass.json').read_text());selected=next(r for r in d['rows'] if r['mode']=='top_cross' and r.get('contact_load',{}).get('observed_vertical_load_n',1)<.05);t=selected['step']
  with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:target=z['mailer'][0].astype(float);other=z['box'][0].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:tq=z['mailer'][0];oq=z['box'][0]
  core=d['plan']['top_recontact']['contact_size_xyz'];other_size=d['plan']['top_recontact'].get('obstacle_contact_geometry',{}).get('collision_core_size_xyz',[.14,.09,.045]);rear=next(c for c in item['alternatives'] if c['route']=='rear');assert rear['object_envelope_eligible']
  for label,index in [('rear_corner',1),('rear_goal',2)]:
   synthetic=target.copy();synthetic[:2]=rear['waypoints_xy'][index];scene=RecontactScene(guard,'left',synthetic,tq,core,other,oq,other_size);save('running',current_episode=ep.name,current_point=label)
   proposal=plan(scene,q,step=t,prefer_interior=True,minimum_motion_pose=True);checks=[]
   if proposal['accepted']:
    for value in proposal['waypoints']:
     x=np.asarray(value);check=scene.check(x);gap=float(min(independent.gap(x)));checks.append(dict(scene_passed=check['accepted'],independent_elbow_gap_m=gap,joint_bounds_passed=bool(np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7))))
   verified=bool(proposal['accepted'] and checks and all(c['scene_passed'] and c['independent_elbow_gap_m']>=.005-2e-7 and c['joint_bounds_passed'] for c in checks))
   record=dict(episode=ep.name,point=label,reference_step=t,reference_is_actual_unloaded_pose=True,synthetic_target_xyz=synthetic.tolist(),parcel_translation_is_hypothetical=True,current_scene_check=scene.check(q),planner=proposal,nominal_path_check=checks,verified_static_landing_and_nominal_path=verified,actual_transport_verified=False,source_sha256={str(ep/n):sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']})
   records.append(record);save('running');print(ep.name,label,'accepted',proposal['accepted'],'verified_static_path',verified,'reason',proposal['reason'],flush=True)
 save('complete')
except Exception as e:save('failed',error=repr(e));raise
