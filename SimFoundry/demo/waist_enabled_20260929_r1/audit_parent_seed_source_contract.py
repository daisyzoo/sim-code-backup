"""Additional precision source/argument/metadata binding; never runs its solver.
The enclosing versioned native and KKT audits retain original mathematics.
This source binding alone does not verify executed actions or task success.
"""
from pathlib import Path
import json,hashlib
import numpy as np
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_parent_seed_source(ep):
 ep=Path(ep);prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];source=prov['source_sha256'];snap=ep.parent/'source_snapshot';stage=W/'staged_precise_parent_seed'
 assert args.get('rear_joint_edge_parent_seed_retry') is True,'parent-seed flag missing/disabled'
 assert args.get('rear_joint_edge_analytic_retry') is True,'parent-seed requires original analytic retry'
 assert args.get('precise_clearance_task_ik') is True,'precision flag missing/disabled'
 assert args['self_clearance_task_ik'] is True and args['unloaded_recontact_pose'] is True and args['recontact_interior_preference'] is True
 names=['collect_paired_sorting.py','waist_coordination_clearance.py','task_ik.py','task_ik_precision.py','joint_edge_command.py','joint_edge_adapter.py'];bound={}
 for name in names:
  keys=[n for n in source if n.endswith('/'+name)];assert len(keys)==1,('missing/duplicate precision source',name);key=keys[0]
  assert sha(snap/key)==source[key]==sha(stage/name),('precision source mismatch',name);bound[name]=source[key]
 parent=(W/'staged_recontact_interior/task_ik.py').read_text();ordinary=(stage/'task_ik.py').read_text();assert ordinary==parent and ordinary.count('ftol=1e-11')==1
 assert (stage/'task_ik_precision.py').read_text()==ordinary.replace('ftol=1e-11','ftol=1e-13'),'precision changed more than stopping tolerance'
 with np.load(ep/'raw.npz') as z:meta=json.loads(str(z['collect_meta']))
 assert meta.get('task_ik_optimizer_ftol')==1e-13,'raw precision setting missing/incorrect'
 assert meta.get('self_clearance_task_ik') is True and meta.get('unloaded_recontact_pose') is True and meta.get('recontact_interior_preference') is True
 assert meta.get('rear_joint_edge_parent_seed_retry') is True,'raw parent-seed setting missing/disabled'
 if (ep/'frontal_bypass.json').exists():
  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']
  if plan.get('rear_joint_edge_command',{}).get('enabled'):
   expected=dict(enabled=True,prior_solver_status=8,finite_endpoint_required=True,maximum_extra_retries=1,initializer='bounded_parent_delta',original_attempts_preserved=True,objective_bounds_tolerances_unchanged=True,failed_retry='preserve_parent_command')
   assert plan.get('rear_joint_edge_parent_seed_retry')==expected
   assert all(type(plan['rear_joint_edge_parent_seed_retry'][k]) is type(v) for k,v in expected.items())
  else:assert 'rear_joint_edge_parent_seed_retry' not in plan
 return dict(passed=True,ftol=1e-13,source_sha256=bound,scope=__doc__,training_ready=False)
