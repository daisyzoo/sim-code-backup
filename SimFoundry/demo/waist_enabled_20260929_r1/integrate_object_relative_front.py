"""Apply explicit candidate only after the complete frozen run and audits finish."""
import hashlib
import json
from pathlib import Path

work=Path(__file__).resolve().parent
root=work.parents[1]
prior=work/'projected_confirmed_clearance_long_r1'
assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert not Path('/proc/3873613').exists()
assert json.loads((prior/'TERMINAL_SOURCE_VERIFICATION.json').read_text())['verified_at_utc']
audits=json.loads((prior/'AUDIT_EXECUTION.json').read_text())
assert len(audits)==9 and all(a['returncode']==0 for a in audits)
protocol=json.loads((prior/'PROTOCOL.json').read_text())
for name,digest in protocol['source_sha256'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
assert (prior/'COMPLETE_GROUP_READINESS.json').exists()
changes={}
p=root/'simfoundry/data/front_top_route.py'
s=p.read_text()
needle='    confirm_nominal_clearance: bool = False\n'
assert s.count(needle)==1
s=s.replace(needle,needle+'    object_relative_lead: bool = False\n    relative_contact_anchor: tuple | None = None\n')
needle="        if row['mode'] == 'top_push':\n"
assert s.count(needle)==1
s=s.replace(needle,"        if row['mode'] != 'top_push':\n            self.relative_contact_anchor = None\n"+needle)
needle="            self.command = (*xy, row['target_xyz'][2])\n"
assert s.count(needle)==1
s=s.replace(needle,"""            if self.object_relative_lead:
                from simfoundry.data.object_relative_push import object_relative_push_xy
                if self.relative_contact_anchor is None:
                    self.relative_contact_anchor = tuple(tip[i]-target[i] for i in (0,1))
                xy, desired_xy = object_relative_push_xy(target[:2], self.relative_contact_anchor,
                    (goal_x, goal_y), base[:2], step_m=self.drag_step_m)
                row['object_relative_contact_anchor_xy_m'] = self.relative_contact_anchor
                row['object_relative_desired_xy_m'] = desired_xy
                row['object_relative_lead_limit_m'] = .012
"""+needle)
changes[p]=s
p=root/'scripts/collect_paired_sorting.py';s=p.read_text()
needle="parser.add_argument('--expert-front-confirm-nominal-clearance'"
at=s.index(needle)
s=s[:at]+"parser.add_argument('--expert-front-object-relative-lead', action='store_true', help='Diagnostic front route: latch contact reference offset per acquisition and bound desired XY lead relative to observed object, retaining3mm slew and original guards.')\n"+s[at:]
at=s.index('if args.expert_front_confirm_nominal_clearance and')
s=s[:at]+"if args.expert_front_object_relative_lead and not (args.expert_front_top_route and args.expert_top_projected_support):\n    parser.error('Object-relative front lead requires explicit front route and projected support diagnostic')\n"+s[at:]
needle='confirm_nominal_clearance=args.expert_front_confirm_nominal_clearance)'
assert s.count(needle)==1
s=s.replace(needle,'confirm_nominal_clearance=args.expert_front_confirm_nominal_clearance,object_relative_lead=args.expert_front_object_relative_lead)')
needle='nominal_clearance_confirmation_frames=3 if args.expert_front_confirm_nominal_clearance else None)'
assert s.count(needle)==1
s=s.replace(needle,'nominal_clearance_confirmation_frames=3 if args.expert_front_confirm_nominal_clearance else None,object_relative_lead=args.expert_front_object_relative_lead,object_relative_lead_limit_m=.012 if args.expert_front_object_relative_lead else None)')
needle="paths.extend([ROOT / 'simfoundry/data/front_top_route.py', ROOT / 'simfoundry/data/tabletop_route_candidates.py'])"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n    paths.append(ROOT / 'simfoundry/data/object_relative_push.py')")
changes[p]=s
for p,s in changes.items(): compile(s,str(p),'exec')
for p,s in changes.items(): p.write_text(s)
(work/'OBJECT_RELATIVE_FRONT_INTEGRATION.json').write_text(json.dumps(dict(source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in changes},prior_terminal_source_verified=True,training_ready=False),indent=2))
print('Integrated explicit object-relative front candidate; regression tests required before running.')
