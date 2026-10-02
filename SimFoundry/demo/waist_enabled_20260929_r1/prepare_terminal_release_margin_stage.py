"""Isolate existing release-margin confirmation on the closed6/8 edge baseline.
Reject the regressed forced-corridor branch as the parent for this experiment.
No data admission or physical launch; all original quality criteria unchanged.
"""
from pathlib import Path
import json,hashlib,ast,datetime
W=Path(__file__).resolve().parent;A=W/'staged_joint_edge_clearance_intersection';B=W/'staged_terminal_release_margin';assert not B.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();parent=json.loads((A/'PREPARATION.json').read_text());result=json.loads((W/'joint_edge_intersection_physical_r1/RESULT_WITH_SUPPLEMENT.json').read_text());assert result['conditions']==10 and result['push_passed']==6 and result['wait_passed']==2 and not result['training_ready'];check=json.loads((W/'CONFIRMED_RELEASE_MARGIN_HISTORY_CHECK.json').read_text());assert check['passed'] and check['episodes']==56
for n,h in parent['stage_sha256'].items():assert sha(A/n)==h,n
s=(A/'collect_paired_sorting.py').read_text();edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b);edits.append(dict(old=a,new=b))
a="parser.add_argument('--edge-clearance-intersection',action='store_true',help='Diagnostic original final edge command with joint elbow-clearance constraints; default off.')"
edit(a,a+"\nparser.add_argument('--terminal-release-margin',action='store_true',help='Diagnostic confirmed release also requires existing5mm zone/10mm progress margins; default off.')")
a="if args.edge_clearance_intersection and not ("
edit(a,"if args.terminal_release_margin and not (args.role=='diagnostic' and args.expert_top_confirmed_release and not args.policy_port and not args.waist_pilot_contract):\n    raise ValueError('Release margin requires existing diagnostic confirmed-release protocol')\n"+a)
a="                frontal_state.load.desired_n=args.expert_frontal_top_load_n"
edit(a,"                if args.terminal_release_margin:\n                    from margin_confirmed_position_release import ConfirmedPositionRelease\n                    frontal_state.position_release_monitor=ConfirmedPositionRelease(frontal_state.rear.plan['initial_target_xyz'][1],frontal_state.rear.plan['direction'])\n                    frontal_plan['confirmed_release_margin']=dict(enabled=True,zone_m=.205,minimum_progress_m=.16,original_confirmation_window=10,original_window_xy_m=.01,quality_thresholds_unchanged=True)\n"+a)
a="    if args.edge_clearance_intersection:\n        episode.collect_meta['edge_clearance_intersection']=True"
edit(a,a+"\n    if args.terminal_release_margin:\n        episode.collect_meta['terminal_release_margin']=True\n        episode.collect_meta['terminal_release_zone_m']=.205\n        episode.collect_meta['terminal_release_progress_m']=.16")
a='    for path in paths:\n';edit(a,"    if args.terminal_release_margin:\n        paths.append(STAGE/'margin_confirmed_position_release.py')\n"+a)
back=s
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(A/'collect_paired_sorting.py').read_text();ast.parse(s);B.mkdir()
for n in parent['stage_sha256']:(B/n).write_bytes((A/n).read_bytes())
(B/'collect_paired_sorting.py').write_text(s);(B/'margin_confirmed_position_release.py').write_bytes((W/'margin_confirmed_position_release.py').read_bytes())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_stage=str(A),parent_preparation_sha256=sha(A/'PREPARATION.json'),parent_closed_result_sha256=sha(W/'joint_edge_intersection_physical_r1/RESULT_WITH_SUPPLEMENT.json'),history_check_sha256=sha(W/'CONFIRMED_RELEASE_MARGIN_HISTORY_CHECK.json'),edits=edits,new_helpers=['margin_confirmed_position_release.py'],stage_sha256={p.name:sha(p) for p in B.iterdir() if p.is_file()},simulation_started=False,training_ready=False,remaining='Actual parser/initialization selection, independent current-observation terminal audit, source/original audit adapters, full fixed10 physics. Recovery progress gate not combined.')
(B/'PREPARATION.json').write_text(json.dumps(report,indent=2));print('prepared',len(report['stage_sha256']),'files')
