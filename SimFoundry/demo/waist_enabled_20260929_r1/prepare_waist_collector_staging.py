"""Stage collector admission plumbing; live controller/source remain frozen."""
from pathlib import Path
import json,hashlib,ast,sys
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_waist_collector';stage.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol_path=(Path(sys.argv[1]).resolve()/'PROTOCOL.json') if len(sys.argv)>1 else root/'contact_stability_groups_r1/PROTOCOL.json'
protocol=json.loads(protocol_path.read_text())
for p,h in protocol['source_sha256'].items():assert sha(p)==h,p
source=(repo/'scripts/collect_paired_sorting.py').read_text();original=source
helper=(root/'waist_collector_admission_candidate.py').read_text();tree=ast.parse(helper)
# Inline exact tested definitions so the contract's collector hash covers them.
helper=ast.unparse(ast.Module(body=[n for n in tree.body if not isinstance(n,ast.Expr)],type_ignores=[]))
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b)
source=replace(source,"parser.add_argument('--role',", "parser.add_argument('--waist-pilot-contract', type=Path, help='Exact verified fresh waist pilot contract; diagnostic files remain excluded.')\nparser.add_argument('--role',")
# Permit validated exact pilot settings wherever diagnostic expert settings were
# previously required. No-contract behavior and other condition terms unchanged.
source=source.replace("args.role != 'diagnostic'",'not diagnostic_or_waist_pilot').replace("args.role!='diagnostic'",'not diagnostic_or_waist_pilot').replace("args.role=='diagnostic'",'diagnostic_or_waist_pilot')
source=replace(source,'args = parser.parse_args()',helper+"\n\nargs = parser.parse_args()\ntry:\n    waist_admission = prepare_waist_pilot(vars(args), Path(__file__).resolve())\nexcept (ValueError, OSError, KeyError) as exc:\n    parser.error(str(exc))\ndiagnostic_or_waist_pilot = args.role == 'diagnostic' or waist_admission is not None\nwaist_contract_hash = waist_admission.contract_sha256 if waist_admission else None")
source=replace(source,'(1.0 if args.extended_waist_diagnostic else .80)','(1.0 if args.extended_waist_diagnostic or waist_admission is not None else .80)')
source=replace(source,"'spatial_pilot_contract_sha256': spatial_contract_hash", "'waist_pilot_contract_sha256': waist_contract_hash, 'spatial_pilot_contract_sha256': spatial_contract_hash")
source=replace(source,"    if args.spatial_pilot_contract:\n        (root/'spatial_pilot_contract.json')", "    if waist_admission is not None:\n        contract_bytes = waist_admission.contract_path.read_bytes()\n        if hashlib.sha256(contract_bytes).hexdigest() != waist_contract_hash:\n            raise ValueError('Waist contract changed before output snapshot')\n        (root/'waist_pilot_contract.json').write_bytes(contract_bytes)\n    if args.spatial_pilot_contract:\n        (root/'spatial_pilot_contract.json')")
source=replace(source,"    paths.append(ROOT / 'simfoundry/data/object_relative_push.py')", "    paths.append(ROOT / 'simfoundry/data/waist_pilot_protocol.py')\n    paths.append(ROOT / 'simfoundry/data/object_relative_push.py')")
source=replace(source,"            layout = dict(explicit_layout) if (args.diagnostic_layout_json or args.spatial_pilot_contract) else sample_layout(i)", "            layout = waist_admission.layout(i) if waist_admission is not None else (dict(explicit_layout) if (args.diagnostic_layout_json or args.spatial_pilot_contract) else sample_layout(i))")
source=replace(source,"            layout = sample_layout(args.wait_layout_start+i)", "            layout = waist_admission.layout(args.wait_layout_start+i,wait=True) if waist_admission is not None else sample_layout(args.wait_layout_start+i)")
source=replace(source, 'app = AppLauncher(args, enable_cameras=True).app', 'app = AppLauncher(args, enable_cameras=True).app\nfinalize_waist_pilot(waist_admission, vars(args), Path(__file__).resolve())')
compile(source,str(stage/'collect_paired_sorting.py'),'exec');(stage/'collect_paired_sorting.py').write_text(source)
(stage/'MANIFEST.json').write_text(json.dumps(dict(source_protocol_path=str(protocol_path),source_protocol_sha256=sha(protocol_path),live_source_sha256=protocol['source_sha256'],candidate_collector_sha256=sha(stage/'collect_paired_sorting.py'),inlined_admission_helper_sha256=sha(root/'waist_collector_admission_candidate.py'),scope='Isolated collector candidate. Default diagnostic behavior preserved; exact full contract validation before simulation required for pilot. Admission helper inlined to bind it under collector SHA. Actual applying, qualifying physics, real fresh contract, data review and training remain pending.',training_ready=False),indent=2));print(stage)
