"""Wire one default-off geometric feedback option in an isolated stage."""
from pathlib import Path
import json,hashlib,ast
w=Path(__file__).resolve().parent;parent=w/'staged_rear_cop_measured_bounds';probe=w/'staged_rear_cop_core_slice_probe';dst=w/'staged_rear_cop_core_slice';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((parent/'MANIFEST.json').read_text());check=json.loads((probe/'CHECK.json').read_text());assert check['passed'] and check['candidate_sha256']==sha(probe/'rear_cop_centering.py')
for n,h in m['source_sha256'].items():assert sha(parent/n)==h
dst.mkdir(exist_ok=False)
for n in m['source_sha256']:(dst/n).write_bytes((parent/n).read_bytes())
(dst/'rear_cop_centering.py').write_bytes((probe/'rear_cop_centering.py').read_bytes())
p=dst/'rear_cop_route.py';s=p.read_text();s=s.replace('    rear_cop_enabled: bool = False','    rear_core_slice_enabled: bool = False\n    rear_cop_enabled: bool = False');old="        previous_xy = self.last_waypoint_xy";new="""        if type(self.rear_core_slice_enabled) is not bool:
            raise ValueError('rear_core_slice_enabled must be bool')
        if self.rear_core_slice_enabled and not self.rear_cop_enabled:
            raise ValueError('Core slice requires rear COP')
        self.rear_cop.core_slice_feedback = self.rear_core_slice_enabled
        previous_xy = self.last_waypoint_xy""";assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
p=dst/'collect_paired_sorting.py';s=p.read_text()
def replace(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
replace("parser.add_argument('--rear-cop-centering',", "parser.add_argument('--rear-core-slice-feedback', action='store_true', help='Diagnostic rotated-core world-X COP error; requires rear COP.')\nparser.add_argument('--rear-cop-centering',")
replace('args = parser.parse_args()', "args = parser.parse_args()\nif args.rear_core_slice_feedback and not args.rear_cop_centering:\n    parser.error('Rear core slice requires rear COP centering')")
replace("top_extra.update(rear_cop_enabled=True, rear_cop_core_size=tuple(actual_core['collision_core_size_xyz']))", "top_extra.update(rear_cop_enabled=True, rear_cop_core_size=tuple(actual_core['collision_core_size_xyz']), rear_core_slice_enabled=args.rear_core_slice_feedback)")
needle="                    region_approach = RegionApproachLifecycle(**region_extra)"
replace(needle,"                    if args.rear_core_slice_feedback:\n                        frontal_plan['rear_cop_centering']['core_slice_feedback']=True\n"+needle)
p.write_text(s)
for p in dst.glob('*.py'):ast.parse(p.read_text())
unchanged=[n for n in m['source_sha256'] if n not in ['collect_paired_sorting.py','rear_cop_route.py','rear_cop_centering.py']]
for n in unchanged:assert sha(dst/n)==m['source_sha256'][n]
report=dict(parent_manifest_sha256=sha(parent/'MANIFEST.json'),probe_check_sha256=sha(probe/'CHECK.json'),source_sha256={n:sha(dst/n) for n in m['source_sha256']},unchanged_parent_helpers=unchanged,default_off=True,collector_wired_in_source=True,cli_checked=False,lifecycle_checked=False,auditor_checked=False,physical_started=False,training_ready=False,scope='Only optional loaded rear COP error geometry changes; original feedforward/YZ/first-loaded and guards remain. No new archive filenames,55 source archive entries expected. Frozen production/parent unchanged. Must finish CLI,actual collector and lifecycle wiring,independent audits before physics.')
(dst/'PREPARATION.json').write_text(json.dumps(report,indent=2));print(dst)
