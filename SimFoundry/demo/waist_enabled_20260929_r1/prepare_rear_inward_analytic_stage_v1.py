"""Independent-copy explicit-defaultoff collector stage; never launches physics."""
from pathlib import Path
import ast,copy,datetime,hashlib,json,shutil
W=Path(__file__).resolve().parent;P=W/'staged_front_effective_height_v1';S=W/'staged_rear_inward_analytic_v1';D=W/'rear_inward_analytic_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not S.exists() and not D.exists();D.mkdir();shutil.copytree(P,S,copy_function=shutil.copy2,ignore=shutil.ignore_patterns('__pycache__'))
parent_hashes={str(p):sha(p) for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
for p in P.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts:
  q=S/p.relative_to(P);assert p.stat().st_ino!=q.stat().st_ino and sha(p)==sha(q)
helper=W/'joint_edge_inward_analytic_first_candidate_v3.py';shutil.copy2(helper,S/helper.name)
s=(P/'joint_edge_inward_adapter.py').read_text();old='from joint_edge_inward_command import refine_rear_command';new='from joint_edge_inward_analytic_first_candidate_v3 import refine_rear_command\nfrom functools import partial\nrefine_rear_command = partial(refine_rear_command, analytic_first=True)';assert s.count(old)==1;s=s.replace(old,new)
(S/'joint_edge_inward_analytic_adapter_v1.py').write_text(s)
assert s.replace(new,old)==(P/'joint_edge_inward_adapter.py').read_text()
p=S/'collect_paired_sorting.py';s=p.read_text();flag='rear_inward_analytic_first';cli='--rear-inward-analytic-first'
anchor="parser.add_argument('--rear-box-inward-correction'";pos=s.index(anchor);s=s[:pos]+"parser.add_argument('--rear-inward-analytic-first',action='store_true',help='Diagnostic right-rear analytic first solve and original stationarity gate before emission; default off.')\n"+s[pos:]
anchor="if args.edge_clearance_intersection and not (";pos=s.index(anchor);s=s[:pos]+"if args.rear_inward_analytic_first and not (args.role=='diagnostic' and args.rear_box_inward_correction and args.rear_joint_edge_command and args.rear_joint_edge_analytic_retry and args.rear_joint_edge_parent_seed_retry and args.edge_clearance_intersection and not args.policy_port and not args.idle):\n    parser.error('Analytic first requires original diagnostic right inward/edge/clearance pipeline without policy or idle')\n"+s[pos:]
anchor="                from joint_edge_inward_adapter import refine_record\n";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"            if args.rear_inward_analytic_first and side=='right':\n                from joint_edge_inward_analytic_adapter_v1 import refine_record\n")
anchor="    if args.rear_box_inward_correction:\n        episode.collect_meta['rear_box_inward_correction']=True\n";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"    if args.rear_inward_analytic_first:\n        episode.collect_meta['rear_inward_analytic_first']=True\n        episode.collect_meta['rear_inward_analytic_first_spec']=dict(version='rear_inward_analytic_first_v1',side='right',first_constraint_jacobian='analytic',original_solver_ftol=1e-11,original_solver_maxiter=300,emitted_stationarity_max=1e-6,original_objective_and_constraints=True,training_ready=False)\n")
anchor="    if args.rear_box_inward_correction:\n        paths.extend([STAGE/'joint_edge_inward_command.py',STAGE/'joint_edge_inward_adapter.py'])\n";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"    if args.rear_inward_analytic_first:\n        paths.extend([STAGE/'joint_edge_inward_analytic_first_candidate_v3.py',STAGE/'joint_edge_inward_analytic_adapter_v1.py'])\n")
p.write_text(s)
class RemoveNew(ast.NodeTransformer):
 def visit_If(self,n):
  if 'args.'+flag in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  v=n.value
  if isinstance(v,ast.Call) and ast.unparse(v.func)=='parser.add_argument' and v.args and isinstance(v.args[0],ast.Constant) and v.args[0].value==cli:return None
  return self.generic_visit(n)
assert ast.dump(RemoveNew().visit(copy.deepcopy(ast.parse(s))),include_attributes=False)==ast.dump(ast.parse((P/'collect_paired_sorting.py').read_text()),include_attributes=False)
for source,h in parent_hashes.items():assert sha(source)==h
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_stage=str(P),stage=str(S),defaultoff_exact_parent_ast=True,adapter_original_body_exact=True,parent_sources_sha256=parent_hashes,stage_sources_sha256={str(p):sha(p) for p in S.rglob('*') if p.is_file()},helpers=['joint_edge_inward_analytic_first_candidate_v3.py','joint_edge_inward_analytic_adapter_v1.py'],independent_inodes=True,collector_cli=cli,explicit_defaultoff=True,physical_launch_allowed=False,training_ready=False,remaining=['Actual six-command parser/invalid-config check','Native collector branch and metadata/archive execution','Source binding and all original audit consumers plus new rejection semantics','Defaultoff full native fixture and enabled fixture','Complete current physical comparison before new full-condition trial'])
with (D/'STAGE_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(stage=str(S),parent_files=len(parent_hashes),defaultoff_exact_parent_ast=True,physics_started=False)))
