"""Replace inherited dynamic hold entry; add native recovery to mandatory checks."""
from pathlib import Path
import ast,hashlib,json,datetime
w=Path(__file__).resolve().parent;p=w/'rear_corridor_stage_run_contract.py';s=p.read_text()
old="def primary(wait):\n return ("
new="REPORTS.pop('audit_terminal_hold_live.py')\nREPORTS['audit_rear_corridor_terminal_hold_live.py']=('REAR_CORRIDOR_TERMINAL_HOLD_LIVE_AUDIT.json',('recorded_hold_checks_passed',))\nREPORTS['audit_rear_corridor_native_commands_v2.py']=('REAR_CORRIDOR_NATIVE_COMMAND_V2_AUDIT.json',('passed',))\ndef primary(wait):\n return ['audit_rear_corridor_native_commands_v2.py'] + ("
assert s.count(old)==1 and new not in s;s=s.replace(old,new);assert s.replace(new,old)==p.read_text();ast.parse(s);q=w/'rear_corridor_stage_run_contract_v2.py';assert not q.exists();q.write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (w/'REAR_CORRIDOR_RUN_CONTRACT_V2_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=p.name,parent_sha256=sha(p),new=q.name,new_sha256=sha(q),edit=dict(old=old,new=new),reverse_matches=True,training_ready=False),f,indent=2)
