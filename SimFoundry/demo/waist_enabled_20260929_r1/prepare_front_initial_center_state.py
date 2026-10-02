"""Prepare isolated front state classes, preserving parent source off behavior.
No collector import or runtime switch is installed by this preparation.
"""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin'
changes=[]
def create(source,name,pairs):
 original=source.read_text();content=original
 for old,new in pairs:
  assert content.count(old)==1,(source,old)
  content=content.replace(old,new)
 target=W/name
 with target.open('x') as f:f.write(content)
 changes.append(dict(source=str(source),source_sha256=hashlib.sha256(original.encode()).hexdigest(),target=str(target),target_sha256=hashlib.sha256(content.encode()).hexdigest(),replacements=[dict(old=a,new=b) for a,b in pairs]))
create(ROOT/'simfoundry/data/top_contact_bypass.py','front_initial_center_top_contact.py',[
 ('    corner_local: tuple|None=None\n','    corner_local: tuple|None=None\n    selected_surface_local_xy: tuple|None=None\n'),
 ('    def _start_recontact(self,tip,reason):\n','    def _start_recontact(self,tip,reason):\n        self.selected_surface_local_xy=None\n'),
 ('        if not math.isfinite(self.alignment_tolerance_m)', '''        if self.selected_surface_local_xy is not None:
            xy=self.selected_surface_local_xy
            if self.corner_contact or self.forward_margin_m or self.contact_rear_shift_m:
                raise ValueError('Physical initial center conflicts with corner/rear contact offsets')
            if len(xy)!=2 or not all(math.isfinite(v) for v in xy) or any(abs(xy[i])>self.size[i]/2-.01 for i in (0,1)):
                raise ValueError('Captured initial contact surface is outside original inset')
            surface=local_surface_world(target,quat,(*xy,self.size[2]/2))
        if not math.isfinite(self.alignment_tolerance_m)''')])
create(S/'front_top_route_micro.py','front_initial_center_route.py',[
 ('from simfoundry.data.top_contact_bypass import TopContactBypassState','from front_initial_center_top_contact import TopContactBypassState')])
create(S/'front_cop_route_micro.py','front_initial_center_cop_route.py',[
 ('from front_top_route_micro import FrontTopRouteState','from front_initial_center_route import FrontTopRouteState')])
with (W/'FRONT_INITIAL_CENTER_STATE_PREPARATION.json').open('x') as f:json.dump(dict(changes=changes,collector_integrated=False,simulation_started=False,training_ready=False),f,indent=2)
