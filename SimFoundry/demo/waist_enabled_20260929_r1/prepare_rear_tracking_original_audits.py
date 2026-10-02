"""Reversible import/source/report adapters; original audit arithmetic unchanged."""
from pathlib import Path
import json,ast,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prior=json.loads((W/'REAR_LATCHED_AUDIT_SUPPLEMENTS_V2_PREPARATION.json').read_text());names=[x['output'] for x in prior['files']]
parents={n:n.removesuffix('_v2').replace('rear_latched_','rear_tracking_').replace('rear_corridor_latched_inputs','rear_tracking_inputs') for n in names}
external=dict(rear_corridor_latched_source_binding='rear_recovery_tracking_source_binding',audit_rear_corridor_latched_native_v2='audit_rear_recovery_tracking_native_bound',audit_rear_corridor_latched_records_v2='audit_rear_recovery_tracking_records',rear_corridor_latched_stationarity='rear_recovery_tracking_stationarity')
symbols=dict(parents,**external,verify_rear_latched_stage_source='verify_rear_tracking_stage_source',staged_rear_corridor_latched='staged_rear_recovery_tracking',REAR_LATCHED_V2_='REAR_TRACKING_',REAR_CORRIDOR_LATCHED_NATIVE_V2_AUDIT='REAR_RECOVERY_TRACKING_NATIVE_AUDIT');rows=[]
for old,new in sorted(parents.items()):
 a=W/(old+'.py');b=W/(new+'.py');assert not b.exists(),b;s=a.read_text();edits=[]
 for x,y in sorted(symbols.items(),key=lambda x:-len(x[0])):
  count=s.count(x)
  if count:assert y not in s,(new,y);s=s.replace(x,y);edits.append(dict(old=x,new=y,count=count))
 back=s
 for e in reversed(edits):assert back.count(e['new'])==e['count'];back=back.replace(e['new'],e['old'])
 assert back==a.read_text();ast.parse(s);b.write_text(s);rows.append(dict(parent=old,output=new,parent_sha256=sha(a),output_sha256=sha(b),edits=edits))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=rows,mapping=dict(parents,**external),training_ready=False)
with (W/'REAR_TRACKING_ORIGINAL_AUDIT_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print('prepared',len(rows),'reversible original audit adapters')
