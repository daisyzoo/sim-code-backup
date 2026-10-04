"""Original task KKT mathematics, with separately verified unloaded joint paths.
Original loaded/ordinary task bounds, objective and1e-6 stationarity are retained.
A joint-path event is accepted here only after the independent full live audit.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from support_vertex_stationarity import certificate,VERSION
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_self_clearance_task_optimality import IndependentElbows,near
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from simfoundry.data.bounded_ik import bounded_damped_step
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

from audit_front_loaded_z_quarter_r1_task_rows import verify_task_rows

def inspect(ep):
 from audit_front_loaded_z_quarter_r1_v1_stage_pose_live import inspect as inspect_pose,source_contract
 ep=Path(ep).resolve();stage=source_contract(ep);pose=inspect_pose(ep)
 assert pose==json.loads((ep/'FRONT_LOADED_Z_QUARTER_R1_V1_STAGE_POSE_LIVE_V2_AUDIT.json').read_text())
 prov=json.loads((ep.parent/'provenance.json').read_text());src=prov['source_sha256'];snap=ep.parent/'source_snapshot'
 assert not prov['args'].get('expert_top_contact_bout_yaw_hold')
 for n in ['simfoundry/robots/g1_assets.py','simfoundry/data/bounded_ik.py']:assert sha(repo/n)==src[n]
 names=[n for n in src if n.endswith('/task_ik.py')];assert len(names)==1 and sha(snap/names[0])==sha(w/'staged_rear_short_recovery/task_ik.py')
 events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'recontact_pose.json').read_text())['rows'] if r['kind'] in ('command','handover')}
 assert set(events)=={r['step'] for r in pose['records']}
 front={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'front_initial_center.json').read_text())['rows'] if r['kind'] in ('command','handover')}
 assert set(front)=={r['step'] for r in pose['front_records']}
 recovery={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'front_recontact_center.json').read_text())['rows'] if r['kind'] in ('command','handover')}
 assert set(recovery)=={r['step'] for r in pose['front_recovery_records']}
 geom=IndependentElbows(stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
 out=verify_task_rows(ep,geom,events,verified_front_events=front,verified_front_recovery_events=recovery);out.update(pose_audit_sha256=sha(ep/'FRONT_LOADED_Z_QUARTER_R1_V1_STAGE_POSE_LIVE_V2_AUDIT.json'),pose_auditor_sha256=sha(w/'audit_front_loaded_z_quarter_r1_v1_stage_pose_live.py'),original_auditor_sha256=sha(w/'audit_self_clearance_task_optimality.py'))
 out.update(task_row_auditor_sha256=sha(w/'audit_front_loaded_z_quarter_r1_task_rows.py'))
 out.update(stationarity_version=VERSION,math_revision_manifest_sha256=sha(w/'POSE_TASK_VERTEX_V2_REVISION.json'),vertex_certificate_source_sha256=sha(w/'support_vertex_stationarity.py'),frozen_parent_auditor_sha256=sha(w/'audit_closed_peak_trial_pose_task_optimality.py'),original_episode_parent_report_required=False,admission_protocol_changed=False)
 return out
if __name__=='__main__':
 ep=Path(sys.argv[1]);path=ep/'FRONT_LOADED_Z_QUARTER_R1_V1_STAGE_TASK_OPTIMALITY_V2_AUDIT.json';assert not path.exists();out=inspect(ep);path.write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['records','scope','source_sha256']});sys.exit(0 if out['passed'] else 1)
