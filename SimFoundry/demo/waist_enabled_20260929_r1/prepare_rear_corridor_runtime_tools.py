"""Prepare versioned watcher/review/closure tools; no collection launch."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();manifest=[]
for parent,dest in [('watch_front_interval_physical_audits.py','watch_rear_corridor_physical_audits.py'),('review_front_interval_stage_episode.py','review_rear_corridor_stage_episode.py'),('review_front_interval_incomplete_episode.py','review_rear_corridor_incomplete_episode.py'),('close_front_interval_physical.py','close_rear_corridor_physical.py')]:
 original=(W/parent).read_text();text=original;edits=[]
 changes=[('front_interval_stage_run_contract','rear_corridor_stage_run_contract_v2'),('front_interval_stage_source_binding','rear_corridor_stage_source_binding'),('audit_front_interval_stage_','audit_rear_corridor_stage_'),('verify_front_interval_stage_source','verify_rear_corridor_stage_source'),('front_corridor_interval','rear_corridor_recovery'),('FRONT_INTERVAL_STAGE_','REAR_CORRIDOR_STAGE_'),('FRONT_INTERVAL_INCOMPLETE_','REAR_CORRIDOR_INCOMPLETE_'),('FRONT_INTERVAL_REVIEW.jpg','REAR_CORRIDOR_REVIEW.jpg'),('run_front_interval_physical.py','run_rear_corridor_physical.py'),('front-interval','rear-corridor')]
 for old,new in changes:
  if old in text:
   assert new not in text;count=text.count(old);text=text.replace(old,new);edits.append(dict(old=old,new=new,count=count))
 if parent.startswith('close_'):
  old="r.get('rear_corridor_recovery',{}).get('changed')";new="r.get('rear_corridor_override') is not None";assert old in text;text=text.replace(old,new);edits.append(dict(old=old,new=new,count=1))
  old='interval_changed_steps';new='rear_recovery_changed_steps';assert old in text;text=text.replace(old,new);edits.append(dict(old=old,new=new,count=1))
 ast.parse(text);reverse=text
 for e in reversed(edits):assert reverse.count(e['new'])==e['count'];reverse=reverse.replace(e['new'],e['old'])
 assert reverse==original;p=W/dest;assert not p.exists();p.write_text(text);manifest.append(dict(parent=parent,parent_sha256=sha(W/parent),new=dest,new_sha256=sha(p),edits=edits,reverse_matches=True))
with (W/'REAR_CORRIDOR_RUNTIME_TOOLS_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest,training_ready=False,launched=False),f,indent=2)
print('prepared',len(manifest))
