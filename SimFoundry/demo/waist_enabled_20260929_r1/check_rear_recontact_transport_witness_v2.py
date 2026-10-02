"""All saved recontact planning events in fixed11 original/new rear histories.
No new endpoint search, no physics, no synthetic force or loaded contact claim.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_peak_load_guard';sys.path[:0]=[str(W),str(S),str(ROOT)]
from rear_recontact_transport_witness import filter_plan
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';hand=HandModel(urdf,ROOT/'assets/robots/g1_hand_support_vertices.json');elbows=IndependentElbows(S/'elbow_torso_hulls.json',urdf);source=W/'REAR_CORRIDOR_LOSS_FINDINGS.json';inputs=json.loads(source.read_text());dest=W/'REAR_RECONTACT_TRANSPORT_WITNESS_V2_CHECK.json';assert not dest.exists();results=[];sources={};frozen={str(p):sha(p) for p in [Path(__file__),W/'rear_recontact_transport_witness.py',source,S/'recontact_scene.py',S/'clearance_runtime.py',S/'articulated_hand_geometry.py',S/'self_clearance.py',W/'audit_unloaded_wrist_prior_live.py',W/'audit_self_clearance_task_optimality.py']}
def save(status,**kw):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=results,source_sha256=sources,frozen_sha256=frozen,training_ready=False,**kw),indent=2));tmp.replace(dest)
try:
 save('running')
 for item in inputs['episodes']:
  ep=W/item['episode'];p=ep/'recontact_pose.json';j=json.loads(p.read_text());sources[str(p)]=sha(p);entry=dict(episode=item['episode'],events=[],entry_lift_events=[]);results.append(entry)
  for event in j['rows']:
   plan=event.get('planning')
   if not plan:continue
   if event.get('entry_lift_phase'):
    assert 'lift' in plan and 'path' in plan and 'endpoint' not in plan
    entry['entry_lift_events'].append(dict(step=event['context']['step'],parent_accepted=plan['accepted'],scope='Entry lift does not declare a recontact endpoint; not evaluated as a transport landing'))
    continue
   context=event['context'];record=context['scene'];scene=RecontactScene(guard,record['side'],record['target_xyz'],record['target_quat'],record['core_size'],record['other_xyz'],record['other_quat'],record['other_size']);current=context['current'];step=context['step'];assert filter_plan(scene,current,step,plan,enabled=False) is plan;out=filter_plan(scene,current,step,plan,enabled=True);independent=None
   if out['accepted']:
    witness=out['rear_transport_witness'];offset=np.array(witness['reference_offset_local']);q=np.array(plan['endpoint']);cmd=np.array(witness['candidate']);side=record['side'];T=hand.fk(cmd,side);T0=hand.fk(q,side);delta=T[:3,3]+T[:3,:3]@offset-T0[:3,3]-T0[:3,:3]@offset;gaps=elbows.gap(cmd)
    assert .001-1e-7<=delta[0]<=.002+1e-7 and max(abs(delta[1:]))<=1e-7 and min(gaps)>=.005-2e-7
    independent=dict(reference_delta_xyz_m=delta.tolist(),elbow_gaps_m=gaps.tolist())
   entry['events'].append(dict(step=step,parent_accepted=plan['accepted'],result=out.get('rear_transport_witness'),accepted=out['accepted'],reason=out.get('reason'),independent_verification=independent));save('running')
  print(ep.name,len(entry['events']),flush=True)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h
 events=[v for e in results for v in e['events']];save('complete',planning_events=len(events),parent_accepted=sum(v['parent_accepted'] for v in events),nominal_witness_accepted=sum(v['accepted'] for v in events))
except Exception as e:save('check_failed',error=repr(e));raise
