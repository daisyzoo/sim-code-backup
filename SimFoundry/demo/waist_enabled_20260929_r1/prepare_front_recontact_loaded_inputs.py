"""Version only loaded capture reader and its execution entry/contract.
Original bound input/record/geometry mathematics retained; capture input selects
independently verified recovery history after a true capture. No runtime edits.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;S=W/'staged_front_recontact_center';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
def create(parent,target,edits):
 p=W/parent;t=W/target;s=p.read_text()
 for a,b in edits:
  assert s.count(a)==1,(parent,a[:70],s.count(a));s=s.replace(a,b,1)
 ast.parse(s);back=s
 for a,b in reversed(edits):assert back.count(b)==1;back=back.replace(b,a,1)
 assert back==p.read_text()
 with t.open('x') as f:f.write(s)
 records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(t),sha256=sha(t),edits=[dict(old=a,new=b) for a,b in edits]))
create('front_loaded_z_priority_episode_inputs.py','front_recontact_loaded_episode_inputs.py',[
 ("  self.coords=indexed(self.read('coordination.json'),self.n)","  self.initial_capture=self.capture\n  self.recovery=self.read('front_recontact_center.json');recovery_rows=indexed(self.recovery['rows'],self.n)\n  assert type(self.recovery['selected']) is bool and self.recovery['training_ready'] is False\n  from audit_front_recontact_stream import verify_files as verify_recovery_files\n  self.recovery_proof=verify_recovery_files(self.ep)\n  assert self.recovery_proof['selected']==self.recovery['selected']\n  if self.recovery['selected']:\n   assert self.front['selected'] and self.side=='left' and set(recovery_rows)==set(range(1,self.n))\n  else:assert not recovery_rows\n  self.capture=dict(self.initial_capture)\n  for t,r in recovery_rows.items():\n   if r['center_local_after'] is not None:self.capture[t]=r\n  for name in ['audit_front_recontact_stream.py','audit_front_recontact_center_events.py','audit_front_initial_center_planning_v2.py','audit_front_initial_center_preflight.py']:\n   self.sources[str(W/name)]=sha(W/name)\n  self.coords=indexed(self.read('coordination.json'),self.n)"),
 ("for r in self.front['rows'] if r.get('context',{}).get('scene')","for r in self.front['rows']+self.recovery['rows'] if r.get('context',{}).get('scene')")])
create('audit_front_recontact_v1_z_execution.py','audit_front_recontact_v2_z_execution.py',[
 ('from front_loaded_z_priority_episode_inputs import EpisodeInputs,indexed','from front_recontact_loaded_episode_inputs import EpisodeInputs,indexed'),
 ("'front_loaded_z_priority_episode_inputs.py'","'front_recontact_loaded_episode_inputs.py'"),
 ("'FRONT_RECONTACT_V1_Z_EXECUTION_AUDIT.json'","'FRONT_RECONTACT_V2_Z_EXECUTION_AUDIT.json'")])
create('audit_front_recontact_v1_execution.py','audit_front_recontact_v2_execution.py',[
 ('from audit_front_recontact_v1_z_execution import inspect as inspect_z','from audit_front_recontact_v2_z_execution import inspect as inspect_z'),
 ("['audit_front_recontact_v1_execution.py'","['audit_front_recontact_v2_execution.py','audit_front_recontact_v2_z_execution.py','front_recontact_loaded_episode_inputs.py'"),
 ("'FRONT_RECONTACT_V1_EXECUTION_AUDIT.json'","'FRONT_RECONTACT_V2_EXECUTION_AUDIT.json'")])
create('front_recontact_v1_stage_run_contract.py','front_recontact_v2_stage_run_contract.py',[
 ("return ['audit_front_recontact_v1_execution.py'","return ['audit_front_recontact_v2_execution.py'"),
 ("REPORTS['audit_front_recontact_v1_execution.py']=('FRONT_RECONTACT_V1_EXECUTION_AUDIT.json'","REPORTS['audit_front_recontact_v2_execution.py']=('FRONT_RECONTACT_V2_EXECUTION_AUDIT.json'")])
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256={str(Path(__file__)):sha(__file__)},source_inverse_restore_passed=True,full_audit_family_ready=False,simulation_started=False,training_ready=False)
with (S/'LOADED_INPUT_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(modules=len(records),full_family_ready=False)))
