"""Prepare isolated default-off bounded witness retry at planning and handover."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;S=W/'staged_rear_recovery_tracking';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();manifest=[]
p=W/'rear_transport_retry_plan.py';assert not p.exists();p.write_text('''"""Original planner plus explicitly selected unchanged directional qualification."""
import numpy as np
from recontact_plan import plan as parent_plan
from rear_transport_feasible_retry_candidate import witness

def qualify(scene,current,step,parent_plan,*,required=False,retry=False):
    if type(required) is not bool or type(retry) is not bool:raise ValueError('Explicit transport flags required')
    if not required:return parent_plan
    if type(parent_plan.get('accepted')) is not bool:raise ValueError('Invalid parent plan')
    if not parent_plan['accepted']:return parent_plan
    if parent_plan['step']!=step or parent_plan['scene']!=scene.record() or not np.array_equal(parent_plan['start'],np.asarray(current,float)):raise ValueError('Parent plan must match current observation')
    result=witness(scene,parent_plan['endpoint'],retry_feasible=retry)
    if not result['accepted']:return dict(accepted=False,reason='rear_transport_endpoint_unverified',step=step,start=list(current),scene=scene.record(),parent_plan=parent_plan,rear_transport_witness=result)
    return dict(parent_plan,rear_transport_witness=result)

def plan(scene,q,*,require_rear_transport=False,transport_feasible_retry=False,**kwargs):
    if type(require_rear_transport) is not bool or type(transport_feasible_retry) is not bool:raise ValueError('Explicit transport flags required')
    original=parent_plan(scene,q,**kwargs)
    return qualify(scene,q,kwargs['step'],original,required=require_rear_transport,retry=transport_feasible_retry)
''');ast.parse(p.read_text())
for old,new,changes in [
 ('rear_transport_recontact_lifecycle.py','rear_transport_retry_lifecycle.py',[
 ('from rear_transport_recontact_plan import plan','from rear_transport_retry_plan import plan'),
 ('from rear_recontact_transport_witness import witness','from rear_transport_feasible_retry_candidate import witness'),
 ('box_center_preference=False):','box_center_preference=False,transport_feasible_retry=False):'),
 ("        if type(enabled) is not bool", "        if type(transport_feasible_retry) is not bool:raise ValueError('Explicit retry flag required')\n        self.transport_feasible_retry=transport_feasible_retry\n        if type(enabled) is not bool"),
 ('require_rear_transport=require_rear_transport)','require_rear_transport=require_rear_transport,transport_feasible_retry=self.transport_feasible_retry)'),
 ('measured_witness=witness(scene,q)','measured_witness=witness(scene,q,retry_feasible=self.transport_feasible_retry)')]),
 ('rear_transport_entry_lift_lifecycle.py','rear_transport_retry_entry_lifecycle.py',[
 ('from rear_transport_recontact_lifecycle import RecontactLifecycle as OriginalLifecycle','from rear_transport_retry_lifecycle import RecontactLifecycle as OriginalLifecycle'),
 ('entry_lift=False):','entry_lift=False,transport_feasible_retry=False):'),
 ('        if type(entry_lift) is not bool',"        if type(transport_feasible_retry) is not bool:raise ValueError('Explicit retry flag required')\n        if type(entry_lift) is not bool"),
 ('box_center_preference=box_center_preference)','box_center_preference=box_center_preference,transport_feasible_retry=transport_feasible_retry)')])]:
 src=S/old;dest=W/new;assert not dest.exists();s=src.read_text();edits=[]
 for a,b in changes:
  assert s.count(a)==1,(new,a);s=s.replace(a,b);edits.append(dict(old=a,new=b))
 back=s
 for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
 assert back==src.read_text();ast.parse(s);dest.write_text(s);manifest.append(dict(parent=str(src),parent_sha256=sha(src),output=str(dest),output_sha256=sha(dest),edits=edits))
with (W/'REAR_TRANSPORT_RETRY_LIFECYCLE_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=manifest,plan_sha256=sha(p),witness_sha256=sha(W/'rear_transport_feasible_retry_candidate.py'),simulation_started=False,training_ready=False),f,indent=2)
print('prepared isolated planning/lifecycle/entry-lift wrappers')
