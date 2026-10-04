"""Prepare default-off right-rear early-edge diagnostic stage; no physics launch."""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;P=W/'staged_front_box_trailing_v2';C=W/'rear_early_edge_candidate_v1';S=W/'staged_rear_early_edge_v1';D=W/'rear_early_edge_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not S.exists() and not D.exists();S.mkdir();D.mkdir();parent={}
for p in P.iterdir():
 if p.is_file() and p.name!='COLLECTOR_PREPARATION.json':(S/p.name).write_bytes(p.read_bytes());parent[p.name]=sha(p)
for n in ['rear_cop_route_early.py','rear_early_edge_governor.py']:(S/n).write_bytes((C/n).read_bytes())
s=(P/'collect_paired_sorting.py').read_text();edits=[]
def replace(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new);edits.append(dict(old=old,new=new))
spec=dict(version='rear_box_early20_preserve_parent10_v1',enabled=True,side='right',rear_region_only=True,warning_inset_m=.020,original_cartesian_inset_m=.010,original_joint_edge_inset_m=.010,infeasible_fallback='complete_original_joint_XY_result',parent_z_unchanged=True,original_guard_priority=True,first_loaded_preserved=True,training_ready=False)
replace('STAGE = Path(__file__).resolve().parent\n', 'STAGE = Path(__file__).resolve().parent\nREAR_EARLY_EDGE_SPEC = '+repr(spec)+'\n')
replace("parser = argparse.ArgumentParser()\n", "parser = argparse.ArgumentParser()\nparser.add_argument('--rear-early-edge',action='store_true',help='Default-off right-rear Cartesian20mm warning with complete original10mm fallback; original joint edge and final guards retained.')\n")
marker='if args.rear_joint_xy_progress and not args.rear_coupled_progress:'
replace(marker,"if args.rear_early_edge and not (args.rear_joint_xy_progress and args.rear_box_inward_correction and args.precise_clearance_task_ik and args.edge_clearance_intersection and args.peak_load_bias_guard and args.trace_substep_contacts and args.role=='diagnostic' and not args.policy_port and not args.waist_probe and not args.idle):\n    parser.error('Rear early edge requires complete precision inward/edge-clearance/peak/substep diagnostic expert; no policy/probe/idle')\n"+marker)
marker='                        top_cls = RearCopRouteState\n'
replace(marker,marker+"                        if args.rear_early_edge and side=='right':\n                            from rear_cop_route_early import RearCopRouteState as EarlyRearCopRouteState\n                            top_cls = EarlyRearCopRouteState\n                            top_extra['rear_early_edge_enabled']=True\n                            frontal_plan['rear_early_edge']=dict(REAR_EARLY_EDGE_SPEC)\n")
marker="    # PEAK_LOAD_GUARD_BEGIN\n    if args.peak_load_bias_guard:\n        episode.collect_meta['peak_load_bias_guard']=True\n"
replace(marker,"    if args.rear_early_edge:\n        episode.collect_meta['rear_early_edge']=dict(REAR_EARLY_EDGE_SPEC)\n        episode.collect_meta['rear_early_edge_selected']=bool(frontal_plan is not None and frontal_plan.get('rear_early_edge',{}).get('enabled'))\n        episode.collect_meta['rear_early_edge_candidate_selected_frames']=sum(bool(r.get('rear_joint_xy_progress',{}).get('early_edge',{}).get('candidate_selected')) for r in frontal_log)\n"+marker)
marker="    if args.precise_clearance_task_ik:\n        paths.append(STAGE/'task_ik_precision.py')"
replace(marker,"    if args.rear_early_edge:\n        paths.extend(STAGE/name for name in ['rear_cop_route_early.py','rear_early_edge_governor.py'])\n"+marker)
(S/'collect_paired_sorting.py').write_text(s);ast.parse(s)
restored=s
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(P/'collect_paired_sorting.py').read_text()
for name,h in parent.items():assert sha(P/name)==h
changed=[n for n,h in parent.items() if sha(S/n)!=h];assert changed==['collect_paired_sorting.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=str(P),stage=str(S),scope=__doc__,spec=spec,parent_source_sha256=parent,stage_sha256={p.name:sha(p) for p in S.iterdir() if p.is_file()},collector_edits=edits,only_existing_file_changed='collect_paired_sorting.py',new_helpers=['rear_cop_route_early.py','rear_early_edge_governor.py'],reverse_edits_restore_parent_bytes=True,source_sha256={str(p):sha(p) for p in [Path(__file__),C/'NATIVE_JOINT_READINESS_REVIEW_V4.json',C/'NATIVE_LOADED_BOUT_JOINT_REPLAY_V4.json']},collector_wiring_verified=False,audit_family_ready=False,physics_started=False,training_ready=False)
with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
with (D/'STAGE_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(stage=str(S),parent_files=len(parent),changed=changed,added=out['new_helpers'],physics_started=False)))
