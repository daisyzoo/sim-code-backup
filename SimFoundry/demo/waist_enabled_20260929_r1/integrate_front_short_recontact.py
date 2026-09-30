"""Register optional shorter front-route recovery after frozen batch review."""
from pathlib import Path
import json,hashlib

work=Path(__file__).resolve().parent;root=work.parents[1]
prior=work/'projected_object_relative_r1'
assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert not Path('/proc/4052617').exists()
assert json.loads((prior/'TERMINAL_SOURCE_VERIFICATION.json').read_text())['verified_at_utc']
audits=json.loads((prior/'AUDIT_EXECUTION.json').read_text())
assert len(audits)==9 and all(a['returncode']==0 for a in audits)
review=json.loads((prior/'COMPLETE_GROUP_READINESS.json').read_text())
assert len(review['rows'])==4 and all(r['actual_visual_review_bound'] for r in review['rows'])
for name,digest in json.loads((prior/'PROTOCOL.json').read_text())['source_sha256'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
changes={}
p=root/'simfoundry/data/top_contact_bypass.py';s=p.read_text()
needle='    recovery_clearance_m: float=0.\n';assert s.count(needle)==1
s=s.replace(needle,needle+'    recontact_travel_z: float=.91\n')
needle="        if not math.isfinite(self.forward_margin_m)"
at=s.index(needle)
s=s[:at]+"""        if not math.isfinite(self.recontact_travel_z) or not .84<=self.recontact_travel_z<=.91:
            raise ValueError('Recontact travel height must be0.84..0.91m')
        if self.recontact_travel_z!=.91 and (not self.guarded_descent or not self.continuous_drag or self.recovery_clearance_m):
            raise ValueError('Short recontact requires guarded continuous drag without another recovery height mode')
"""+s[at:]
needle='        travel_z=.91\n';assert s.count(needle)==1
s=s.replace(needle,'        travel_z=self.recontact_travel_z if self.recontacts else .91\n')
needle="                self._start_recontact(tip,'lost_contact')\n";assert s.count(needle)==1
s=s.replace(needle,needle+"                if self.recontact_travel_z != .91:\n                    travel_z=self.recontact_travel_z\n")
changes[p]=s
p=root/'scripts/collect_paired_sorting.py';s=p.read_text()
at=s.index("parser.add_argument('--expert-front-object-relative-lead'")
s=s[:at]+"parser.add_argument('--expert-front-recontact-z', type=float, default=.91, help='Diagnostic front route only: recovery travel height after lost contact; initial approach remains0.91m. Bound0.84..0.91m, original guards retained.')\n"+s[at:]
at=s.index('if args.expert_front_object_relative_lead and')
s=s[:at]+"""if not .84 <= args.expert_front_recontact_z <= .91:
    parser.error('Front recontact Z must be0.84..0.91m')
if args.expert_front_recontact_z != .91 and not (args.expert_front_top_route and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag):
    parser.error('Short front recontact requires projected, guarded, continuous front diagnostic')
"""+s[at:]
needle='object_relative_lead=args.expert_front_object_relative_lead)';assert s.count(needle)==1
s=s.replace(needle,'object_relative_lead=args.expert_front_object_relative_lead,recontact_travel_z=args.expert_front_recontact_z)')
needle='object_relative_lead_limit_m=.012 if args.expert_front_object_relative_lead else None)';assert s.count(needle)==1
s=s.replace(needle,'object_relative_lead_limit_m=.012 if args.expert_front_object_relative_lead else None,recontact_travel_z=args.expert_front_recontact_z,initial_travel_z=.91)')
changes[p]=s
p=root/'tests/test_front_short_recontact.py'
changes[p]='''import unittest
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState,frontal_bypass_plan
Q=(0.,0.,0.,1.)
class FrontShortRecontactTests(unittest.TestCase):
    def state(self,z=.86):
        plan=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),0.,0.,-1)
        return FrontTopRouteState(FrontalBypassState(plan),'right',(.14,.09,.045),guarded_descent=True,continuous_drag=True,recontact_travel_z=z)
    def call(self,s,load=5.,gap=.1,tip=(.35,.12,.795)):
        return s.update(tip,(.4,.12,.7725),(.55,-.12,.77),.07,.075,tip=tip,quat=Q,obstacle_quat=Q,control_offset_local=(.2,0,0),load_n=load,hand_obstacle_gap_m=gap)
    def test_initial_approach_is_unchanged(self):
        self.assertEqual(self.call(self.state())['target_xyz'][2],.91)
    def test_recovery_height_only_after_three_lost_load_frames(self):
        s=self.state();self.call(s);s.top_mode='top_push';s.command=(.35,.12,.795)
        for _ in range(2): self.assertEqual(self.call(s,load=0.)['mode'],'top_push')
        r=self.call(s,load=0.);self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['target_xyz'][2],.86)
        self.assertEqual(r['recontacts'],1)
    def test_default_recovery_remains_point91(self):
        s=self.state(.91);self.call(s);s.top_mode='top_push';s.command=(.35,.12,.795)
        for _ in range(3):r=self.call(s,load=0.)
        self.assertEqual(r['target_xyz'][2],.91)
    def test_emergency_lift_remains_point91(self):
        s=self.state();self.call(s);s.recontacts=1
        r=self.call(s,gap=.004);self.assertEqual(r['mode'],'front_guard_lift');self.assertGreaterEqual(r['target_xyz'][2],.91)
    def test_no_downward_lift_if_already_above_recovery_height(self):
        s=self.state();self.call(s);s._start_recontact((.35,.12,.88),'lost_contact')
        r=self.call(s,tip=(.35,.12,.80));self.assertGreaterEqual(r['target_xyz'][2],.88)
    def test_invalid_and_unguarded_short_recovery_rejected(self):
        for z in (.83,.92,float('nan')):
            with self.assertRaises(ValueError):self.call(self.state(z))
        s=self.state();s.guarded_descent=False
        with self.assertRaises(ValueError):self.call(s)
if __name__=='__main__':unittest.main()
'''
for p,s in changes.items():compile(s,str(p),'exec')
for p,s in changes.items():p.write_text(s)
(work/'FRONT_SHORT_RECONTACT_INTEGRATION.json').write_text(json.dumps(dict(source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in changes},prior_complete_visual_review_verified=True,training_ready=False),indent=2))
print('Integrated optional shorter recovery; tests required before diagnostic run')
