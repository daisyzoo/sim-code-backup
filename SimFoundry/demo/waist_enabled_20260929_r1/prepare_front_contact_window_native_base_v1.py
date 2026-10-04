"""Isolate original top-contact phase machine; alter only loss-counter evidence.
Default off restores original branch/output. No collector/front-route wiring.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;ROOT=W.parents[1];C=W/'front_contact_window_candidate_v1';parent=ROOT/'simfoundry/data/top_contact_bypass.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=parent.read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='TopContactBypassState');original='\n'.join(source.splitlines()[min(x.lineno for x in node.decorator_list)-1:node.end_lineno])+'\n';s=original;edits=[]
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b);edits.append(dict(old=a,new=b))
replace('class TopContactBypassState:','class WindowTopContactBypassState:')
marker='    def _start_recontact(self,tip,reason):'
extra='''    contact_window_enabled: bool=False
    contact_window_selected_front: bool=False
    _window_packet: dict|None=field(default=None,init=False,repr=False)
    _last_window_step: int=field(default=0,init=False,repr=False)

    def observe_contact_window(self,*,action_step,after_action_step,vertical_load_n,instantaneous_load_n):
        if self.contact_window_enabled is not True:
            raise ValueError('Window observations require explicit enabled candidate')
        if self._window_packet is not None or action_step<=self._last_window_step:
            raise ValueError('Consume each advancing interval exactly once')
        packet=loss_counter_observation(enabled=self.contact_window_enabled,
            selected_front=self.contact_window_selected_front,mode=self.top_mode,
            action_step=action_step,after_action_step=after_action_step,
            vertical_load_n=vertical_load_n,instantaneous_load_n=instantaneous_load_n)
        self._window_packet=packet;self._last_window_step=action_step

    def _consume_contact_window(self,load_n):
        if type(self.contact_window_enabled) is not bool or type(self.contact_window_selected_front) is not bool:
            raise ValueError('Explicit boolean window flags required')
        if not self.contact_window_enabled:return None
        packet=self._window_packet
        if packet is None or packet['mode']!=self.top_mode or abs(packet['observation']['instantaneous_load_n']-load_n)>1e-5:
            raise ValueError('Fresh same-phase current-load binding required')
        if hasattr(self.load,'_last_action_step') and self.load._last_action_step!=packet['observation']['action_step']:
            raise ValueError('Window and pressure must share the same completed interval')
        self._window_packet=None
        return packet

'''
replace(marker,extra+marker)
marker='        if not math.isfinite(self.hand_obstacle_guard_m)'
replace(marker,'        window=self._consume_contact_window(load_n)\n'+marker)
old='            self.lost_contact_steps=self.lost_contact_steps+1 if load_n<.2 else 0'
replace(old,"            contact_present=(load_n>=.2) if window is None else window['contact_evidence_for_loss_counter']\n            self.lost_contact_steps=0 if contact_present else self.lost_contact_steps+1")
replace('        return dict(tilt_recontact_threshold_rad=', '        result=dict(tilt_recontact_threshold_rad=')
s+='        if window is not None:result[\'contact_window_loss_evidence\']=window\n        return result\n'
header='''"""Uninstalled native top-contact candidate. Original helpers retain original paths.
Only loss-counter evidence differs when enabled; current force and COP unchanged.
"""
from simfoundry.data.top_contact_bypass import *
from contact_window_evidence import loss_counter_observation

'''
p=C/'top_contact_window.py';compile(header+s,str(p),'exec')
with p.open('x') as f:f.write(header+s)
back=s.removesuffix("        if window is not None:result['contact_window_loss_evidence']=window\n        return result\n")
for e in reversed(edits):back=back.replace(e['new'],e['old'])
assert back==original
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,original_parent=str(parent),original_parent_sha256=sha(parent),class_inverse_exact=True,edits=edits,candidate=str(p),candidate_sha256=sha(p),source_sha256={str(x):sha(x) for x in [Path(__file__),parent,C/'contact_window_evidence.py',p]},collector_modified=False,front_route_wired=False,physics_verified=False,training_ready=False)
with (C/'NATIVE_BASE_PREPARATION_V1.json').open('x') as f:json.dump(report,f,indent=2)
print('PREPARED_NATIVE_TOP_BASE_ONLY')
