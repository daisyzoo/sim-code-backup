"""Prepare complete numeric/visual/control watchers without launch.
Correct descriptive exit counts: normal release cannot inherit an old failure.
Original task, pose, quality and independent audit checks remain unchanged.
"""
from pathlib import Path
import json,hashlib,re,ast,datetime
W=Path(__file__).resolve().parent;P=W/'rear_early_edge_physical_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
source=W/'front_box_trailing_physical_preparation_r2/REVIEW_AND_WATCHER_PREPARATION.json';old=read(source)
mapping={'front_box_trailing_trial2_numeric_reviews_r2':'rear_early_edge_trial1_numeric_reviews_r1','front_box_trailing_trial2':'rear_early_edge_trial1','front_box_trailing_physical_preparation_r2':'rear_early_edge_physical_preparation_r1','front_box_trailing_physical_r2':'rear_early_edge_physical_r1','front_box_trailing_admission_preparation_r2':'rear_early_edge_preparation_r1','staged_front_box_trailing_v2':'staged_rear_early_edge_v1','front_box_trailing_stage_source_binding_v2':'rear_early_edge_stage_source_binding_v1','front_box_trailing_r2_':'rear_early_edge_r1_','FRONT_BOX_TRAILING_R2_':'REAR_EARLY_EDGE_R1_'}
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inv={v:k for k,v in mapping.items()};reverse=re.compile('|'.join(map(re.escape,sorted(inv,key=len,reverse=True))));records=[]
for row in old['files']:
 parent=Path(row['path']);assert sha(parent)==row['sha256'];dest=W/pat.sub(lambda m:mapping[m.group()],parent.name);text=pat.sub(lambda m:mapping[m.group()],parent.read_text());edits=[]
 if parent.name=='review_front_box_trailing_trial2_v1_stage_episode.py':
  a="   current['end']=row['step'];current['frames']+=1\n  elif current is not None:current['exit_reason']=row.get('last_recontact_reason');bouts.append(current);current=None"
  b="   current['end']=row['step'];current['frames']+=1;current['last_recontact_counter']=row.get('recontacts',0)\n  elif current is not None:\n   current['exit_mode']=row['mode']\n   current['exit_reason']='normal_release' if row['mode']=='top_release' else row.get('last_recontact_reason') if row.get('recontacts',0)>current['last_recontact_counter'] else row.get('route_stop_reason') or row.get('release_reason') or 'other_guard'\n   bouts.append(current);current=None"
  assert text.count(a)==1;text=text.replace(a,b);edits.append(dict(old=a,new=b))
 restored=text
 for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert reverse.sub(lambda m:inv[m.group()],restored)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 records.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=records,replacements=mapping,source_sha256={str(p):sha(p) for p in [Path(__file__),source,P/'PLAN.json']},descriptive_exit_count_changed=True,quality_gates_changed=False,simulation_started=False,training_ready=False)
with (P/'REVIEW_AND_WATCHER_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(prepared_files=len(records),descriptive_exit_fix=True,quality_gates_changed=False,launched=False)))
