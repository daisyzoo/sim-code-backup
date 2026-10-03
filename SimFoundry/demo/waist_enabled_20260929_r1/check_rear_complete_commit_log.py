"""Log-envelope fixtures over original recorded histories; no altered rollout.
Applied records are earlier independent, unexecuted per-frame proposals. This
checks completeness and rejection, never admits the composed history as physics.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'rear_waypoint_reconciliation_draft_r1';sys.path[:0]=[str(D),str(W),str(ROOT)]
from independent_post_commit_audit import load_context
from independent_commit_log_contract import verify_complete_log
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};inputpath=D/'POST_COMMIT_ADAPTER_CHECK.json';test=json.loads(inputpath.read_text());assert test['passed']
for p,h in test['source_sha256'].items():assert sha(p)==h;sources[p]=h
urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';results=[]
def base(step,reason):return dict(step=step,version='rear_box_post_commit_adapter_draft_v1',applied=False,current_action_changed=False,training_ready=False,reason=reason)
def declaration(selected):return dict(requested=True,enabled=selected,post_successful_action_only=True,post_guard_required=True,changes='next_state_command_y_and_last_waypoint_y_only',current_action_unchanged=True,default_off=True,training_ready=False)
for run in test['results']:
 ep=W/run['run']/'case_840023/layout_840023_push_box_to_bin';ctx=load_context(ep,urdf);ctx['fr']['plan']['rear_waypoint_reconciliation']=declaration(True)
 records={x['step']:x for x in run['records']};rows=[records.get(t,base(t,'first_zero_frame_preserved' if t==0 else 'fixture_unchanged_no_application')) for t,p in ctx['pg'].items() if p['accepted']]
 log=dict(rows=rows,training_ready=False);meta=dict(rear_waypoint_reconciliation=True,rear_waypoint_reconciliation_applied_frames=len(records));report=verify_complete_log(ctx,log,meta,'push_box_to_bin',frames=len(ctx['q']));assert report['complete_event_rows']==1200 and report['independently_verified_events']['applied_events']==len(records)
 results.append(dict(run=run['run'],fixture_event_rows=len(rows),independent_applied_events=len(records)));print(results[-1],flush=True)
# Other branches use original full actions and actual accepted guards, with an
# explicitly synthetic all-no-op log (not an emitted collector log).
branch_checks=[]
for layout,task in [(840022,'push_box_to_bin'),(840020,'nudge_mailer_to_bin'),(841011,'wait_no_package')]:
 ep=W/'front_corridor_midpoint_physical_r1'/f'case_{layout}'/f'layout_{layout}_{task}'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 clear=json.loads((ep/'self_clearance.json').read_text());frp=ep/'frontal_bypass.json';fr=json.loads(frp.read_text()) if frp.exists() else None
 if task!='wait_no_package':fr['plan']['rear_waypoint_reconciliation']=declaration(False)
 other=dict(q=q,u=u,fg={x['step']:x for x in clear['rows'] if x['phase']=='final_command'},pg={x['step']:x for x in clear['rows'] if x['phase']=='post'},fr=fr)
 other_log=dict(rows=[base(t,'first_zero_frame_preserved' if t==0 else 'not_rear_box') for t,p in other['pg'].items() if p['accepted']],training_ready=False);other_meta=dict(rear_waypoint_reconciliation=True,rear_waypoint_reconciliation_applied_frames=0)
 result=verify_complete_log(other,other_log,other_meta,task,frames=len(q));assert result['selected'] is False;branch_checks.append(dict(episode=ep.name,fixture_rows=len(q)))
 for p in [ep/'raw.npz',ep/'self_clearance.json']+([frp] if frp.exists() else []):sources[str(p)]=sha(p)
 # Wrong applied branch must fail even if the count is changed consistently.
 bad=copy.deepcopy(other_log);bad['rows'][-1]['applied']=True
 try:verify_complete_log(other,bad,dict(other_meta,rear_waypoint_reconciliation_applied_frames=1),task,frames=len(q))
 except AssertionError:pass
 else:raise AssertionError('nonselected branch admitted')
negative=[]
for label,change in [('missing_noop',lambda z:z['rows'].pop(1)),('duplicate_noop',lambda z:z['rows'].insert(1,copy.deepcopy(z['rows'][0]))),('reordered',lambda z:z['rows'].reverse()),('bad_zero_reason',lambda z:z['rows'][0].__setitem__('reason','not_rear_box')),('changed_current_action',lambda z:z['rows'][1].__setitem__('current_action_changed',True)),('nonboolean_applied',lambda z:z['rows'][1].__setitem__('applied',0)),('wrong_step_type',lambda z:z['rows'][0].__setitem__('step',False))]:
 bad=copy.deepcopy(log);change(bad)
 try:verify_complete_log(ctx,bad,meta,'push_box_to_bin',frames=len(ctx['q']))
 except AssertionError:negative.append(label)
 else:raise AssertionError('invalid log accepted '+label)
for label,bad in [('bad_metadata_count',dict(meta,rear_waypoint_reconciliation_applied_frames=meta['rear_waypoint_reconciliation_applied_frames']+1)),('disabled_metadata',dict(meta,rear_waypoint_reconciliation=False))]:
 try:verify_complete_log(ctx,log,bad,'push_box_to_bin',frames=len(ctx['q']))
 except AssertionError:negative.append(label)
 else:raise AssertionError(label)
for p in [Path(__file__),D/'independent_commit_log_contract.py',D/'independent_post_commit_audit.py',inputpath,urdf,ROOT/'simfoundry/calibration/sorting_station.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,rear_histories=results,unselected_branch_fixtures=branch_checks,negative_log_checks=negative,unselected_applied_rejections=3,source_sha256=sources,continuous_modified_replay=False,physics_started=False,training_ready=False)
with (D/'COMPLETE_COMMIT_LOG_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(passed=True,rear_fixture_rows=sum(x['fixture_event_rows'] for x in results),unselected_fixture_rows=sum(x['fixture_rows'] for x in branch_checks),negative_cases=len(negative)+3),flush=True)
