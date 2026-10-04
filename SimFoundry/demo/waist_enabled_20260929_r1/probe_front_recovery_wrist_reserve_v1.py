"""Prospective 0.30rad wrist reserve on actual same-observation recovery inputs.
Only nominal geometry and the existing local causal-response preflight are
examined. No hypothetical capture enters physics or any later recorded state.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_recontact_center_selection import select_planned
from front_initial_center_plan import checked_scene
from front_recovery_wrist_reserve_candidate_v1 import plan
from front_recontact_center_lifecycle_static import FrontRecontactCenterLifecycle
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
D=W/'front_recovery_wrist_reserve_probe_r1';D.mkdir(exist_ok=False);ep=W/'front_effective_height_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';rs=read(ep/'front_recontact_center.json')['rows'];guard=ClearanceGuard(ROOT,S)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
selected=[r for r in rs if r.get('planning') and r['planning']['accepted'] and r['step']>=900];assert len(selected)==3
reports=[]
for event in selected:
 c=event['context'];t=event['step'];scene=RecontactScene(guard,**c['scene']);assert scene.record()==c['scene'];np.testing.assert_array_equal(q[t],c['current']);np.testing.assert_array_equal(q[t-1],c['previous_q']);np.testing.assert_array_equal(u[t-1],c['previous_command']);assert c['observed_load_n']==0 and 0<=c['filtered_load_n']<=.05
 frozen=sha(ep/'raw.npz');static=plan(scene,q[t],step=t,wrist_reserve_rad=.30)
 p=select_planned(static,scene,q[t],step=t,previous_q=c['previous_q'],previous_command=c['previous_command'],decay=c['decay'],recontact_index=c['recontacts'])
 checks=[]
 if static['accepted']:
  endpoint=np.array(static['endpoint']);assert min(endpoint[5]-guard.lower[5],guard.upper[5]-endpoint[5])>=.30-2e-7
  assert checked_scene(scene,endpoint)['accepted']
 if p['accepted']:
  for waypoint in p['waypoints']:
   checked=checked_scene(scene,waypoint);assert checked['accepted'];checks.append(checked)
  assert p['transport_preflight']['predicted_capture_discarded']
 assert sha(ep/'raw.npz')==frozen
 item=dict(step=t,recontact_index=c['recontacts'],actual_start_wrist_rad=float(q[t,5]),parent_endpoint_wrist_rad=event['planning']['endpoint'][5],static_accepted=static['accepted'],causal_preflight_accepted=p['accepted'],candidate_endpoint_wrist_rad=p.get('endpoint',[None]*6)[5],candidate_endpoint_reserve_rad=None if not static['accepted'] else float(min(np.array(static['endpoint'])[5]-guard.lower[5],guard.upper[5]-np.array(static['endpoint'])[5])),planning=p,independent_scene_checks=checks)
 reports.append(item);print(json.dumps({k:v for k,v in item.items() if k not in ['planning','independent_scene_checks']}),flush=True)
 with (D/'PROGRESS.json').open('w') as f:json.dump(dict(rows=reports,expected=3,training_ready=False),f,indent=2)
sources={str(p):sha(p) for p in [Path(__file__),W/'front_recovery_wrist_reserve_candidate_v1.py',ep/'front_recontact_center.json',ep/'raw.npz']}
for m in list(sys.modules.values()):
 f=getattr(m,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=reports,source_sha256=sources,installed=False,physical_validated=False,training_ready=False,limitation='Only three actual late front-bag recovery contexts. Nominal geometry and assumed local-response transport cannot establish contact stability, later wrist freedom, or sorting success.')
with (D/'RESULT.json').open('x') as f:json.dump(result,f,indent=2)
