"""Unloaded recontact endpoint reserve probes on fixed actual left/right contexts.
Additional0.10rad waist reserve, never wider limits. Preserve all original
endpoint constraints and whole sampled path. No actual execution after context.
"""
from pathlib import Path
import json,hashlib,datetime,sys,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_transport_retry';sys.path[:0]=[str(W),str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from minimum_motion_recontact_waist_reserve_probe import plan as left_plan
from box_center_preference_plan_waist_reserve_probe import plan as right_plan
from audit_recontact_pose_events import EventAudit
from rear_recontact_transport_witness import witness
from audit_rear_transport_witness import verify_witness
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'RECONTACT_WAIST_RESERVE_PROBE.json';assert not dest.exists();guard=ClearanceGuard(ROOT,S);audit=EventAudit(ROOT,S);rows=[];sources={}
def save(status,**kw):
 out=dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,analyzer_sha256=sha(__file__),probe_source_sha256={str(W/n):sha(W/n) for n in ['minimum_motion_recontact_waist_reserve_probe.py','box_center_preference_plan_waist_reserve_probe.py']},physics=False,training_ready=False,**kw);tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2));tmp.replace(dest)
try:
 save('running')
 for run,seed,task in [('fresh_closed_peak_trials_r1',840004,'nudge_mailer_to_bin'),('rear_transport_retry_physical_r1',840015,'push_box_to_bin')]:
  ep=W/run/f'case_{seed}'/f'layout_{seed}_{task}';p=ep/'recontact_pose.json';events=json.loads(p.read_text())['rows'];event=next(r for r in events if (r.get('planning') or {}).get('accepted') and not r.get('entry_lift_phase'));ctx=event['context'];s=ctx['scene'];q=np.array(ctx['current']);scene=RecontactScene(guard,s['side'],s['target_xyz'],s['target_quat'],s['core_size'],s['other_xyz'],s['other_quat'],s['other_size']);sources[str(p)]=sha(p);fn=right_plan if s['side']=='right' else left_plan;result=fn(scene,q,step=event['step'],parent_plan=event['planning']);key='box_center_preference_pose' if s['side']=='right' else 'minimum_motion_pose';selected=result[key]['selected']=='candidate';item=dict(episode=str(ep.relative_to(W)),step=event['step'],selected_new_endpoint=selected,original_endpoint_waist_rad=event['planning']['endpoint'][0],result=result)
  if selected:
   x=np.array(result['endpoint']);assert abs(x[0])<=.88+2e-7
   rec,geometry=audit.geometry(x,s);assert rec['accepted'];core=np.array(s['core_size']);pt=np.array(rec['contact_object_local']);assert min(core[:2]/2-.02-abs(pt[:2]))>=-2e-7 and .006-2e-7<=rec['active_above_top_m']<=.007+2e-7;assert min(audit.elbows.gap(x))>=.005-2e-7;inactive='left' if s['side']=='right' else 'right';assert audit.hand.minz(x,inactive)>=.84-2e-7
   _,vectors=np.linalg.eigh(np.cov(audit.hand.vertices[s['side']].T));normal=geometry['rotation'][:,2];axis=vectors[:,0];assert abs(normal@(geometry['pose'][:3,:3]@axis))>=.8-2e-7
   previous=q
   for command in result['waypoints']:
    command=np.array(command);actual,_=audit.geometry(command,s);assert actual['accepted'];assert np.max(abs(command-previous)/(audit.limits*.25))<=1.+1e-9;previous=command
   assert np.allclose(previous,x,atol=1e-12,rtol=0)
   wi=witness(scene,x);proof=verify_witness(audit,wi,endpoint=x,scene=s) if wi['accepted'] else None
   item.update(independent_endpoint_and_path_passed=True,nominal_waypoints=len(result['waypoints']),new_endpoint_waist_rad=float(x[0]),unloaded_direction_witness=wi,independent_direction_proof=proof)
  rows.append(item);save('running');print(ep.name,'candidate',selected,'waypoints',item.get('nominal_waypoints'),'direction',item.get('unloaded_direction_witness',{}).get('accepted'),flush=True)
 save('complete',new_endpoints=sum(r['selected_new_endpoint'] for r in rows),remaining='Nominal endpoint only; loaded-motion reserve, actual press/settling, measured tracking/handover and whole paired physics still unverified.')
except BaseException as e:save('failed',error=repr(e));raise
