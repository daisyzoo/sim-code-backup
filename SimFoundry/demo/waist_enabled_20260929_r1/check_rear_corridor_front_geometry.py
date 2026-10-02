"""Complete original front geometry/action-chain/KKT regression, no new physics.
Fixture case metadata are read-only links to original archives. Recovery is not
selected. This is verify-function integration, not new-stage source admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(W),str(ROOT)]
from audit_rear_corridor_stage_pose_self_clearance import audit
from audit_closed_peak_trial_pose_self_clearance import audit as original
from audit_rear_corridor_stage_pose_task_optimality import verify_task_rows,IndependentElbows
from audit_joint_edge_stage_task_optimality import verify_task_rows as original_task
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'REAR_CORRIDOR_FRONT_GEOMETRY_CHECK.json';assert not dest.exists();rows=[];sources={};check=json.loads((W/'REAR_CORRIDOR_FRONT_POSE_CHECK.json').read_text());assert check['passed']
fixture=Path(check['fixture_root']);case=Path(check['rows'][0]['episode']).parent
for p in case.iterdir():
 if p.name.startswith('layout_'):continue
 if not (fixture/p.name).exists():os.symlink(p,fixture/p.name,target_is_directory=p.is_dir())
geom=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
def save(status,**extra):
 p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,training_ready=False,**extra),indent=2));p.replace(dest)
try:
 save('running')
 for item in check['rows']:
  ep=fixture/Path(item['episode']).name;parent=original(ep,verified_events={});new=audit(ep,verified_events={})
  assert {k:v for k,v in new.items() if k not in ['recovery_overrides','recovery_input_auditor_sha256']}==parent
  assert new['episode_clearance_passed'] and new['executed_frames']==1200 and new['recovery_overrides']==0
  ptask=original_task(ep,geom,{});ntask=verify_task_rows(ep,geom,{})
  for k in ['passed','errors','frames','overrides','max_kkt_residual','records']:assert ptask[k]==ntask[k],k
  rows.append(dict(task=item['task'],geometry_equal=True,complete_frames=1200,task_kkt_equal=True,task_kkt_passed=ntask['passed'],original_kkt_failures=ntask['errors'],minimum_command_support_gap_m=new['minimum_command_support_gap_m']));save('running');print(item['task'],flush=True)
 for p in [Path(__file__),W/'REAR_CORRIDOR_FRONT_POSE_CHECK.json',W/'audit_rear_corridor_stage_pose_self_clearance.py',W/'audit_rear_corridor_stage_pose_task_optimality.py',W/'rear_corridor_audit_inputs.py']:sources[str(p)]=sha(p)
 save('complete',passed=True)
except BaseException as e:save('check_failed',error=repr(e));raise
