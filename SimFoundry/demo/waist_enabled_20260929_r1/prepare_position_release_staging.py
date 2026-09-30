"""Build isolated source candidates; never edit running controller files."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent;repo=root.parents[1]
protocol=json.loads((root/'projected_hysteresis_mirror1200_r1/PROTOCOL.json').read_text())
for p,h in protocol['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
out=root/'staged_position_release';out.mkdir(exist_ok=True)
p=repo/'simfoundry/data/top_contact_bypass.py';original=p.read_text();s=original
s=s.replace('    recontact_travel_z: float=.91\n','    recontact_travel_z: float=.91\n    confirm_terminal_release: bool=False\n    position_release_monitor: object|None=None\n    release_reason: str|None=None\n',1)
s=s.replace("        if self.top_mode is None:\n", "        if self.confirm_terminal_release and not (self.guarded_descent and self.continuous_drag):\n            raise ValueError('Confirmed release requires guarded continuous top route')\n        if self.top_mode is None:\n",1)
s=s.replace("        direction=self.rear.plan['direction']\n", """        direction=self.rear.plan['direction']
        position_ready=False
        if self.confirm_terminal_release:
            from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease
            if self.position_release_monitor is None:
                self.position_release_monitor=ConfirmedPositionRelease(self.rear.plan['initial_target_xyz'][1],direction)
            position_ready=self.position_release_monitor.observe(target)
        guarded_this_step=False
""",1)
s=s.replace("            self.contact_rear_shift_m=min(.03,self.contact_rear_shift_m+.01)", "            guarded_this_step=True\n            self.contact_rear_shift_m=min(.03,self.contact_rear_shift_m+.01)",1)
s=s.replace("            if edge_close or tilt>.03:self._start_recontact(tip,'loaded_edge_margin' if edge_close else 'incipient_tilt')", "            if edge_close or tilt>.03:\n                guarded_this_step=True\n                self._start_recontact(tip,'loaded_edge_margin' if edge_close else 'incipient_tilt')",1)
s=s.replace('        travel_z=self.recontact_travel_z if self.recontacts else .91', """        if position_ready and not guarded_this_step and self.top_mode in ('top_lift','top_cross','top_descend','top_press','top_push'):
            self.top_mode='top_release';self.mode_step=0;self.release=tuple(tip)
            self.release_reason='confirmed_original_target_position'
        travel_z=self.recontact_travel_z if self.recontacts else .91""",1)
s=s.replace("                self.top_mode='top_release';self.mode_step=0;self.release=tuple(tip)", "                self.top_mode='top_release';self.mode_step=0;self.release=tuple(tip);self.release_reason='original_margin'",1)
s=s.replace("        return dict(hand_obstacle_gap_m=", "        return dict(terminal_position_confirmed=position_ready,release_reason=self.release_reason,hand_obstacle_gap_m=",1)
assert s!=original;compile(s,str(p),'exec');(out/'top_contact_bypass.py').write_text(s)
helper=(root/'confirmed_position_release_candidate.py').read_text();(out/'confirmed_position_release.py').write_text(helper)
p=repo/'scripts/collect_paired_sorting.py';c=p.read_text();base=c
line="parser.add_argument('--expert-top-confirmed-release', action='store_true', help='Diagnostic guarded top route: release after ten measured frames satisfy original target position/stability conditions; all original safety/quality gates retained.')\n"
c=c.replace("parser.add_argument('--expert-front-recontact-z'",line+"parser.add_argument('--expert-front-recontact-z'",1)
c=c.replace('if not .84 <= args.expert_front_recontact_z <= .91:', "if args.expert_top_confirmed_release and not (args.role=='diagnostic' and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag):\n    parser.error('Confirmed top release requires explicit projected guarded continuous diagnostic route')\nif not .84 <= args.expert_front_recontact_z <= .91:",1)
c=c.replace('frontal_state = top_cls(frontal_state,side,contact_size,**top_extra,', 'frontal_state = top_cls(frontal_state,side,contact_size,**top_extra,confirm_terminal_release=args.expert_top_confirmed_release,',1)
c=c.replace('                top_cls, top_extra = TopContactBypassState, {}', "                frontal_plan['confirmed_terminal_release'] = dict(enabled=args.expert_top_confirmed_release,zone_y_m=.20,min_progress_m=.15,consecutive_frames=10,max_endpoint_xy_m=.01,keeps_original_release=True,guard_precedence=True)\n                top_cls, top_extra = TopContactBypassState, {}",1)
c=c.replace("    paths.append(ROOT / 'simfoundry/data/object_relative_push.py')", "    paths.append(ROOT / 'simfoundry/data/object_relative_push.py')\n    paths.append(ROOT / 'simfoundry/data/confirmed_position_release.py')",1)
assert c!=base;compile(c,str(p),'exec');(out/'collect_paired_sorting.py').write_text(c)
(out/'MANIFEST.json').write_text(json.dumps(dict(frozen_parent_protocol_sha256=hashlib.sha256((root/'projected_hysteresis_mirror1200_r1/PROTOCOL.json').read_bytes()).hexdigest(),source_sha256={p:h for p,h in protocol['source_sha256'].items()},candidate_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.py')},scope='Isolated source candidates only; running files unchanged. Await full mirror review before any integration/physical test.',training_ready=False),indent=2))
print(out)
