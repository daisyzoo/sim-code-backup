"""Read-only task-objective ablation on recorded states; no action is executed.
Same bounds, normal task, damping, elbow and final guard; inactive task scaling
changes the optimization objective, not the original data/quality requirements.
Five nominal interpolation poses additionally screen inactive-hand/table/parcels.
No force, physical tracking, all-body collision or trajectory feasibility proof.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from task_ik_precision import solve
from clearance_runtime import ClearanceGuard
from audit_self_clearance_task_optimality import IndependentElbows
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';independent=IndependentElbows(S/'elbow_torso_hulls.json',urdf)
paths=[W/'fresh_closed_peak_trials_r1'/f'case_{layout}'/f'layout_{layout}_{task}' for layout,task in [(840008,'push_box_to_bin'),(840008,'nudge_mailer_to_bin'),(840016,'nudge_mailer_to_bin')]]+[W/'terminal_margin_physical_r1/case_840014/layout_840014_nudge_mailer_to_bin'];records=[]
for ep in paths:
 rows={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right';active=slice(3,6) if side=='right' else slice(0,3);other=slice(0,3) if side=='right' else slice(3,6)
 with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in ['box','mailer']}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in ['box','mailer']}
 with np.load(ep/'raw.npz') as z:actions=z['action'][:,12:23].copy()
 for t in [900,1199]:
  c=rows[t];inp=c.get('task_inputs');assert inp is not None;current=np.asarray(inp['current']);previous=np.asarray(inp['previous']);J=np.array(inp['jacobian']);error=np.array(inp['error']);baseline=None;options=[]
  for weight in [1.,.25,0.]:
   candidate=copy.deepcopy(inp);candidate['jacobian']=J.copy();candidate['error']=error.copy();candidate['jacobian'][other]*=weight;candidate['error'][other]*=weight
   command,info=solve(enabled=True,geometry=guard.geometry,**candidate);record=dict(inactive_task_scale=weight,solver=info,command_available=command is not None)
   if command is not None:
    lo=np.maximum.reduce([inp['lower'],current-inp['step_limits'],previous-.055]);hi=np.minimum.reduce([inp['upper'],current+inp['step_limits'],previous+.055]);assert np.all(command>=lo-2e-7) and np.all(command<=hi+2e-7)
    gap=independent.gap(command);assert min(gap)>=.005-2e-7;final=guard.command(command,current,previous);assert final['accepted']
    residual=J@(command-current)-error;ia=[];table=[];elbows=[]
    for fraction in np.linspace(0,1,5):
     q=current+fraction*(command-current);m,_,_=guard.model.fk(inactive,q);vertices=guard.model.vertices[inactive]@m[:3,:3].T+m[:3,3];over=(vertices[:,0]>=.28)&(vertices[:,0]<=.88)&(abs(vertices[:,1])<=.75)
     table.append(float(np.min(vertices[over,2])-.75) if over.any() else None);elbows.append(float(min(independent.gap(q))))
     ia.append({key:float(hand_face_separation(inactive).gap(m[:3,3],Rotation.from_matrix(m[:3,:3]).as_quat(),tr[key][t],ori[key][t],size)) for key,size in [('box',[.14,.09,.045]),('mailer',[.15,.145,.04])]})
    m0,_,_=guard.model.fk(inactive,current);m1,_,_=guard.model.fk(inactive,command);offset=np.array([.20,0,.007]);move=(m1[:3,:3]@offset+m1[:3,3])-(m0[:3,:3]@offset+m0[:3,3])
    record.update(command=command.tolist(),active_linear_residual_mm=float(np.linalg.norm(residual[active])*1000),inactive_linear_residual_mm=float(np.linalg.norm(residual[other])*1000),normal_linear_residual_mm=float(np.linalg.norm(residual[6:])*1000),nominal_inactive_palm_motion_mm=(move*1000).tolist(),independent_endpoint_elbow_min_mm=float(min(gap)*1000),interpolated_elbow_min_mm=float(min(elbows)*1000),inactive_parcel_gaps_mm=[{k:v*1000 for k,v in x.items()} for x in ia],inactive_table_clearance_mm=[None if x is None else x*1000 for x in table],inactive_scene_screen_passed=all(v>=.005 for x in ia for v in x.values()) and all(x is None or x>=.005 for x in table) and min(elbows)>=.005-2e-7,actual_command_difference_rad=float(np.max(abs(command-actions[t]))))
    if weight==1.:baseline=record['active_linear_residual_mm']
    record['active_residual_reduction_vs_parent_mm']=None if baseline is None else baseline-record['active_linear_residual_mm']
   options.append(record)
  records.append(dict(episode=ep.name,step=t,mode=fr[t]['mode'],source_sha256={str(ep/n):sha(ep/n) for n in ['coordination.json','frontal_bypass.json','raw.npz','trace.npz','parcel_orientation.npz']},options=options));print(ep.name,t,[(o['inactive_task_scale'],o.get('active_linear_residual_mm'),o.get('inactive_scene_screen_passed')) for o in options],flush=True)
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,simulation_started=False,collector_integrated=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),S/'task_ik_precision.py',S/'clearance_runtime.py',S/'articulated_hand_geometry.py',W/'audit_self_clearance_task_optimality.py',urdf,ROOT/'simfoundry/data/paired_sorting.py']})
dest=W/'INACTIVE_ANCHOR_TASK_COMPETITION_PROBE.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2))
