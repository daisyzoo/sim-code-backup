"""Default-off measured-state-domain fix on closed XY parent, without loaded COP."""
from pathlib import Path
import ast,hashlib,json
w=Path(__file__).resolve().parent;src=w/'staged_region_causal_xy_diagnostics';probe=w/'staged_measured_bounds_probe';dst=w/'staged_region_measured_bounds';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((src/'MANIFEST.json').read_text())
for f,h in m['source_sha256'].items():assert sha(src/f)==h
for name in ['CHECK.json','REAL_GEOMETRY_CHECK.json']:
 d=json.loads((probe/name).read_text());assert d['passed'] and d['candidate_sha256']==sha(probe/'contact_patch_approach.py')
dst.mkdir(exist_ok=False)
for f in m['source_sha256']:(dst/f).write_bytes((src/f).read_bytes())
(dst/'contact_patch_approach.py').write_bytes((probe/'contact_patch_approach.py').read_bytes())
def edit(path,replacements):
 text=path.read_text()
 for a,b in replacements:
  assert text.count(a)==1,(path.name,a,text.count(a));text=text.replace(a,b)
 path.write_text(text);ast.parse(text)
edit(dst/'region_approach_lifecycle.py',[
 ('    response_centered_xy_objective: bool=False','    response_centered_xy_objective: bool=False\n    separate_measured_bounds: bool=False'),
 ('load_n,previous_q=None):','load_n,previous_q=None,measured_lower=None,measured_upper=None):'),
 ('        result=contact_patch_step(q,geometry,', '''        if self.separate_measured_bounds:
            if measured_lower is None or measured_upper is None:raise ValueError('Separate measured-state bounds require both physical limits')
            solver_extra.update(measured_lower=measured_lower,measured_upper=measured_upper)
        result=contact_patch_step(q,geometry,'''),
 ("        if response_record is not None:result['causal_response']=response_record", """        if response_record is not None:result['causal_response']=response_record
        if self.separate_measured_bounds:
            result['measured_state_bounds']=dict(measured_lower=np.asarray(measured_lower).tolist(),measured_upper=np.asarray(measured_upper).tolist(),command_lower=np.asarray(lower).tolist(),command_upper=np.asarray(upper).tolist(),handover_requires_command_bounds=True)""")])
edit(dst/'collect_paired_sorting.py',[
 ("parser.add_argument('--region-causal-xy-response',", "parser.add_argument('--region-separate-measured-bounds', action='store_true', help='Separate original1rad measured-state limit from unchanged0.98rad command/forecast domain; diagnostic default off.')\nparser.add_argument('--region-causal-xy-response',"),
 ('args = parser.parse_args()', """args = parser.parse_args()
if args.region_separate_measured_bounds and not (args.region_causal_xy_response and args.waist_limit_rad==1.):
    parser.error('Separate measured bounds require causal XY diagnostic and original1rad physical range')"""),
 ('                    region_approach = RegionApproachLifecycle(**region_extra)', """                    if args.region_separate_measured_bounds:
                        region_extra['separate_measured_bounds']=True
                        frontal_plan['region_measured_state_bounds']=dict(enabled=True,waist_measured_limit_rad=args.waist_limit_rad,waist_command_limit_rad=args.waist_limit_rad-.02,other_joints='original_URDF',handover_requires_command_bounds=True,original_geometry_and_prediction_bounds=True)
                    region_approach = RegionApproachLifecycle(**region_extra)"""),
 ("                    waypoint,reference,region_step=region_approach.update(", """                    if args.region_separate_measured_bounds:
                        measured_lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();measured_hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy()
                        measured_lo[0]=-args.waist_limit_rad;measured_hi[0]=args.waist_limit_rad
                        causal_context.update(measured_lower=measured_lo,measured_upper=measured_hi)
                    waypoint,reference,region_step=region_approach.update(""")])
names=list(m['source_sha256']);report=dict(source_sha256={n:sha(dst/n) for n in names},parent_manifest_sha256=sha(src/'MANIFEST.json'),probe_checks_sha256={n:sha(probe/n) for n in ['CHECK.json','REAL_GEOMETRY_CHECK.json']},collector_wired_in_source=True,cli_checked=False,actual_wiring_checked=False,physical_started=False,training_ready=False,scope='Only optional measured-domain handling on closedXY parent. Command/forecast0.98, geometry, slew and handover domain unchanged. LoadedCOP/release-margin candidates excluded. Requires CLI, actual data-flow/negative tests and independent audit before physical run.')
(dst/'PREPARATION.json').write_text(json.dumps(report,indent=2));print(dst)
