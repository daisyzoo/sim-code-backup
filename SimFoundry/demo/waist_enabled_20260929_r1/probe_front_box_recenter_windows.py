"""Actual failed front-box recovery windows and unissued recenter feasibility.
Uses frozen original two-sided first-center planning mathematics as a geometric/
causal probe only. It does not run a right-recovery controller or predict force,
transport success, cross-window continuity or model performance.
"""
from pathlib import Path
import sys,json,datetime,hashlib
from collections import Counter
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';D=W/'front_box_recenter_draft_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_plan import checked_scene
from front_initial_center_selection import plan
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=W/'front_corridor_midpoint_physical_r1/case_840020/layout_840020_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];initial=json.loads((ep/'front_initial_center.json').read_text());template=next(v['context']['scene'] for v in initial['rows'] if 'context' in v);assert template['side']=='right'
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23];u=z['action'][:,12:23]
with np.load(ep/'trace.npz') as z:target=z['box'];other=z['mailer']
with np.load(ep/'parcel_orientation.npz') as z:tq=z['box'];oq=z['mailer']
assert q.shape==u.shape==(1200,11)
packets={v['after_action_step']:v for v in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};decay=json.loads((S/'causal_response_parameters.json').read_text())['tasks']['push_box_to_bin']['decay'];guard=ClearanceGuard(ROOT,S);audit=SelectionAudit(ROOT,S);windows={};eligible={}
for r in rows:
 counter=r['recontacts'];t=r['step'];g=windows.setdefault(counter,dict(counter=counter,first_step=t,last_step=t,mode_counts={},exit_reason=r.get('last_recontact_reason'),unloaded_candidates=0,original_geometry_eligible=0,first_eligible=None));g['last_step']=t;g['mode_counts'][r['mode']]=g['mode_counts'].get(r['mode'],0)+1
 if counter==0 or r['mode'] not in ('top_cross','top_descend') or r.get('route_stop_reason') or r.get('release_reason'):continue
 load=r['contact_load'];measured=sum(abs(float(v['force_world_N'][2])) for v in packets[t-1]['parcel_contacts'] if any('right_wrist_roll' in n for n in v['shapes']) and any('/parcel_box/' in n for n in v['shapes']));assert abs(measured-load['observed_vertical_load_n'])<1e-10
 if measured!=0 or not 0<=load['filtered_vertical_load_n']<=.05:continue
 g['unloaded_candidates']+=1;scene=RecontactScene(guard,'right',target[t],tq[t],template['core_size'],other[t],oq[t],template['other_size']);check=checked_scene(scene,q[t]);independent,_=audit.geometry(q[t],scene.record());audit.compare_geometry(check,independent)
 if check['accepted']:
  g['original_geometry_eligible']+=1
  if g['first_eligible'] is None:g['first_eligible']=t;eligible[counter]=(t,scene)
for g in windows.values():
 a,b=g['first_step'],g['last_step'];g['target_y_progress_mm']=float((target[a,1]-target[b,1])*1000)
selected=[1,6,12];probes=[]
for counter in selected:
 if counter not in eligible:probes.append(dict(counter=counter,eligible=False,reason='no_original_unloaded_geometry_window'));continue
 t,scene=eligible[counter];planning=plan(scene,q[t],step=t,previous_q=q[t-1],previous_command=u[t-1],decay=decay);proof=audit.verify_selection(planning,current=q[t],previous_q=q[t-1],previous_command=u[t-1],decay=decay,scene=scene.record(),step=t);assert proof['passed'];pre=planning.get('transport_preflight',{})
 probes.append(dict(counter=counter,step=t,eligible=True,planning=planning,independent_proof=proof,actual_context=dict(current=q[t].tolist(),previous_q=q[t-1].tolist(),previous_command=u[t-1].tolist(),actual_recontact_counter=counter,scope='Original first-center causal probe internally uses private first-contact lifecycle; actual episode counter is retained here. No runtime replacement or actual capture.'),hypothetical_transport_accepted=pre.get('accepted',False)));print(counter,t,planning['accepted'],planning.get('reason'),flush=True)
files=[Path(__file__),*[ep/n for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','front_initial_center.json','solved_contact_forces.json','quality.json']],*S.glob('*.py'),S/'causal_response_parameters.json',S/'elbow_torso_hulls.json',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_preflight.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete_original_frames=1200,windows=list(windows.values()),selected_counters=selected,probes=probes,source_sha256={str(p):sha(p) for p in files},runtime_implemented=False,new_physics=False,training_ready=False)
with (D/'RECENTER_WINDOW_PROBE.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(actual_recovery_counters=len(windows)-1,eligible_counters=sorted(eligible),probed=len(probes),hypothetical_accepted=sum(v.get('hypothetical_transport_accepted',False) for v in probes),new_physics=False)))
