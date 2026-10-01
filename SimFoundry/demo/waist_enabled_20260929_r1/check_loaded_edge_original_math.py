"""Original task and geometry math preserved; old10 streams compared directly.
Recorded path events are supplied for math-equivalence only: an unfinished path
can be compared here, but fails the separate complete live pose admission.
"""
from pathlib import Path
import sys,ast,json,hashlib,datetime,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
import audit_recontact_pose_self_clearance as old_geometry
import audit_loaded_edge_self_clearance as new_geometry
import audit_recontact_pose_task_optimality as old_task
import audit_loaded_edge_task_optimality as new_task
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();stage=w/'staged_loaded_edge_coverage'
# Exact original task math (not only agreement on chosen records).
def function(path,name):return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
a=function(w/'audit_recontact_pose_task_optimality.py','verify_task_rows');b=function(w/'audit_loaded_edge_task_optimality.py','verify_task_rows');assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
# Remove only declared coverage dependency, extra argument and new override branch.
a=function(w/'audit_recontact_pose_self_clearance.py','audit');b=function(w/'audit_loaded_edge_self_clearance.py','audit');b.args.args=b.args.args[:-1];b.args.defaults=b.args.defaults[:-1]
class RemoveCoverage(ast.NodeTransformer):
 def visit_If(self,node):
  test=ast.unparse(node.test)
  if test in ['verified_edges is None',"'loaded_edge_coverage' in c"]:return None
  return self.generic_visit(node)
 def visit_ImportFrom(self,node):
  if node.module=='audit_loaded_edge_pose_live':node.module='audit_recontact_pose_live'
  return node
 def visit_Constant(self,node):
  if node.value=='LOADED_EDGE_POSE_LIVE_AUDIT.json':node.value='RECONTACT_POSE_LIVE_AUDIT.json'
  return node
b=RemoveCoverage().visit(b);assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'undeclared original geometry change'
geom=old_task.IndependentElbows(stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');records=[];sources={};failures=[]
for quality in sorted((w/'recontact_pose_groups_r1').glob('case_*/layout_*/quality.json')):
 ep=quality.parent;events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'recontact_pose.json').read_text())['rows'] if r['kind'] in ['command','handover']} if (ep/'recontact_pose.json').exists() else {}
 old=old_geometry.audit(ep,verified_events=events);new=new_geometry.audit(ep,verified_events=events,verified_edges={})
 # Scope docstring deliberately changes, numerical source evidence stays exact.
 old.pop('scope');new.pop('scope');assert old==new,(ep.name,'geometry differs')
 row=dict(episode=ep.name,geometry_equal=True,executed_frames=new['executed_frames'])
 if 'wait' not in ep.name:
  a=old_task.verify_task_rows(ep,geom,events);b=new_task.verify_task_rows(ep,geom,events)
  for x in [a,b]:x.pop('auditor_sha256');x.pop('scope')
  assert a==b;row.update(task_math_equal=True,task_frames=b['frames'],kkt_failures=len(b['errors']),max_kkt_residual=b['max_kkt_residual']);failures.extend(dict(episode=ep.name,**r) for r in b['errors'])
 records.append(row);print(row,flush=True)
 for path in ep.iterdir():
  if path.suffix in ['.json','.npz'] and 'AUDIT' not in path.name:sources[str(path)]=sha(path)
 for path in [ep.parent/'provenance.json',ep.parent/'runtime_geometry_provenance.json',ep.parent/'runtime_configuration.json',ep.parent/'runtime_collision_arrays.npz']:sources[str(path)]=sha(path)
 for name,h in json.loads((ep.parent/'provenance.json').read_text())['source_sha256'].items():sources[str(ep.parent/'source_snapshot'/name)]=h
for name in ['check_loaded_edge_original_math.py','audit_loaded_edge_self_clearance.py','audit_recontact_pose_self_clearance.py','audit_loaded_edge_task_optimality.py','audit_recontact_pose_task_optimality.py','audit_self_clearance_task_optimality.py']:
 sources[str(w/name)]=sha(w/name)
assert len(records)==10 and sum(r['executed_frames'] for r in records)==9740
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,geometry_and_task_ast_exact=True,records=records,retained_kkt_failures=failures,retained_kkt_failure_count=len(failures),source_sha256=sources,physical_validation=False,training_ready=False)
(stage/'ORIGINAL_MATH_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS original geometry/task math, retained failures',len(failures),flush=True)
