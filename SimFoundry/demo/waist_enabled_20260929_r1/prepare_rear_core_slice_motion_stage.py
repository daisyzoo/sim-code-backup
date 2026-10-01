"""Add only default-off measured slice-motion feedforward to frozen core-slice."""
from pathlib import Path
import json,hashlib,ast
w=Path(__file__).resolve().parent;parent=w/'staged_rear_cop_core_slice';probe=w/'staged_rear_core_slice_motion_probe';dst=w/'staged_rear_core_slice_motion';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((parent/'MANIFEST.json').read_text());check=json.loads((probe/'CHECK.json').read_text());assert check['passed'] and check['candidate_sha256']==sha(probe/'rear_cop_centering.py')
for n,h in m['source_sha256'].items():assert sha(parent/n)==h
dst.mkdir(exist_ok=False)
for n in m['source_sha256']:(dst/n).write_bytes((parent/n).read_bytes())
(dst/'rear_cop_centering.py').write_bytes((probe/'rear_cop_centering.py').read_bytes())
p=dst/'rear_cop_route.py';s=p.read_text();needle='    rear_core_slice_enabled: bool = False';assert s.count(needle)==1;s=s.replace(needle,'    rear_core_slice_motion_enabled: bool = False\n'+needle);needle='        self.rear_cop.core_slice_feedback = self.rear_core_slice_enabled';assert s.count(needle)==1;s=s.replace(needle,"""        if type(self.rear_core_slice_motion_enabled) is not bool:
            raise ValueError('rear_core_slice_motion_enabled must be bool')
        if self.rear_core_slice_motion_enabled and not self.rear_core_slice_enabled:
            raise ValueError('Core slice motion requires core slice feedback')
        self.rear_cop.core_slice_motion_feedforward = self.rear_core_slice_motion_enabled
"""+needle);p.write_text(s)
p=dst/'collect_paired_sorting.py';s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace("parser.add_argument('--rear-core-slice-feedback',", "parser.add_argument('--rear-core-slice-motion-feedforward', action='store_true', help='Diagnostic measured core slice X motion feedforward; requires core slice feedback.')\nparser.add_argument('--rear-core-slice-feedback',")
replace('args = parser.parse_args()',"args = parser.parse_args()\nif args.rear_core_slice_motion_feedforward and not args.rear_core_slice_feedback:\n    parser.error('Rear core slice motion requires core slice feedback')")
replace('rear_core_slice_enabled=args.rear_core_slice_feedback)', 'rear_core_slice_enabled=args.rear_core_slice_feedback, rear_core_slice_motion_enabled=args.rear_core_slice_motion_feedforward)')
needle="                    region_approach = RegionApproachLifecycle(**region_extra)"
replace(needle,"                    if args.rear_core_slice_motion_feedforward:\n                        frontal_plan['rear_cop_centering']['core_slice_motion_feedforward']=True\n"+needle)
p.write_text(s)
for p in dst.glob('*.py'):ast.parse(p.read_text())
unchanged=[n for n in m['source_sha256'] if n not in ['collect_paired_sorting.py','rear_cop_route.py','rear_cop_centering.py']]
for n in unchanged:assert sha(dst/n)==m['source_sha256'][n]
report=dict(parent_manifest_sha256=sha(parent/'MANIFEST.json'),probe_check_sha256=sha(probe/'CHECK.json'),source_sha256={n:sha(dst/n) for n in m['source_sha256']},unchanged_parent_helpers=unchanged,default_off=True,collector_wired_in_source=True,cli_checked=False,lifecycle_checked=False,auditor_checked=False,physical_started=False,training_ready=False,scope='Only optional loaded rear core-slice motion feedforward differs; current/past measured poses/COP only. Gain/YZ/first loaded and original guards/limits preserved. Finish CLI/lifecycle/independent audit before freeze or physics.')
(dst/'PREPARATION.json').write_text(json.dumps(report,indent=2));print(dst)
