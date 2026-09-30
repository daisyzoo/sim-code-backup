"""Apply optional hysteresis only after the complete prior frozen run is reviewed."""
from pathlib import Path
import json,hashlib
work=Path(__file__).resolve().parent;root=work.parents[1];prior=work/'projected_short_recontact_r1'
assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert not Path('/proc/4181161').exists()
assert json.loads((prior/'TERMINAL_SOURCE_VERIFICATION.json').read_text())['verified_at_utc']
a=json.loads((prior/'AUDIT_EXECUTION.json').read_text());assert len(a)==9 and all(x['returncode']==0 for x in a)
r=json.loads((prior/'COMPLETE_GROUP_READINESS.json').read_text());assert len(r['rows'])==4 and all(x['actual_visual_review_bound'] for x in r['rows'])
for p,h in json.loads((prior/'PROTOCOL.json').read_text())['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
changes={}
p=root/'simfoundry/data/front_clearance_progress.py';s=Path('/tmp/front_clearance_hysteresis_candidate.py').read_text().replace('Offline hysteresis candidate only; not wired to active collector.','Observed clearance stage logic with optional bounded hysteresis.');changes[p]=s
p=root/'simfoundry/data/front_top_route.py';s=p.read_text();needle='    confirm_nominal_clearance: bool = False\n';assert s.count(needle)==1;s=s.replace(needle,needle+'    recovery_hysteresis_m: float = 0.\n')
needle="        if not math.isfinite(hand_obstacle_gap_m):";assert s.count(needle)==1;s=s.replace(needle,"        if self.recovery_hysteresis_m and not self.recover_clearance:\n            raise ValueError('Hysteresis requires explicit front clearance recovery')\n"+needle)
needle='confirm_nominal_clearance=self.confirm_nominal_clearance)';assert s.count(needle)==1;s=s.replace(needle,'confirm_nominal_clearance=self.confirm_nominal_clearance,recovery_hysteresis_m=self.recovery_hysteresis_m)');changes[p]=s
p=root/'scripts/collect_paired_sorting.py';s=p.read_text();at=s.index("parser.add_argument('--expert-front-recontact-z'");s=s[:at]+"parser.add_argument('--expert-front-recovery-hysteresis-m', type=float, default=0., help='Diagnostic front recovery hysteresis0..1mm. Initial/resume nominal clearance unchanged; recovery threshold remains>=11mm and original10mm emergency guard remains.')\n"+s[at:]
at=s.index('if not .84 <= args.expert_front_recontact_z');s=s[:at]+"if not 0 <= args.expert_front_recovery_hysteresis_m <= .001 or (args.expert_front_recovery_hysteresis_m and not args.expert_front_recover_clearance):\n    parser.error('Front hysteresis0..1mm requires explicit clearance recovery')\n"+s[at:]
needle='recontact_travel_z=args.expert_front_recontact_z)';assert s.count(needle)==1;s=s.replace(needle,'recontact_travel_z=args.expert_front_recontact_z,recovery_hysteresis_m=args.expert_front_recovery_hysteresis_m)')
needle='initial_travel_z=.91)';assert s.count(needle)==1;s=s.replace(needle,'initial_travel_z=.91,recovery_hysteresis_m=args.expert_front_recovery_hysteresis_m,recovery_trigger_clearance_m=args.expert_front_clearance_m-args.expert_front_recovery_hysteresis_m)');changes[p]=s
p=root/'tests/test_front_clearance_hysteresis.py';s=Path('/tmp/test_front_clearance_hysteresis_candidate.py').read_text().replace('from front_clearance_hysteresis_candidate import','from simfoundry.data.front_clearance_progress import');at=s.index("if __name__=='__main__'")
s=s[:at]+'''from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState,frontal_bypass_plan
class HalfMillimeterIntegrationTests(unittest.TestCase):
 def test_observed_band_then_recovery_and_original_emergency(self):
  plan=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),0.,0.,-1)
  s=FrontTopRouteState(FrontalBypassState(plan),'right',(.14,.09,.045),guarded_descent=True,continuous_drag=True,route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005)
  def call(x,y=.12):
   tip=(.35,y,.795)
   return s.update(tip,(x,y,.7725),(.55,-.12,.77),.07,.075,tip=tip,quat=(0,0,0,1),obstacle_quat=(0,0,0,1),control_offset_local=(.2,0,0),load_n=5.,hand_obstacle_gap_m=.1)
  call(.4)
  for _ in range(3):r=call(.3929)
  self.assertEqual(r['route_stage'],'lateral_y')
  self.assertEqual(call(.3934,-.04)['route_stage'],'lateral_y')
  r=call(.3936,-.05);self.assertEqual(r['route_stage'],'front_x')
  self.assertAlmostEqual(r['clearance_progress']['front_hold_y'],-.05)
  self.assertAlmostEqual(r['clearance_progress']['recover_clearance_m'],.0115)
  self.assertEqual(call(.3951,-.05)['route_stop_reason'],'parcel_clearance_10mm')
 def test_half_millimeter_boundary_requires_original_confirmation(self):
  s=FrontClearanceProgress(.012,.12,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005)
  for _ in range(3):s.update(.0121,.12)
  self.assertEqual(s.update(.0116,.0)['route_stage'],'lateral_y')
  self.assertEqual(s.update(.0114,.0)['route_stage'],'front_x')
  for _ in range(20):self.assertEqual(s.update(.0119,.0)['route_stage'],'front_x')
  for _ in range(2):self.assertEqual(s.update(.0121,.0)['route_stage'],'front_x')
  self.assertEqual(s.update(.0121,.0)['route_stage'],'lateral_y')
'''+s[at:];changes[p]=s
p=work/'audit_recovery_and_anchor.py';s=p.read_text();needle="elif stage=='lateral_y' and gap<clear:";assert s.count(needle)==1;s=s.replace(needle,"elif stage=='lateral_y' and gap<clear-guards.get('recovery_hysteresis_m',0.):");changes[p]=s
for p,s in changes.items():compile(s,str(p),'exec')
for p,s in changes.items():p.write_text(s)
(work/'FRONT_CLEARANCE_HYSTERESIS_INTEGRATION.json').write_text(json.dumps(dict(source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in changes},prior_complete_visual_review_verified=True,training_ready=False),indent=2));print('Integrated bounded hysteresis; tests required before running')
