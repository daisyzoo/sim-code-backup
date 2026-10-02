"""Prepare a default-off front-route interval candidate, not installed anywhere.
Only replace an infeasible extra-reserve X goal inside the original safe interval.
Original independent live guards and latched stops take precedence.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;parent=W/'staged_closed_peak_trial/front_top_route_micro.py';dest=W/'front_top_route_interval_candidate.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=parent.read_text();edits=[]
def replace(old,new):
 global s
 assert s.count(old)==1;s=s.replace(old,new);edits.append(dict(old=old,new=new))
replace('    recontact_on_route_change: bool = False\n','    corridor_interval_replan: bool = False\n    recontact_on_route_change: bool = False\n')
replace("        if type(self.retain_micro_repair_contact) is not bool:\n", "        if type(self.corridor_interval_replan) is not bool:\n            raise ValueError('corridor_interval_replan must be bool')\n        if type(self.retain_micro_repair_contact) is not bool:\n")
replace('        goal_x = min(self.route_x, required_x-.003)\n','''        goal_x = min(self.route_x, required_x-.003)
        interval_record = {}
        if self.corridor_interval_replan:
            # Preserve every existing live protection, including the parcel gap
            # that the original state machine checks immediately below.
            protected_gap_x = obstacle[0]-target[0]-other[0]-tr[0]
            protected_gap_y = abs(obstacle[1]-target[1])-other[1]-tr[1]
            protected = bool(reason or self.stop_reason or max(protected_gap_x,protected_gap_y)<.01)
            lower_x = .285+tr[0]
            original_goal_x = goal_x
            changed = False
            if not protected and not lower_x<=goal_x<=required_x and lower_x<required_x:
                goal_x = (lower_x+required_x)/2
                changed = True
            interval_record = dict(front_corridor_interval=dict(enabled=True,original_goal_x=float(original_goal_x),safe_interval_x=[float(lower_x),float(required_x)],protected=protected,changed=changed,goal_x=float(goal_x),table_margin_m=.005,parcel_planning_clearance_m=float(self.route_clearance_m)))
''')
replace('                        hand_obstacle_gap_m=hand_obstacle_gap_m)\n','                        hand_obstacle_gap_m=hand_obstacle_gap_m, **interval_record)\n')
replace('                    measured_front_gap_m=gap_x, route_stop_reason=None)\n','                    measured_front_gap_m=gap_x, route_stop_reason=None, **interval_record)\n')
ast.parse(s);back=s
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==parent.read_text();assert not dest.exists();dest.write_text(s)
manifest=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=str(parent),parent_sha256=sha(parent),candidate=str(dest),candidate_sha256=sha(dest),edits=edits,reverse_matches=True,default_off=True,runtime_installed=False,simulation_started=False,training_ready=False,scope=__doc__)
(W/'FRONT_CORRIDOR_INTERVAL_CANDIDATE_PREPARATION.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:v for k,v in manifest.items() if k!='edits'},indent=2))
