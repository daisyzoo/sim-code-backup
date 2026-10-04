"""Version independent phase-aware midpoint auditors; retain original math."""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;D=W/'front_corridor_lateral_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();entries=[]
def build(oldname,newname,replacements):
 parent=W/oldname;dest=W/newname;s=parent.read_text();edits=[]
 for old,new in replacements:
  assert s.count(old)==1,(oldname,old,s.count(old));s=s.replace(old,new);edits.append(dict(old=old,new=new))
 ast.parse(s);restored=s
 for e in reversed(edits):restored=restored.replace(e['new'],e['old'])
 assert restored==parent.read_text()
 with dest.open('x') as f:f.write(s)
 entries.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits))
build('audit_front_corridor_midpoint_record.py','audit_front_corridor_lateral_record_v1.py',[
 ('parent_guard_reason,prior_stop_reason):','parent_guard_reason,prior_stop_reason,lateral_y_enabled=False):\n assert type(lateral_y_enabled) is bool'),
 ("elif route_stage!='front_x':reason='preserve_outside_front_x'","elif route_stage!='front_x' and not lateral_y_enabled:reason='preserve_outside_front_x'")])
build('audit_front_corridor_midpoint_observations.py','audit_front_corridor_lateral_observations_v1.py',[
 ('from audit_front_corridor_midpoint_record import verify,near','from audit_front_corridor_lateral_record_v1 import verify,near'),
 ('def inspect(rows,plan,tr,ori,*,enabled,expected_steps):','def inspect(rows,plan,tr,ori,*,enabled,expected_steps,lateral_y_enabled=False):\n assert type(lateral_y_enabled) is bool and (not lateral_y_enabled or enabled)'),
 ("cfg['phase']=='front_x_only'","cfg['phase']==('front_x_and_lateral_y' if lateral_y_enabled else 'front_x_only')"),
 ('parent_guard_reason=parent,prior_stop_reason=stop)','parent_guard_reason=parent,prior_stop_reason=stop,lateral_y_enabled=lateral_y_enabled)')])
build('audit_front_corridor_midpoint_cop.py','audit_front_corridor_lateral_cop_v1.py',[
 ('def reconstruct(rows,plan,tr,ori,packets,key,*,midpoint_enabled,expected_steps):','def reconstruct(rows,plan,tr,ori,packets,key,*,midpoint_enabled,expected_steps,lateral_y_enabled=False):'),
 ('from audit_front_corridor_midpoint_observations import inspect','from audit_front_corridor_lateral_observations_v1 import inspect'),
 ('checked=inspect(rows,plan,tr,ori,enabled=midpoint_enabled,expected_steps=expected_steps)','checked=inspect(rows,plan,tr,ori,enabled=midpoint_enabled,expected_steps=expected_steps,lateral_y_enabled=lateral_y_enabled)')])
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=entries,independent_planner_math_unchanged=True,full_native_audit_family_integrated=False,training_ready=False,source_sha256={str(Path(__file__)):sha(__file__)})
with (D/'AUDITOR_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print('Created three independent adapters; full audit family still pending')
