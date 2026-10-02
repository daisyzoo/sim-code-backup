"""Isolated front corridor diagnostic stage; no simulator is started.
Parent matches the frozen peak-load expert; joint-edge repair is not combined.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'staged_peak_load_guard';S=W/'staged_front_corridor_interval';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((W/'fresh_closed_peak_trials_r1/PROTOCOL.json').read_text());cand=json.loads((W/'FRONT_CORRIDOR_INTERVAL_CANDIDATE_PREPARATION.json').read_text());check=json.loads((W/'FRONT_CORRIDOR_INTERVAL_CANDIDATE_CHECK.json').read_text());assert check['passed'] and check['rows']==8393 and check['changed_rows']==3;assert sha(cand['candidate'])==cand['candidate_sha256'];assert sha(P/'front_top_route_micro.py')==cand['parent_sha256']
assert not S.exists();sources={}
for p in P.iterdir():
 if p.is_file() and (p.suffix=='.py' or p.name in ['causal_response_parameters.json','elbow_torso_hulls.json']):
  assert sha(p)==protocol['frozen_files_sha256'][str(p)];sources[p.name]=sha(p)
s=(P/'collect_paired_sorting.py').read_text();edits=[]
def replace(old,new):
 global s
 assert s.count(old)==1;s=s.replace(old,new);edits.append(dict(old=old,new=new))
replace('parser = argparse.ArgumentParser()\n',"parser = argparse.ArgumentParser()\nparser.add_argument('--front-corridor-interval',action='store_true',help='Diagnostic feasible front-goal interval; original live guards retained, default off.')\n")
replace('args = parser.parse_args()\n',"""args = parser.parse_args()
if args.front_corridor_interval and not (args.role=='diagnostic' and args.expert_front_top_route and args.front_micro_repair_retention and args.front_diagonal_entry and args.front_direction_recontact and args.front_cop_slip_following and args.self_clearance_task_ik and args.trace_substep_contacts and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):
    parser.error('Front interval requires original diagnostic front+micro+COP+clearance+substep setup; no policy/pilot.')
""")
marker="                            top_extra['retain_micro_repair_contact'] = True\n"
replace(marker,marker+"""                            if args.front_corridor_interval:
                                top_extra['corridor_interval_replan'] = True
                                frontal_plan['front_corridor_interval'] = dict(enabled=True,table_margin_m=.005,parcel_planning_clearance_m=args.expert_front_clearance_m,original_extra_reserve_m=.003,proposal='midpoint_only_when_original_infeasible',original_live_guards=True,latched_stop_preserved=True,training_ready=False)
""")
marker="    if args.rear_box_inward_correction:\n        episode.collect_meta['rear_box_inward_correction']=True\n"
replace(marker,marker+"    if args.front_corridor_interval:\n        episode.collect_meta['front_corridor_interval']=True\n")
ast.parse(s);back=s
for e in reversed(edits):back=back.replace(e['new'],e['old'])
assert back==(P/'collect_paired_sorting.py').read_text();S.mkdir()
for name in sources:(S/name).write_bytes((P/name).read_bytes())
(S/'collect_paired_sorting.py').write_text(s);(S/'front_top_route_micro.py').write_bytes(Path(cand['candidate']).read_bytes())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=str(P),stage=str(S),parent_source_sha256=sources,stage_sha256={p.name:sha(p) for p in S.iterdir() if p.is_file()},collector_edits=edits,front_component_preparation_sha256=sha(W/'FRONT_CORRIDOR_INTERVAL_CANDIDATE_PREPARATION.json'),front_component_check_sha256=sha(W/'FRONT_CORRIDOR_INTERVAL_CANDIDATE_CHECK.json'),reverse_collector_matches=True,default_off=True,joint_edge_repair_combined=False,simulation_started=False,training_ready=False,scope=__doc__)
(S/'PREPARATION.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['parent_source_sha256','stage_sha256','collector_edits']},indent=2))
