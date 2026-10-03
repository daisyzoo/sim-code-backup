"""Actual baseline/event checks plus one clearly isolated next-update fixture.
Fixture ends before its changed action would execute. No altered future physical
observations are consumed, and no generated record is admitted as training data.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
w=Path(__file__).resolve().parent;root=w.parents[1];draft=w/'rear_waypoint_reconciliation_draft_r1';sys.path[:0]=[str(draft),str(w),str(root)]
from independent_post_commit_audit import load_context,verify
from independent_rear_state_replay import reconstruct
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputpath=draft/'POST_COMMIT_ADAPTER_CHECK.json';test=json.loads(inputpath.read_text());assert test['passed'];sources={str(inputpath):sha(inputpath)}
for p,h in test['source_sha256'].items():assert sha(p)==h,p;sources[p]=h
urdf=root/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';baseline=[];contexts={};evidence={}
for run in test['results']:
 ep=w/run['run']/'case_840023/layout_840023_push_box_to_bin';ctx=load_context(ep,urdf);proof=verify(ctx,run['records']);assert proof['applied_events']==run['applied'];contexts[run['run']]=ctx;evidence[run['run']]=proof
 region=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next((x['step'] for x in region if x['solver'] and x['solver'].get('handover')),None)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z['box'].astype(float)
 actual=reconstruct(ctx['fr']['rows'],ctx['fr']['plan'],ctx['xyz'],quat,ctx['packets'],'box',handover);assert actual['passed'],actual['errors']
 files=list(ep.glob('*REAR_XY*AUDIT.json'));assert len(files)==1;old=json.loads(files[0].read_text());assert old['passed'];assert actual=={k:old[k] for k in actual}
 baseline.append(dict(run=run['run'],full_original_rows=len(ctx['fr']['rows']),original_replay_record_count=actual['overrides_checked'],independent_post_commit_events=proof['applied_events'],same_as_saved_original_replay=True));print(baseline[-1],flush=True)
 ctx.update(handover=handover,quat=quat)
 for path in [files[0],ep/'region_approach.json',ep/'parcel_orientation.npz']:sources[str(path)]=sha(path)
ctx=contexts['front_corridor_midpoint_physical_r1'];proof=evidence['front_corridor_midpoint_physical_r1'];t=566;commit=565;update=proof['verified_post_commit'][commit];prefix=copy.deepcopy([x for x in ctx['fr']['rows'] if x['step']<=t]);last=prefix[-1];original_last=copy.deepcopy(last);prior=prefix[-2];assert last['step']==t and prior['step']==commit
assert last['mode']==prior['mode']=='top_push' and not last['rear_coupled_progress']['override'] and not last['rear_joint_xy_progress']['override'];assert abs(last['target_xyz'][1]-prior['target_xyz'][1]+.0015)<1e-12
shift=update[1]-prior['target_xyz'][1];assert shift>0
last['target_xyz'][1]+=shift;assert last['rear_cop_centering']['override'];last['rear_cop_centering']['command_xyz'][1]+=shift
fixture=reconstruct(prefix,ctx['fr']['plan'],ctx['xyz'][:t+1],ctx['quat'][:t+1],{k:v for k,v in ctx['packets'].items() if k<t},'box',ctx['handover'],verified_post_commit={commit:update});assert fixture['passed'],fixture['errors'];assert fixture['post_commit_overrides_checked']==1
# Declaring the state transition is mandatory; silently altered waypoints fail.
missing=reconstruct(prefix,ctx['fr']['plan'],ctx['xyz'][:t+1],ctx['quat'][:t+1],{k:v for k,v in ctx['packets'].items() if k<t},'box',ctx['handover']);assert not missing['passed'];negative=[dict(case='missing_state_transition',errors=missing['errors'])]
records=next(x['records'] for x in test['results'] if x['run']=='front_corridor_midpoint_physical_r1')
for label,change in [('missing_eligible_event',lambda z:z.pop()),('duplicate_event',lambda z:z.append(copy.deepcopy(z[0]))),('wrong_committed_action',lambda z:z[0]['committed_upper_command'].__setitem__(0,z[0]['committed_upper_command'][0]+.001)),('wrong_next_x',lambda z:z[0]['state_after']['command'].__setitem__(0,z[0]['state_after']['command'][0]+.001)),('wrong_next_y',lambda z:z[0]['state_after']['command'].__setitem__(1,z[0]['state_after']['command'][1]+.001)),('wrong_previous_cursor',lambda z:z[0]['state_before']['command'].__setitem__(1,z[0]['state_before']['command'][1]+.001)),('wrong_measured_load',lambda z:z[0].__setitem__('observed_normal_load_n',0.))]:
 bad=copy.deepcopy(records);change(bad)
 try:verify(ctx,bad)
 except AssertionError:negative.append(dict(case=label,rejected=True))
 else:raise AssertionError('bad event admitted '+label)
for path in [Path(__file__),draft/'independent_post_commit_audit.py',draft/'independent_rear_state_replay.py',draft/'INDEPENDENT_REPLAY_PREPARATION.json',urdf,root/'simfoundry/calibration/sorting_station.py']:sources[str(path)]=sha(path)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,baseline=baseline,independent_event_evidence=evidence,isolated_prefix_fixture=dict(original_steps_through=commit,unchanged_action_through=commit,changed_unexecuted_next_waypoint_step=t,post_commit_state=update,original_next_waypoint=original_last['target_xyz'],hypothetical_next_waypoint=last['target_xyz'],only_changed_row_fields=['target_xyz[1]','rear_cop_centering.command_xyz[1]'],passed=True,replay=fixture),negative_checks=negative,source_sha256=sources,collector_connected=False,physical_rollout=False,training_ready=False)
with (draft/'INDEPENDENT_POST_COMMIT_REPLAY_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(passed=True,baseline_rows=sum(x['full_original_rows'] for x in baseline),independent_events=sum(x['independent_post_commit_events'] for x in baseline),negative_checks=len(negative),fixture_changed_unexecuted_step=t),flush=True)
