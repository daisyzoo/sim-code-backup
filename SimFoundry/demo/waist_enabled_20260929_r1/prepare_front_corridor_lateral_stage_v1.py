"""Isolated opt-in lateral corridor integration; no physical launch or admission."""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;P=W/'staged_joint_transport_reserve_v1';S=W/'staged_front_corridor_lateral_v1';D=W/'front_corridor_lateral_preparation_r1';C=W/'front_corridor_lateral_candidate_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
readiness=json.loads((C/'READINESS_REVIEW.json').read_text())
for p,h in readiness['source_sha256'].items():
 assert sha(p)==h
 for f,v in json.loads(Path(p).read_text())['source_sha256'].items():assert sha(f)==v
protocol=json.loads((W/'joint_transport_reserve_physical_r1/PROTOCOL.json').read_text())
S.mkdir(exist_ok=False);D.mkdir(exist_ok=False);copies={};edits={}
for p in P.iterdir():
 if not p.is_file() or not (p.suffix=='.py' or p.name in ['causal_response_parameters.json','elbow_torso_hulls.json']):continue
 assert protocol['frozen_files_sha256'][str(p)]==sha(p)
 (S/p.name).write_bytes(p.read_bytes());copies[p.name]=sha(p)
def replace(name,old,new):
 p=S/name;s=p.read_text();assert s.count(old)==1,(name,old[:100],s.count(old));p.write_text(s.replace(old,new));edits.setdefault(name,[]).append(dict(old=old,new=new))
name='front_corridor_midpoint_runtime.py';old=(S/name).read_text();new=(C/'selection.py').read_text();replace(name,old,new)
name='front_initial_center_route.py'
replace(name,'    corridor_midpoint_replan: bool = False\n','    corridor_midpoint_replan: bool = False\n    corridor_lateral_replan: bool = False\n')
replace(name,"        if type(self.corridor_midpoint_replan) is not bool:\n","        if type(self.corridor_lateral_replan) is not bool:\n            raise ValueError('corridor_lateral_replan must be bool')\n        if self.corridor_lateral_replan and not self.corridor_midpoint_replan:\n            raise ValueError('Lateral corridor requires original midpoint guards')\n        if type(self.corridor_midpoint_replan) is not bool:\n")
replace(name,'                parent_guard_reason=reason, prior_stop_reason=self.stop_reason)','                parent_guard_reason=reason, prior_stop_reason=self.stop_reason,\n                lateral_y_enabled=self.corridor_lateral_replan)')
name='collect_paired_sorting.py'
old="parser.add_argument('--front-corridor-midpoint-replan',action='store_true',help='Diagnostic midpoint recovery of an invalid front-X route; preserves original table/parcel/hand and latched guards; default off.')"
replace(name,old,old+"\nparser.add_argument('--front-corridor-lateral-replan',action='store_true',help='Diagnostic opt-in extension of midpoint checking to lateral_y; retains original guards and nominal path proofs.')")
old='if args.front_corridor_midpoint_replan and not (args.front_loaded_z_priority and args.front_initial_center_landing and args.front_diagonal_entry and args.front_micro_repair_retention):'
replace(name,old,"if args.front_corridor_lateral_replan and not (args.front_corridor_midpoint_replan and args.joint_transport_clearance and args.role=='diagnostic' and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):\n    parser.error('Lateral corridor requires diagnostic original midpoint and joint-transport protocol')\n"+old)
old="                            top_extra['corridor_midpoint_replan']=True"
replace(name,old,old+"\n                            if args.front_corridor_lateral_replan:\n                                top_extra['corridor_lateral_replan']=True")
replace(name,"phase='front_x_only',trigger='original_goal_violates_table_margin_and_positive_safe_interval'","phase='front_x_and_lateral_y' if args.front_corridor_lateral_replan else 'front_x_only',trigger='original_goal_violates_table_margin_and_positive_safe_interval'")
old="        episode.collect_meta['front_corridor_midpoint_replanned_frames']=sum(bool(r.get('front_corridor_midpoint',{}).get('changed')) for r in frontal_log)"
replace(name,old,old+"\n    if args.front_corridor_lateral_replan:\n        episode.collect_meta['front_corridor_lateral_replan']=True\n        episode.collect_meta['front_corridor_lateral_replanned_frames']=sum(bool(r.get('front_corridor_midpoint',{}).get('changed')) and r['front_corridor_midpoint']['route_stage']=='lateral_y' for r in frontal_log)")
for name,changes in edits.items():
 s=(S/name).read_text();ast.parse(s)
 for e in reversed(changes):assert s.count(e['new'])==1;s=s.replace(e['new'],e['old'],1)
 assert s==(P/name).read_text()
for name,h in copies.items():
 if name not in edits:assert sha(S/name)==h
manifest=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),stage=str(S),parent_files=copies,changed_files=edits,stage_sha256={p.name:sha(p) for p in S.iterdir() if p.is_file()},default_off=True,collector_wired=True,physics_started=False,training_ready=False,source_sha256={str(Path(__file__)):sha(__file__),str(C/'READINESS_REVIEW.json'):sha(C/'READINESS_REVIEW.json'),str(C/'selection.py'):sha(C/'selection.py')})
with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(manifest,f,indent=2)
print(json.dumps(dict(stage=str(S),files=len(copies),changed=list(edits),exact_parent_restoration=True),indent=2))
