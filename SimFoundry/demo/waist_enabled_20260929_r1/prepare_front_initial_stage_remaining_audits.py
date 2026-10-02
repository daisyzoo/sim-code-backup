"""Prepare original audit inventory bindings and explicit front references/heights.
Syntax and source diffs only. Runtime and complete inventory checks remain required.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
pairs=[('terminal_margin_stage','front_initial_stage'),('TERMINAL_MARGIN_STAGE','FRONT_INITIAL_STAGE'),('staged_terminal_release_margin','staged_front_initial_center')]
def base(name):
 p=W/name;s=p.read_text()
 for a,b in pairs:s=s.replace(a,b)
 return p,s

def put(parent,s,edits,dest=None):
 p=W/(dest or parent.name.replace('terminal_margin_stage','front_initial_stage'));assert not p.exists();ast.parse(s);p.write_text(s);records.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(p),sha256=sha(p),edits=edits))
def change(s,e,a,b):assert s.count(a)==1,(a[:100],s.count(a));e.append(dict(old=a,new=b));return s.replace(a,b)
p,s=base('audit_terminal_margin_stage_region_reference.py');e=[]
s=change(s,e,' from front_initial_stage_audit_context import verified_events',' from front_initial_stage_audit_context import verified_events,verified_front_events\n from front_initial_center_reference_ledger import verified_reference_lifetimes')
s=change(s,e,' verified_recontacts=verified_events(ep)', ''' verified_recontacts=verified_events(ep)
 front=verified_front_events(ep)
 if front:
  assert not verified_recontacts and not f.exists()
  assert rows_override is None,'front references require full native frontal rows'
  rows=json.loads((ep/'frontal_bypass.json').read_text())['rows']
  result=verified_reference_lifetimes(rows,front)
  result.update(raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),native_pose_sha256=hashlib.sha256((ep/'FRONT_INITIAL_STAGE_POSE_LIVE_V2_AUDIT.json').read_bytes()).hexdigest(),ledger_sha256=hashlib.sha256((w/'front_initial_center_reference_ledger.py').read_bytes()).hexdigest())
  return result''')
put(p,s,e)
for name in ['audit_terminal_margin_stage_initial_near_half.py','audit_terminal_margin_stage_terminal_inputs.py','audit_terminal_margin_stage_release.py','audit_terminal_margin_stage_contacts.py','audit_terminal_margin_stage_pressure.py','audit_terminal_margin_stage_micro_clearance.py','audit_terminal_margin_stage_region_continuity.py','audit_terminal_margin_stage_region_bounds.py','audit_terminal_margin_stage_region_action.py','audit_terminal_margin_stage_rear_xy.py','audit_terminal_margin_stage_pose_height.py','audit_terminal_margin_stage_pose_loaded_execution.py','audit_terminal_margin_stage_loaded_parent.py']:
 p,s=base(name);put(p,s,[])
p=W/'audit_front_recovery_height_live.py';s=p.read_text();e=[]
s=change(s,e,'def audit(log,controls):','def audit(log,controls,*,verified_front_events=None):\n verified_front_events={} if verified_front_events is None else verified_front_events\n assert set(verified_front_events)<={r["step"] for r in log["rows"]}')
s=change(s,e,"  if mode=='top_cross' and abs(goal[2]-height)>2e-6:","  if t in verified_front_events:\n   event=verified_front_events[t];assert event['kind'] in ('command','handover') and count==0\n   assert mode==('top_press' if event['kind']=='handover' else 'top_cross')\n   assert r['front_initial_center_phase']==('measured_handover' if event['kind']=='handover' else 'tracking')\n  if mode=='top_cross' and t not in verified_front_events and abs(goal[2]-height)>2e-6:")
s=change(s,e,"ep=Path(sys.argv[1]);result=audit(json.loads((ep/'frontal_bypass.json').read_text()),json.loads((ep/'expert_control.json').read_text()));", "ep=Path(sys.argv[1]);from front_initial_stage_audit_context import verified_front_events\n result=audit(json.loads((ep/'frontal_bypass.json').read_text()),json.loads((ep/'expert_control.json').read_text()),verified_front_events=verified_front_events(ep));")
s=change(s,e,'FRONT_RECOVERY_HEIGHT_LIVE_AUDIT.json','FRONT_INITIAL_STAGE_FRONT_HEIGHT_AUDIT.json');put(p,s,e,'audit_front_initial_stage_front_height.py')
p=W/'audit_terminal_lead_stage_stability.py';s=p.read_text().replace('terminal_lead_stage','front_initial_stage').replace('TERMINAL_LEAD_STAGE','FRONT_INITIAL_STAGE');put(p,s,[dict(kind='Source binding/report prefix only: lead->front_initial; original corrected margin formula reused')],'audit_front_initial_stage_stability.py')
out=W/'FRONT_INITIAL_STAGE_REMAINING_AUDITS_PREPARATION.json';assert not out.exists();out.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,generator_sha256=sha(__file__),global_replacements=pairs,adapters=records,syntax_passed=True,inventory_complete=False,simulation_started=False,training_ready=False,remaining=['full audit inventory and fixture checks','front pressure/COP command history review','combined native self-clearance test or exact branch proof','provenance/observation positive binding','freeze full-group baseline and candidate protocol before physics']),indent=2));print('Prepared',len(records),'reference/height and source-bound original adapters; no launch approval')
