"""Additional observer provenance binding; no execution of controller or physics."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_observation_binding(ep):
 ep=Path(ep).resolve();case=ep.parent;stage=W/'staged_substep_observer';repo=W.parents[1]
 prov=json.loads((case/'provenance.json').read_text());args=prov['args'];source=prov['source_sha256']
 assert args['trace_substep_contacts'] is True and args['trace_solved_contact_forces'] is True
 assert args['role']=='diagnostic' and args['expert_top_tilt_recontact_rad']==.03 and args['expert_frontal_top_load_n']==5.
 assert not args['policy_port'] and not args['push_force_n'] and not args['wait_force_n']
 p=json.loads((W/'box_inward_groups_r1/PROTOCOL.json').read_text());prep=json.loads((stage/'PREPARATION.json').read_text());helpers=set(prep['helpers'])
 collector=(stage/'collect_paired_sorting.py').read_text();restored=collector
 for block in prep['instrumentation_blocks']:assert restored.count(block)==1;restored=restored.replace(block,'')
 parent=W/'staged_box_inward_correction/collect_paired_sorting.py'
 assert restored==parent.read_text() and sha(parent)==p['frozen_files_sha256'][str(parent)]
 for rel,digest in source.items():
  path=repo/rel;assert sha(case/'source_snapshot'/rel)==digest==sha(path)
  normalized=str(path).replace('/staged_substep_observer/','/staged_box_inward_correction/')
  if path.parent==stage and path.name in helpers:assert digest==prep['source_sha256'][str(path)]
  elif path==stage/'collect_paired_sorting.py':assert digest==prep['new_collector_sha256']
  else:assert digest==p['frozen_files_sha256'][normalized],rel
 for name in helpers|{'collect_paired_sorting.py'}:assert str((stage/name).relative_to(repo)) in source
 runtime=json.loads((case/'SUBSTEP_RUNTIME_BINDING.json').read_text());record=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())
 assert runtime['observer_installed'] is True and runtime['original_graph_setting'] is True and runtime['training_ready'] is False
 assert record['metadata']==runtime['metadata'] and record['training_ready'] is False
 m=runtime['metadata'];assert m['fixture_cpu'] is False and m['expected_substeps']==24 and m['control_decimation']==8 and m['substeps_per_physics_tick']==3 and abs(m['solver_dt_s']-1/360)<1e-12
 assert m['expected_manager_steps']==(1 if m['all_graphable'] else 8)
 assert len(m['geom_to_shape'])==1
 required={'newton_manager.py','mjwarp_manager.py','solver_mujoco.py','support.py',*helpers}
 assert {Path(k).name for k in runtime['source_files']}==required
 for path,row in runtime['source_files'].items():
  assert sha(path)==row['sha256']==sha(case/row['snapshot'])
  if Path(path).name in helpers:assert Path(path).parent==stage and row['sha256']==source[str(Path(path).relative_to(repo))]
 # Physical collision shape/body ownership has an independent existing archive.
 import numpy as np
 with np.load(case/'runtime_collision_arrays.npz') as z:assert np.array_equal(z['shape_body'],m['shape_body'])
 assert record['recording_sha256']==sha(ep/'substep_contacts.npz')
 return dict(passed=True,original_control_recovered_byte_exact=True,source_sha256={str(f):sha(f) for f in [case/'provenance.json',case/'SUBSTEP_RUNTIME_BINDING.json',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',stage/'PREPARATION.json',Path(__file__)]},training_ready=False)
