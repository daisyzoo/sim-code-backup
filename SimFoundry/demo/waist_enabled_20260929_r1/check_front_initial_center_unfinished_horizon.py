"""Deliberately synthetic 1200-frame file ending with an unfinished new path.
Only tests native lifecycle finalization; the prefix is not a physical trajectory.
"""
from pathlib import Path
import sys,json,hashlib,tempfile,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_front_initial_center_live_v2 import verify_files
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=W/'FRONT_INITIAL_CENTER_SELECTION_CHECK.json';d=json.loads(source.read_text());original=next(r for r in d['records'] if '840023' in r['episode']);event=copy.deepcopy(original['live_first_event']);ctx=event['context'];z=ctx['scene'];n=1200;t=n-1
assert event['kind']=='command';event['context']['step']=t;event['planning']['step']=t;event['planning']['transport_preflight']['initial_context']['step']=t
out=W/'FRONT_INITIAL_CENTER_UNFINISHED_HORIZON_CHECK.json';assert not out.exists()
report=dict(status='running',scope=__doc__,simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),source,W/'audit_front_initial_center_live_v2.py']})
def save():report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();out.write_text(json.dumps(report,indent=2))
try:
 save()
 with tempfile.TemporaryDirectory(prefix='unfinished-front-fixture-') as tmp:
  ep=Path(tmp);q=np.zeros((n,23));u=q.copy();q[t-1,12:23]=ctx['previous_q'];q[t,12:23]=ctx['current'];u[t-1,12:23]=ctx['previous_command'];u[t,12:23]=event['command']
  np.savez_compressed(ep/'raw.npz',q=q,action=u,task_id='nudge_mailer_to_bin',fixture_only=True)
  np.savez_compressed(ep/'trace.npz',mailer=np.tile(z['target_xyz'],(n,1)),box=np.tile(z['other_xyz'],(n,1)))
  np.savez_compressed(ep/'parcel_orientation.npz',mailer=np.tile(z['target_quat'],(n,1)),box=np.tile(z['other_quat'],(n,1)))
  def put(name,value):(ep/name).write_text(json.dumps(value))
  evs=[dict(step=i,kind='unchanged',reason='not_initial_front_unloaded_phase') for i in range(1,n)];evs[-1]=dict(step=t,**event);put('front_initial_center.json',dict(selected=True,rows=evs,training_ready=False))
  fr=[dict(step=i,mode='top_lift' if i<t else 'top_cross',recontacts=0,target_xyz=z['target_xyz'],contact_load=dict(observed_vertical_load_n=0.,filtered_vertical_load_n=0.,applied_z_bias_m=0.,stored_z_bias_m=0.)) for i in range(1,n)]
  put('frontal_bypass.json',dict(plan=dict(front_route_selected=True,front_initial_center_landing=dict(actual_core=dict(collision_core_size_xyz=z['core_size']))),rows=fr))
  coords=[dict(step=i,controller_kind='fixture_parent',contact_normal_tracking=None) for i in range(1,n)];coords[-1]=dict(step=t,controller_kind='verified_unloaded_front_initial_joint_path',front_initial_center_override=event,upper_q=q[t,12:23].tolist(),active_side='left',bounded_solver=True,task_inputs=None,contact_normal_tracking=None,contact_bout_yaw_tracking=None)
  put('coordination.json',coords);put('expert_control.json',[dict(step=0,mode='fixture',target_xyz=[0,0,0])]+[dict(step=r['step'],mode=r['mode'],target_xyz=r['target_xyz']) for r in fr]);put('solved_contact_forces.json',dict(rows=[dict(after_action_step=i,parcel_contacts=[]) for i in range(n)]));put('self_clearance.json',dict(failure=None,requested_frames=n,recorded_frames=n))
  reason=None
  try:verify_files(ep)
  except AssertionError as e:reason=str(e)
  assert reason=='unfinished initial-front path',reason
 report.update(status='complete',passed=True,rejected_at_end_of_horizon=True,reason=reason,full_frames=n);save();print(reason,'rejected',flush=True)
except Exception as e:report.update(status='failed',error=repr(e));save();raise
