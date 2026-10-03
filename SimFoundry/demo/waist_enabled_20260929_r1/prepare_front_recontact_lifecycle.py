"""Prepare isolated default-off repeated-front-bag landing components.
No runtime collector edits. Original geometry, tracking and capture math retained.
"""
from pathlib import Path
import json,hashlib,datetime
W=Path(__file__).resolve().parent;S=W/'staged_rear_waypoint_reconciliation';D=W/'front_bag_recontact_center_draft_r4';D.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();changes=[]
def make(parent,name,replacements):
 original=Path(parent).read_text();text=original;entries=[]
 for old,new in replacements:
  count=text.count(old);assert count>0,(name,old);text=text.replace(old,new);entries.append(dict(old=old,new=new,count=count))
 restored=text
 for e in reversed(entries):assert restored.count(e['new'])==e['count'];restored=restored.replace(e['new'],e['old'])
 assert restored==original
 dest=D/name
 with dest.open('x') as f:f.write(text)
 changes.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),changes=entries,reverse_text_identical=True))
make(W/'front_bag_recontact_center_draft_r3/front_recontact_center_tracking.py','front_recontact_center_tracking.py',[])
common=[('Unwired first-front-only measured landing lifecycle, default off.','Unwired one-real-recovery front-bag measured landing lifecycle, default off.'),('from front_initial_center_tracking import propose','from front_recontact_center_tracking import propose'),('class FrontInitialCenterLifecycle:','class FrontRecontactCenterLifecycle:'),('def __init__(self, *, enabled=False, maximum_ticks=240):','def __init__(self, *, recontact_index, enabled=False, maximum_ticks=240):'),("        self.enabled = enabled", "        if type(recontact_index) is not int or recontact_index < 1:\n            raise ValueError('Expected one real positive recovery index')\n        self.recontact_index = recontact_index\n        self.enabled = enabled"),('initial_handover_already_complete','recovery_handover_already_complete'),("selected and recontacts == 0 and parent_mode", "selected and scene.side == 'left' and recontacts == self.recontact_index and parent_mode"),("            self.attempted = True", "            if not checked_scene(scene, q)['accepted']:\n                return dict(kind='unchanged', reason='waiting_for_original_unloaded_geometry', context=context)\n            self.attempted = True")]
make(S/'front_initial_center_lifecycle_v2.py','front_recontact_center_lifecycle_static.py',common)
selection=[('from front_initial_center_lifecycle_v2 import FrontInitialCenterLifecycle','from front_recontact_center_lifecycle_static import FrontRecontactCenterLifecycle'),('def select_planned(planning, scene, current, *, step, previous_q, previous_command, decay):','def select_planned(planning, scene, current, *, step, previous_q, previous_command, decay, recontact_index):'),('    q0, qp0, prev0, a =',"    if type(recontact_index) is not int or recontact_index < 1 or scene.side != 'left':\n        raise ValueError('Expected real front-bag recovery')\n    q0, qp0, prev0, a ="),('probe = FrontInitialCenterLifecycle(enabled=True)','probe = FrontRecontactCenterLifecycle(enabled=True,recontact_index=recontact_index)'),("recontacts=0,guard_stop=False", "recontacts=recontact_index,guard_stop=False"),('def plan(scene, current, *, step, previous_q, previous_command, decay):','def plan(scene, current, *, step, previous_q, previous_command, decay, recontact_index):'),('previous_command=previous_command,decay=decay)','previous_command=previous_command,decay=decay,recontact_index=recontact_index)')]
make(S/'front_initial_center_selection.py','front_recontact_center_selection.py',selection)
make(S/'front_initial_center_lifecycle_v3.py','front_recontact_center_lifecycle.py',common+[('from front_initial_center_selection import plan','from front_recontact_center_selection import plan'),('created = plan(scene, q, step=step, previous_q=previous_q, previous_command=previous_command, decay=decay)','created = plan(scene, q, step=step, previous_q=previous_q, previous_command=previous_command, decay=decay, recontact_index=self.recontact_index)')])
adapter=[('Initial front path bookkeeping and measured-reference capture only.','Real front-bag recovery bookkeeping and measured-reference capture only.'),("    if event['context']['recontacts'] != 0 or state.recontacts != 0:\n        raise ValueError('Initial landing cannot impersonate recontact')", "    counter = event['context']['recontacts']\n    if type(counter) is not int or counter < 1 or type(state.recontacts) is not int or state.recontacts != counter:\n        raise ValueError('Recovery capture must match the real parent counter')"),('front_initial_center_phase=','front_recontact_center_phase=')]
make(S/'front_initial_center_adapter.py','front_recontact_center_adapter.py',adapter)
with (D/'COMPONENT_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,changes=changes,simulation_started=False,collector_integrated=False,training_ready=False),f,indent=2)
print(json.dumps(dict(directory=str(D),components=len(changes))))
