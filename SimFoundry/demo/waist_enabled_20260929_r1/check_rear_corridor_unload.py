"""All250 failed loaded-recovery inputs, not a simulated unload trajectory.
Independent nominal reference and entire-hand lowest height verify emitted steps.
Passing one step does not establish contact unloading or a feasible recontact path.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_peak_load_guard';sys.path[:0]=[str(W),str(STAGE),str(ROOT)]
from rear_corridor_unload_candidate import solve_lift
from clearance_runtime import ClearanceGuard
from audit_self_clearance_task_optimality import IndependentElbows
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,STAGE);urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';verts=ROOT/'assets/robots/g1_hand_support_vertices.json';ind=IndependentElbows(STAGE/'elbow_torso_hulls.json',urdf);hand=HandModel(urdf,verts);vertices=json.loads(verts.read_text())['vertices']
source=wsource=W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json';input_report=json.loads(source.read_text());assert input_report['status']=='complete';dest=W/'REAR_CORRIDOR_UNLOAD_CHECK.json';assert not dest.exists();rows=[];sources={};frozen={str(p):sha(p) for p in [Path(__file__),W/'rear_corridor_unload_candidate.py',source,STAGE/'clearance_runtime.py',STAGE/'articulated_hand_geometry.py',STAGE/'self_clearance.py',STAGE/'elbow_torso_hulls.json',W/'audit_unloaded_wrist_prior_live.py',W/'audit_self_clearance_task_optimality.py',urdf,verts]};negative=[]
def save(status,**kwargs):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,frozen_sha256=frozen,negative_checks=negative,training_ready=False,**kwargs),indent=2));tmp.replace(dest)
try:
 save('running')
 for item in input_report['episodes']:
  selected=[r for r in item['rows'] if r['result'].get('requires_recontact')]
  if not selected:continue
  ep=W/item['episode'];fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())}
  with np.load(ep/'raw.npz') as z:actions=z['action'].copy()
  for n in ['frontal_bypass.json','coordination.json','raw.npz']:sources[str(ep/n)]=sha(ep/n)
  for itemrow in selected:
   t=itemrow['step'];c=cs[t];r=fr[t];q=np.array(c['upper_q']);prev=actions[t-1,12:23];parent=actions[t,12:23];args=dict(guard=guard,row=r,coordinate=c,current=q,previous=prev,parent_command=parent,recovery_result=itemrow['result']);cmd,result=solve_lift(**args);check=None
   if cmd is not None:
    assert result['applied'];side=c['active_side'];T=hand.fk(cmd,side);T0=hand.fk(q,side);offset=np.array(r['control_offset_local']);delta=T[:3,3]+T[:3,:3]@offset-T0[:3,3]-T0[:3,:3]@offset;v=np.array(vertices[side]);h=float(np.min((v@T[:3,:3].T+T[:3,3])[:,2])-np.min((v@T0[:3,:3].T+T0[:3,3])[:,2]));gap=ind.gap(cmd)
    assert max(abs(delta[:2]))<=1e-7 and .0005-1e-7<=delta[2]<=.003+1e-7 and h>=.0005-1e-7 and min(gap)>=.005-2e-7
    assert np.all(cmd>=guard.lower-2e-7) and np.all(cmd<=guard.upper+2e-7) and np.all(abs(cmd-q)<=guard.limits+2e-7) and max(abs(cmd-prev))<=.0550002
    check=dict(independent_reference_delta_xyz_m=delta.tolist(),independent_lowest_hand_height_increment_m=h,independent_elbow_gaps_m=gap.tolist())
   else:assert not result['applied'] and result['requires_stop']
   rows.append(dict(episode=str(ep.relative_to(W)),step=t,result=result,independent_verification=check))
   if not negative:
    for label,mutate in [('already_applied',lambda a:a['recovery_result'].update(applied=True)),('table_rejection',lambda a:a['recovery_result'].update(reason='table_route_infeasible')),('parent_release',lambda a:a['row'].update(mode='top_release')),('parent_guard',lambda a:a['row'].update(route_stop_reason='guard')),('causal_mismatch',lambda a:a.update(current=q+.001))]:
     bad=dict(args,row=copy.deepcopy(r),recovery_result=copy.deepcopy(args['recovery_result']));mutate(bad)
     try:solve_lift(**bad)
     except ValueError:negative.append(label)
     else:raise AssertionError(('invalid lift admitted',label))
   if len(rows)%25==0:save('running');print(len(rows),flush=True)
 for p,h in {**frozen,**sources}.items():assert sha(p)==h,p
 assert len(rows)==250;save('complete',nominal_steps_verified=sum(r['result']['applied'] for r in rows),unverified_steps=sum(not r['result']['applied'] for r in rows))
except Exception as e:save('check_failed',error=repr(e));raise
