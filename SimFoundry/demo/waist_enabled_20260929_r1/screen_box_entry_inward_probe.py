"""Recorded selected right-rear inputs, same original task/bounds/forward constraint.
Compare zero-margin replay and explicit0.5/1mm inward demand. Actual future object
and joint states are not used to produce a candidate. Geometry only, not physics.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_entry_lift';sys.path[:0]=[str(stage),str(w),str(repo)]
import joint_edge_adapter as adapter
from joint_edge_inward_probe import refine_rear_command
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
r=w/'box_entry_lift_groups_r1';ep=r/'case_840001/layout_840001_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};core=fr['plan']['rear_cop_centering']['actual_core_size_xyz'];guard=ClearanceGuard(repo,stage);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
with np.load(ep/'trace.npz') as z:xyz=z['box'].copy();other=z['mailer'].copy()
with np.load(ep/'parcel_orientation.npz') as z:quat=z['box'].copy();oq=z['mailer'].copy()
rows=[];original=adapter.refine_rear_command;out=r/'INWARD_COMMAND_SCREEN.json'
def save(complete):
 sources=[Path(__file__),w/'joint_edge_inward_probe.py',stage/'joint_edge_command.py',stage/'joint_edge_adapter.py',stage/'clearance_runtime.py',stage/'recontact_scene.py',ep/'raw.npz',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'frontal_bypass.json',ep/'coordination.json'];summary={}
 for margin in [0.,.0005,.001]:
  rr=[x for x in rows if x['inward_step_m']==margin];summary[str(margin)]=dict(total=len(rr),solver_direction_verified=sum(x['direction_verified'] for x in rr),original_command_guard_passed=sum(x['command_guard']['accepted'] for x in rr),hand_gap_passed=sum(x['min_other_hand_gap_m']>=.01 for x in rr),combined_qualified=sum(x['direction_verified'] and x['command_guard']['accepted'] and x['min_other_hand_gap_m']>=.01 for x in rr),reasons=dict(collections.Counter(x['trace']['reason'] for x in rr)))
 out.write_text(json.dumps(dict(scope=__doc__,complete=complete,rows=rows,summary=summary,source_sha256={str(p):sha(p) for p in sources},physical_validation=False,training_ready=False),indent=2));return summary
try:
 for f in fr['rows']:
  t=f['step'];c=cs[t];trace=c.get('joint_edge_refinement',{})
  if not trace.get('input_selected'):continue
  assert f['mode']=='top_push';scene=RecontactScene(guard,'right',xyz[t],quat[t],core,other[t],oq[t],[.15,.145,.04]);R=Rotation.from_quat(quat[t]).as_matrix();parent=trace['parent_final_upper_command'];common=dict(enabled=True,row=f,coordinate=c,current=q[t],previous=u[t-1],parent_command=parent,object_xyz=xyz[t],object_rotation=R,core_size=core,model=guard.model,side='right',analytic_retry=True,parent_seed_retry=True)
  adapter.refine_rear_command=original
  baseline_cmd,baseline_event=adapter.refine_record(**common)
  for margin in [0.,.0005,.001]:
   adapter.refine_rear_command=lambda **kw:refine_rear_command(**kw,inward_step_m=margin)
   cmd,event=adapter.refine_record(**common)
   if margin==0.:assert np.array_equal(cmd,baseline_cmd) and event==baseline_event,('zero_same_input_original_replay',t)
   verified=event['reason'] in ['nonlinear_joint_direction','parent_direction_valid'];check=guard.command(cmd,q[t],u[t-1]);g=scene.details(cmd);rows.append(dict(step=t,inward_step_m=margin,zero_same_input_original_replay_exact=margin==0.,original_replay_vs_recorded_max_rad=float(np.max(abs(baseline_cmd-np.array(trace['final_upper_command'])))),direction_verified=verified,command_guard=check,min_other_hand_gap_m=float(min(g['gaps'].values())),actual_core_clearance=g['gaps'],trace=event))
  print('step',t,[(x['inward_step_m'],x['trace']['reason'],x['command_guard']['accepted'],round(x['min_other_hand_gap_m'],5)) for x in rows[-3:]],flush=True);save(False)
finally:adapter.refine_rear_command=original
assert rows;print('COMPLETE',save(True),flush=True)
