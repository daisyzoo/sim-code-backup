"""Bind each recorded loaded-Z decision to actual raw history and final guard.
Separate original control/source/physics quality audits remain required; this
report alone never admits data or proves the shared model objective.
"""
from pathlib import Path
import sys,json,hashlib,datetime
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from front_z_priority_stage_source_binding import verify_observation_binding
from front_loaded_z_priority_episode_inputs import EpisodeInputs,indexed
from audit_front_loaded_z_priority_record import verify_record
from audit_front_loaded_z_priority_parent import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(ep,*,allow_source_fixture=False):
 ep=Path(ep).resolve();fixture=(ep.parent/'SOURCE_CONTRACT_FIXTURE.json').exists()
 assert not fixture or allow_source_fixture,'Synthetic contract fixture is not physical evidence'
 binding=verify_observation_binding(ep);inputs=EpisodeInputs(ep);log=inputs.read('front_loaded_z_priority.json');records=indexed(log['rows'],inputs.n)
 assert set(records)==set(range(inputs.n)) and [r['step'] for r in log['rows']]==list(range(inputs.n))
 results=[]
 for t in range(inputs.n):
  m=records[t];c=inputs.coords.get(t)
  if c is not None:
   assert c['front_loaded_z_priority']==m
   if m['applied']:
    assert 'unexecuted_parent_waist_target_rad' in c;near(c['waist_target_rad'],inputs.u[t,0])
   else:assert 'unexecuted_parent_waist_target_rad' not in c
  inputs.verify_actual_final_guard(t)
  results.append(verify_record(**inputs.arguments(t,m)))
 sources=dict(binding['source_sha256'],**inputs.sources)
 for name in ['audit_front_z_priority_execution.py','front_z_priority_stage_source_binding.py','front_loaded_z_priority_episode_inputs.py','audit_front_loaded_z_priority_record.py','audit_front_loaded_z_priority_applied_row.py','audit_front_loaded_z_priority_parent.py','front_loaded_z_priority_audit_geometry.py','support_vertex_stationarity.py','audit_unloaded_wrist_prior_live.py','audit_self_clearance_task_optimality.py','screen_bag_vertical_priority_geometry.py']:sources[str(W/name)]=sha(W/name)
 return dict(passed=True,scope=__doc__,episode=ep.name,frames=inputs.n,actual_history_bound=True,fixture_only=fixture,physical_execution_evidence=not fixture,applied=sum(r['applied'] for r in results),reason_counts={name:sum(r['reason']==name for r in results) for name in sorted({r['reason'] for r in results})},records=results,source_sha256=sources,original_full_control_audits_required=True,training_ready=False)

if __name__=='__main__':
 assert len(sys.argv)==2
 ep=Path(sys.argv[1]);out=inspect(ep);path=ep/'FRONT_Z_PRIORITY_EXECUTION_AUDIT.json'
 with path.open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:v for k,v in out.items() if k not in ['records','source_sha256','scope']},indent=2))
