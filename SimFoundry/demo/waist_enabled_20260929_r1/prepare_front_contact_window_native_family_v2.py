"""Clone actual initial-center front family, replacing only loss evidence opt-in.
Uninstalled: collector and current physical stage remain unchanged.
"""
from pathlib import Path
import ast,hashlib,json,datetime
W=Path(__file__).resolve().parent;S=W/'staged_front_loaded_z_quarter_v1';C=W/'front_contact_window_candidate_v1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};edits=[]
p=S/'front_initial_center_top_contact.py';text=p.read_text();node=next(x for x in ast.parse(text).body if isinstance(x,ast.ClassDef) and x.name=='TopContactBypassState');original='\n'.join(text.splitlines()[min(x.lineno for x in node.decorator_list)-1:node.end_lineno])+'\n'
a='            self.lost_contact_steps=self.lost_contact_steps+1 if load_n<.2 else 0';b="            present=self._window_loss_contact(load_n) if getattr(self,'contact_window_enabled',False) else load_n>=.2\n            self.lost_contact_steps=0 if present else self.lost_contact_steps+1"
assert original.count(a)==1;body=original.replace(a,b);assert body.replace(b,a)==original
out=C/'window_initial_center_top_v2.py'
with out.open('x') as f:f.write('from front_initial_center_top_contact import *\n\n'+body)
sources[str(p)]=sha(p);sources[str(out)]=sha(out);edits.append(dict(source=str(p),candidate=str(out),class_inverse_exact=True,only_loss_predicate=True))
for old,new,old_import,new_import in [('front_initial_center_route.py','window_initial_center_route_v2.py','from front_initial_center_top_contact import TopContactBypassState','from window_initial_center_top_v2 import TopContactBypassState'),('front_initial_center_cop_route.py','window_initial_center_cop_v2.py','from front_initial_center_route import FrontTopRouteState','from window_initial_center_route_v2 import FrontTopRouteState')]:
 p=S/old;s=p.read_text();assert s.count(old_import)==1;v=s.replace(old_import,new_import);assert v.replace(new_import,old_import)==s;out=C/new
 with out.open('x') as f:f.write(v)
 sources[str(p)]=sha(p);sources[str(out)]=sha(out);edits.append(dict(source=str(p),candidate=str(out),inverse_exact=True,only_parent_import=True))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,source_sha256=sources,edits=edits,default_off=True,collector_modified=False,physics_verified=False,training_ready=False)
with (C/'NATIVE_FAMILY_DERIVATION_V2.json').open('x') as f:json.dump(report,f,indent=2)
print('PREPARED_ACTUAL_INITIAL_CENTER_FAMILY_V2')
