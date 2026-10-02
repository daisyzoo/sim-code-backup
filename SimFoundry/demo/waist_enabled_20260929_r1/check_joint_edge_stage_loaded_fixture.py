"""Synthetic baseline serialization regression of full loaded execution checks.
Source acceptance is explicitly excluded and independently must reject fixture.
Only the record replay function is exercised with a scoped mocked source check.
This report is neither a physical run nor data admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,tempfile,shutil
from unittest.mock import patch
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;S=W/'staged_joint_edge_clearance_intersection';ROOT=W.parents[1];sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from joint_edge_clearance_adapter_candidate import repair_record
from joint_edge_stage_source_binding import verify_trial_provenance
from audit_joint_edge_stage_pose_loaded_execution import replay
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=json.loads((S/'WHOLE_EPISODE_FIXTURE_CHECK.json').read_text());old=Path(source['fixture_root'])/'case';root=Path(tempfile.mkdtemp(prefix='joint_edge_loaded_fixture_'));case=root/'case';shutil.copytree(old,case,symlinks=True)
ep=case/'layout_840004_nudge_mailer_to_bin';prov=json.loads((case/'provenance.json').read_text());prov['args']['role']='diagnostic';(case/'provenance.json').write_text(json.dumps(prov))
# The earlier negative fixture deliberately deleted one trace; reconstruct all
# eligible traces anew from fixed original inputs, never altering actual data.
cs=json.loads((ep/'coordination.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in fr['rows']};core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'];guard=ClearanceGuard(ROOT,S)
with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
with np.load(ep/'trace.npz') as z:xyz=z['mailer'].copy()
with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['mailer']).as_matrix()
for c in cs:
 if not c.get('joint_edge_refinement',{}).get('override'):continue
 t=c['step'];x,tr=repair_record(guard=guard,row=rows[t],coordinate=c,current=q[t,12:23],previous=u[t-1,12:23],command=u[t,12:23],object_xyz=xyz[t],object_rotation=rot[t],core_size=core);assert np.array_equal(x,u[t,12:23]);c['joint_edge_clearance_intersection']=tr
(ep/'coordination.json').write_text(json.dumps(cs));(ep/'JOINT_EDGE_STAGE_POSE_LIVE_AUDIT.json').write_text((ep/'CLOSED_PEAK_TRIAL_POSE_LIVE_AUDIT.json').read_text())
try:verify_trial_provenance(case)
except (AssertionError,KeyError,ValueError):pass
else:raise AssertionError('Fixture passed stage source admission')
original_collector=W/'staged_closed_peak_trial/collect_paired_sorting.py'
with patch('audit_joint_edge_stage_contract.verify_joint_edge_stage_source',return_value=None) as mock_source:
 result=replay(ep,original_collector);assert mock_source.call_count==1
assert result['passed'] and len(result['final_intersection_records'])==71 and result['final_intersection_changed']==0
print('Full loaded parent and original-edge checks pass with 71 independently rechecked final intersections',flush=True)
# An output trace mutation must fail even with source explicitly out of scope.
first=next(c for c in cs if 'joint_edge_clearance_intersection' in c);first['joint_edge_clearance_intersection']['output_command'][1]+=.001;(ep/'coordination.json').write_text(json.dumps(cs))
with patch('audit_joint_edge_stage_contract.verify_joint_edge_stage_source',return_value=None):
 try:replay(ep,original_collector)
 except AssertionError:rejected=True
 else:raise AssertionError('Tampered output trace accepted')
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,fixture_root=str(root),fixture_not_physical=True,stage_source_admission_rejected=True,source_mock_only_for_record_regression=True,loaded_parent_frames=result['parent_full_push_replay_frames'],refinement_frames=result['refinement_frames'],final_intersections=len(result['final_intersection_records']),changed=0,tampered_output_rejected=rejected,task_frames=result['nonlinear_task_execution']['independent_task_frames'],source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_joint_edge_stage_pose_loaded_execution.py',W/'audit_joint_edge_stage_loaded_parent.py',W/'audit_joint_edge_stage_task_optimality.py',W/'audit_joint_edge_clearance_record.py']},training_ready=False)
out=W/'JOINT_EDGE_STAGE_LOADED_FIXTURE_CHECK.json'
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
