"""Reversible source/import/report adaptation of unchanged original audit math.
The new native boundary independently proves measured phase and new command KKT.
This preparation does not imply that full native or physics checks have passed.
"""
from pathlib import Path
import ast,re,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parents={p.stem:p.stem.replace('audit_rear_corridor_','audit_rear_latched_') for p in W.glob('audit_rear_corridor_stage_*.py')}
for n in ['audit_rear_corridor_diagonal_live','audit_rear_corridor_terminal_hold_live','audit_rear_corridor_transport_events_v2']:
 parents[n]=n.replace('audit_rear_corridor_','audit_rear_latched_')
parents.update(rear_corridor_xy_reconstruction='rear_latched_xy_reconstruction',rear_corridor_height_reconstruction='rear_latched_height_reconstruction',rear_corridor_stage_audit_context='rear_latched_audit_context',rear_corridor_audit_inputs='rear_corridor_latched_inputs',rear_corridor_stage_run_contract_v2='rear_latched_run_contract')
externals=dict(rear_corridor_stage_source_binding='rear_corridor_latched_source_binding',audit_rear_corridor_native_commands_v2='audit_rear_corridor_latched_native',audit_rear_corridor_command_records='audit_rear_corridor_latched_records',rear_corridor_stationarity='rear_corridor_latched_stationarity')
mapping=dict(parents,**externals);symbols=dict(mapping,verify_rear_corridor_stage_source='verify_rear_latched_stage_source',staged_rear_corridor_recovery_guarded='staged_rear_corridor_latched',REAR_CORRIDOR_NATIVE_COMMAND_V2_AUDIT='REAR_CORRIDOR_LATCHED_NATIVE_AUDIT')
manifest=[]
for parent,dest in sorted(parents.items()):
 src=W/(parent+'.py');path=W/(dest+'.py');assert not path.exists(),path;s=src.read_text();edits=[]
 def replace(old,new):
  global s
  count=s.count(old)
  if count:
   assert new not in s,(dest,new);s=s.replace(old,new);edits.append(dict(old=old,new=new,count=count))
 for old,new in sorted(symbols.items(),key=lambda item:-len(item[0])):replace(old,new)
 for name in sorted(set(re.findall(r'REAR_CORRIDOR_(?:STAGE|DIAGONAL|TERMINAL_HOLD)_[A-Z_]+',s))):replace(name,name.replace('REAR_CORRIDOR_','REAR_LATCHED_'))
 restored=s
 for e in reversed(edits):assert restored.count(e['new'])==e['count'];restored=restored.replace(e['new'],e['old'])
 assert restored==src.read_text();ast.parse(s);path.write_text(s);manifest.append(dict(parent=parent,output=dest,parent_sha256=sha(src),output_sha256=sha(path),edits=edits,reversible=True))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,mapping=mapping,files=manifest,external_sha256={n:sha(W/(n+'.py')) for n in externals.values()},training_ready=False)
(W/'REAR_LATCHED_ORIGINAL_AUDIT_PREPARATION.json').write_text(json.dumps(report,indent=2));print('Prepared',len(manifest),'reversible adapters. Original arithmetic unchanged.')
