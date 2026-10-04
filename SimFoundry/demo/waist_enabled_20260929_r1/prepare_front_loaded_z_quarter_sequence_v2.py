"""Rebind the fully checked quarter trial to follow repaired front-box r2.
Quarter controller, original8push2wait and direct lateral parent are unchanged.
Old queue/r1 preparation stay immutable and visibly failed; no physical launch.
"""
from pathlib import Path
import json,hashlib,datetime,copy,ast,re
W=Path(__file__).resolve().parent;P=W/'front_loaded_z_quarter_physical_preparation_r2';OLD=W/'front_loaded_z_quarter_physical_preparation_r1';P.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not (W/'front_loaded_z_quarter_physical_r1').exists() and read(OLD/'LAUNCH_QUEUE_STATUS.json')['status']=='stopped_without_retry'
oldpid=read(OLD/'LAUNCH_QUEUE_STATUS.json')['pid'];assert not Path('/proc',str(oldpid)).exists()
mapping={'front_loaded_z_quarter_trial1_physical_audits_r1':'front_loaded_z_quarter_trial2_physical_audits_r2','front_loaded_z_quarter_trial1_numeric_reviews_r1':'front_loaded_z_quarter_trial2_numeric_reviews_r2','front_loaded_z_quarter_trial1_physical_r1':'front_loaded_z_quarter_trial2_physical_r2','front_loaded_z_quarter_trial1':'front_loaded_z_quarter_trial2','front_loaded_z_quarter_physical_preparation_r1':'front_loaded_z_quarter_physical_preparation_r2','front_loaded_z_quarter_physical_r1':'front_loaded_z_quarter_physical_r2','FRONT_LOADED_Z_QUARTER_R1_':'FRONT_LOADED_Z_QUARTER_R2_','front_box_trailing_physical_r1':'front_box_trailing_physical_r2','run_front_box_trailing_trial1_physical_r1':'run_front_box_trailing_trial2_physical_r2'}
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inv={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inv,key=len,reverse=True))));remap=lambda t:pat.sub(lambda m:mapping[m.group()],t);invert=lambda t:rev.sub(lambda m:inv[m.group()],t)
files=[]
for r in read(OLD/'REVIEW_AND_WATCHER_PREPARATION.json')['files']:
 parent=Path(r['path']);assert sha(parent)==r['sha256'];dest=W/remap(parent.name);text=remap(parent.read_text());assert invert(text)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 files.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest)))
(P/'REVIEW_AND_WATCHER_PREPARATION.json').write_text(json.dumps(dict(created_at_utc=now(),scope=__doc__,files=files,replacements=mapping,simulation_started=False,training_ready=False),indent=2))
plan=copy.deepcopy(read(OLD/'PLAN.json'));plan.update(created_at_utc=now(),scope=__doc__,required_before_launch=['All original quarter native/record/source/family checks pass unchanged.','Repaired front-box r2 complete10collection/10actual reviews and producer terminal.','Lateral remains the exact direct comparison parent; all original task/control conditions retained.','GPU free and original30GiB startup/25GiB reserve budget satisfied.'])
for c in plan['commands']:
 args=c['args'];args[args.index('--out-dir')+1]=str(W/'front_loaded_z_quarter_physical_r2'/f"case_{c['layout_id']}")
assert plan['collector']==read(OLD/'PLAN.json')['collector'] and plan['parent_run']==str(W/'front_corridor_lateral_physical_r1')
(P/'PLAN.json').write_text(json.dumps(plan,indent=2));prepared=[]
for name in ['run_front_loaded_z_quarter_trial1_physical_r1.py','close_front_loaded_z_quarter_trial1_physical_v1.py','queue_front_loaded_z_quarter_trial1_physical_v1.py']:
 parent=W/name;dest=W/remap(name);text=remap(parent.read_text());assert invert(text)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 prepared.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest)))
report=dict(passed=True,created_at_utc=now(),scope=__doc__,replacements=mapping,files=prepared,inverse_checked=True,old_queue_status=str(OLD/'LAUNCH_QUEUE_STATUS.json'),direct_parent_unchanged=True,quarter_collector_unchanged=True,source_sha256={str(p):sha(p) for p in [Path(__file__),OLD/'PLAN.json',OLD/'LAUNCH_QUEUE_STATUS.json',P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json']},physical_started=False,training_ready=False)
with (P/'LAUNCHER_DERIVATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(prepared=True,conditions=10,direct_parent='front_corridor_lateral_physical_r1',sequencing_after='front_box_trailing_physical_r2',physics_started=False)))
