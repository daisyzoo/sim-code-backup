"""Labeled synthetic serialization fixture built from a full unchanged episode.
No physical result is fabricated: raw camera data are omitted, stage source
admission MUST reject this fixture, and only the explicit record-audit entry is
exercised with already audited original unloaded events. One-command changes
remain separately checked by the independent record regression.
"""
from pathlib import Path
import sys,tempfile,json,hashlib,datetime,copy,shutil
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_edge_clearance_intersection';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from joint_edge_clearance_adapter_candidate import repair_record
from audit_joint_edge_stage_self_clearance import audit
from joint_edge_stage_source_binding import verify_trial_provenance
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
R=Path(sys.argv[1]).resolve();base=R/'case_840004/layout_840004_nudge_mailer_to_bin';out=S/'WHOLE_EPISODE_FIXTURE_CHECK.json';assert not out.exists();root=Path(tempfile.mkdtemp(prefix='edge_intersection_audit_fixture_'));case=root/'case';ep=case/base.name;ep.mkdir(parents=True);guard=ClearanceGuard(ROOT,S)
for p in base.parent.iterdir():
 if p.name=='provenance.json':continue
 if p.is_file() or p.name in ['source_snapshot','runtime_source','substep_runtime_sources']:(case/p.name).symlink_to(p.resolve(),target_is_directory=p.is_dir())
for p in base.iterdir():
 if p.name not in ['raw.npz','coordination.json']:(ep/p.name).symlink_to(p.resolve(),target_is_directory=p.is_dir())
prov=json.loads((base.parent/'provenance.json').read_text());prov['args']['edge_clearance_intersection']=True;(case/'provenance.json').write_text(json.dumps(prov))
with np.load(base/'raw.npz') as z:
 saved={k:z[k].copy() for k in ['q','action','intrinsics','collect_meta','task_id']}
meta=json.loads(str(saved['collect_meta']));meta['edge_clearance_intersection']=True;saved['collect_meta']=np.array(json.dumps(meta));np.savez_compressed(ep/'raw.npz',**saved)
coords=json.loads((base/'coordination.json').read_text());fr=json.loads((base/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']
with np.load(base/'trace.npz') as z:xyz=z['mailer'].copy()
with np.load(base/'parcel_orientation.npz') as z:rots=Rotation.from_quat(z['mailer']).as_matrix()
n=0
for c in coords:
 tr=c.get('joint_edge_refinement')
 if not tr or not tr.get('override'):continue
 t=c['step'];x,trace=repair_record(guard=guard,row=fs[t],coordinate=c,current=saved['q'][t,12:23],previous=saved['action'][t-1,12:23],command=saved['action'][t,12:23],object_rotation=rots[t],object_xyz=xyz[t],core_size=core);assert np.array_equal(x,saved['action'][t,12:23]) and not trace['changed'];c['joint_edge_clearance_intersection']=trace;n+=1
assert n==71;(ep/'coordination.json').write_text(json.dumps(coords))
events={v['step']:{k:x for k,x in v.items() if k!='step'} for v in json.loads((base/'recontact_pose.json').read_text())['rows'] if v['kind'] in ('command','handover')};pose=json.loads((base/'CLOSED_PEAK_TRIAL_POSE_LIVE_AUDIT.json').read_text());assert pose['passed'] and set(events)=={v['step'] for v in pose['records']}
try:verify_trial_provenance(case)
except (AssertionError,KeyError,ValueError):source_rejected=True
else:raise AssertionError('Synthetic fixture admitted as actual stage source')
result=audit(ep,verified_events=events);assert result['passed'] and result['executed_frames']==1200 and result['controller_frames']==1199 and len(result['intersection_records'])==71 and result['intersection_changed']==0
print('positive1200records with71unchanged edge repairs passed',flush=True)
# Coverage is substantive: deleting one added repair log cannot be silently
# accepted because final actions happen to equal baseline actions.
changed=copy.deepcopy(coords);target=next(c for c in changed if 'joint_edge_clearance_intersection' in c);del target['joint_edge_clearance_intersection'];(ep/'coordination.json').write_text(json.dumps(changed))
try:audit(ep,verified_events=events)
except AssertionError as e:assert 'intersection' in str(e);negative=str(e)
else:raise AssertionError('Missing branch accepted')
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,fixture_root=str(root),fixture_not_physical=True,source_admission_rejected=source_rejected,executed_baseline_frames=result['executed_frames'],controller_frames=result['controller_frames'],unchanged_edge_branches=n,missing_branch_rejected=negative,minimum_actual_support_gap_m=result['minimum_actual_support_gap_m'],minimum_command_support_gap_m=result['minimum_command_support_gap_m'],source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_joint_edge_stage_self_clearance.py',W/'audit_joint_edge_clearance_record.py',W/'joint_edge_stage_source_binding.py',S/'joint_edge_clearance_adapter_candidate.py',S/'joint_edge_clearance_intersection_candidate.py',base/'raw.npz',base/'coordination.json',base/'CLOSED_PEAK_TRIAL_POSE_LIVE_AUDIT.json']},training_ready=False)
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
# The labeled tiny fixture remains under/tmp for inspection; raw images were
# never copied or removed and actual input files remain untouched.
